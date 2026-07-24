"""
Multi-Action LLM Controller for TLE
====================================
Extends TLE with a richer action space where the LLM chooses among 4 distinct
algorithmic interventions at each invocation:

  1. PARAM            - tune F/CR/strategy (legacy TLE behavior)
  2. ARCHIVE_RESET    - reset/trim the non-dominated archive
  3. RESTART_TOP      - re-initialize top X% around current best
  4. DIVERSITY_INJECT - inject K random or guided immigrants

This is A3 in our paper's "boosting contribution" plan: it changes the LLM
from a passive config advisor to an active controller that picks structurally
different interventions. This unlocks the LLM's leverage on dynamics that pure
parameter tuning cannot reach (e.g., when the population has collapsed into a
local region, param tuning alone will not escape it).

The action space is intentionally small (4 actions) for tractability and to
make the per-action ablation interpretable. The LLM receives:
  - Current population state (mean/std per dim, top-3 individuals, fitness range)
  - Change signal (entropy/stagnation/change-detection triggers)
  - History of last N actions and their measured reward

The LLM returns a structured JSON with action_type + params + reasoning.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, Optional, List
import numpy as np


# ==================== Action Specification ====================

VALID_ACTIONS = ("param", "archive_reset", "restart_top", "diversity_injection")


@dataclass
class Action:
    """Container for one LLM-chosen action."""
    action_type: str                       # one of VALID_ACTIONS
    params: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""

    def is_valid(self) -> bool:
        if self.action_type not in VALID_ACTIONS:
            return False
        if self.action_type == "param":
            return "F" in self.params or "CR" in self.params or "strategy" in self.params
        if self.action_type == "archive_reset":
            return "mode" in self.params
        if self.action_type == "restart_top":
            return "restart_pct" in self.params
        if self.action_type == "diversity_injection":
            return "n_inject" in self.params
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "params": dict(self.params),
            "reasoning": self.reasoning,
        }


# ==================== Action Implementations ====================

def execute_param_action(
    action: Action,
    tle_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    PARAM action: modify DE strategy / F / CR.
    Returns updated state changes (caller applies them).
    """
    changes = {}
    p = action.params
    if "strategy" in p:
        s = str(p["strategy"]).strip().lower()
        if s in ("rand", "best", "current_to_best"):
            changes["de_strategy"] = s
    if "F" in p:
        try:
            changes["F"] = float(np.clip(float(p["F"]), 0.1, 1.0))
        except Exception:
            pass
    if "CR" in p:
        try:
            changes["CR"] = float(np.clip(float(p["CR"]), 0.1, 1.0))
        except Exception:
            pass
    return changes


def execute_archive_reset_action(
    action: Action,
    pop: np.ndarray,
    fit: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
    archive: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
) -> Tuple[np.ndarray, np.ndarray, List[Tuple[np.ndarray, np.ndarray]]]:
    """
    ARCHIVE_RESET action: reset / trim the non-dominated archive and seed
    new individuals from it.

    Modes:
      - "all":        clear archive, recompute from current population's ND front
      - "trim":       keep only top trim_pct by crowding distance
      - "replace_worst": replace worst trim_pct with random individuals

    Returns (new_pop, new_fit, new_archive).
    """
    p = action.params
    mode = str(p.get("mode", "trim")).strip().lower()
    trim_pct = float(p.get("trim_pct", 30))
    trim_pct = float(np.clip(trim_pct, 0, 100))
    lower, upper = bounds
    NP, D = pop.shape

    if archive is None:
        archive = []
    new_archive = list(archive)

    if mode == "all":
        # Rebuild archive from current population's ND front
        new_archive = _extract_non_dominated(pop, fit)
        # Reset 30% of population to random (maintain some stability)
        n_replace = int(NP * 0.3)
        idx = np.random.choice(NP, n_replace, replace=False)
        for i in idx:
            pop[i] = np.random.uniform(lower, upper, D)
        fit = np.vstack([fit[:1]] * NP)  # placeholder, will be re-evaluated
        # Caller is expected to re-evaluate fit; we just return a sentinel
        # that signals re-evaluation needed.
        fit = np.full_like(fit, np.nan)

    elif mode == "trim":
        # Keep top trim_pct by non-domination rank, replace rest with random
        ranks = _non_dominated_ranks(fit)
        keep_n = max(1, int(NP * (100 - trim_pct) / 100))
        keep_idx = np.argsort(ranks)[:keep_n]
        n_replace = NP - keep_n
        if n_replace > 0:
            new_idx = np.setdiff1d(np.arange(NP), keep_idx)
            chosen = np.random.choice(new_idx, n_replace, replace=False)
            for i in chosen:
                pop[i] = np.random.uniform(lower, upper, D)
            fit = np.full_like(fit, np.nan)

    elif mode == "replace_worst":
        # Replace worst trim_pct with random
        scores = np.sum(fit, axis=1) if fit.ndim == 2 else fit
        n_replace = max(1, int(NP * trim_pct / 100))
        worst_idx = np.argsort(-scores)[:n_replace]
        for i in worst_idx:
            pop[i] = np.random.uniform(lower, upper, D)
        fit = np.full_like(fit, np.nan)

    else:
        # Unknown mode -> no-op
        pass

    return pop, fit, new_archive


def execute_restart_top_action(
    action: Action,
    pop: np.ndarray,
    fit: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    RESTART_TOP action: re-initialize the top X% of individuals around
    current best, with small Gaussian noise. This restarts convergence
    around the best known region instead of random restart.

    params:
      restart_pct: 0-50 (percent of population to restart)
      around: "best" | "current_center" (where to seed the restart)
      noise_scale: 0.01-0.2 (relative noise around seed)
    """
    p = action.params
    restart_pct = float(p.get("restart_pct", 20))
    restart_pct = float(np.clip(restart_pct, 0, 50))
    around = str(p.get("around", "best")).strip().lower()
    noise_scale = float(p.get("noise_scale", 0.1))
    noise_scale = float(np.clip(noise_scale, 0.01, 0.2))
    lower, upper = bounds
    NP, D = pop.shape

    # Determine seed location
    if fit.ndim == 2:
        scores = np.sum(fit, axis=1)
    else:
        scores = fit
    valid = ~np.isnan(scores)
    if not np.any(valid):
        # No valid fitness, just noise current
        seed = np.mean(pop, axis=0)
    elif around == "current_center":
        seed = np.mean(pop[valid], axis=0)
    else:  # "best"
        seed = pop[valid][np.argmin(scores[valid])]

    # Select top X% to restart (by best score)
    n_restart = max(1, int(NP * restart_pct / 100))
    top_idx = np.argsort(scores)[:n_restart]
    # The top individuals should be near best, so we re-seed them around best
    # with controlled noise.
    rng_span = upper - lower
    for i in top_idx:
        pop[i] = seed + np.random.normal(0, noise_scale, D) * rng_span
        pop[i] = np.clip(pop[i], lower, upper)

    fit = np.full_like(fit, np.nan)
    return pop, fit


def execute_diversity_injection_action(
    action: Action,
    pop: np.ndarray,
    fit: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    DIVERSITY_INJECT action: inject K new individuals to maintain diversity.
    Similar to DNSGA-II-A's random immigrants, but LLM can choose WHERE to
    inject (random vs. around best vs. anti-best).

    params:
      n_inject: 1-50 (number of new individuals)
      around: "random" | "best" | "anti_best"
      noise_scale: 0.05-0.5 (relative noise; only for non-random modes)
    """
    p = action.params
    n_inject = int(p.get("n_inject", 10))
    n_inject = int(np.clip(n_inject, 1, 50))
    around = str(p.get("around", "random")).strip().lower()
    noise_scale = float(p.get("noise_scale", 0.2))
    noise_scale = float(np.clip(noise_scale, 0.05, 0.5))
    lower, upper = bounds
    NP, D = pop.shape

    # Pick n_inject random indices to replace
    if n_inject >= NP:
        # Replace whole population
        idx = np.arange(NP)
    else:
        idx = np.random.choice(NP, n_inject, replace=False)

    if around == "random":
        new_individuals = np.random.uniform(lower, upper, (len(idx), D))
    else:
        # Need a seed point (best or anti-best)
        if fit.ndim == 2:
            scores = np.sum(fit, axis=1)
        else:
            scores = fit
        valid = ~np.isnan(scores)
        if not np.any(valid):
            seed = np.mean(pop, axis=0)
        else:
            best_idx = np.argmin(scores[valid])
            if around == "best":
                seed = pop[valid][best_idx]
            else:  # anti_best -> furthest from best
                best = pop[valid][best_idx]
                dists = np.linalg.norm(pop[valid] - best, axis=1)
                seed = pop[valid][np.argmax(dists)]

        rng_span = upper - lower
        new_individuals = seed + np.random.normal(0, noise_scale, (len(idx), D)) * rng_span
        new_individuals = np.clip(new_individuals, lower, upper)

    for k, i in enumerate(idx):
        pop[i] = new_individuals[k]
    fit = np.full_like(fit, np.nan)
    return pop, fit


# ==================== Helpers ====================

def _extract_non_dominated(
    pop: np.ndarray, fit: np.ndarray
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Extract non-dominated individuals as (pop_i, fit_i) pairs."""
    N = fit.shape[0]
    nd_mask = np.ones(N, dtype=bool)
    for i in range(N):
        if not nd_mask[i]:
            continue
        for j in range(N):
            if i == j or not nd_mask[j]:
                continue
            if np.all(fit[j] <= fit[i]) and np.any(fit[j] < fit[i]):
                nd_mask[i] = False
                break
    return [(pop[i].copy(), fit[i].copy()) for i in range(N) if nd_mask[i]]


def _non_dominated_ranks(fit: np.ndarray) -> np.ndarray:
    """Compute non-domination rank for each individual (0 = best front)."""
    N = fit.shape[0]
    ranks = np.zeros(N, dtype=int)
    dominated_by = [[] for _ in range(N)]
    domination_count = np.zeros(N, dtype=int)
    fronts = [[]]

    for p in range(N):
        for q in range(N):
            if p == q:
                continue
            if np.all(fit[p] <= fit[q]) and np.any(fit[p] < fit[q]):
                dominated_by[p].append(q)
            elif np.all(fit[q] <= fit[p]) and np.any(fit[q] < fit[p]):
                domination_count[p] += 1
        if domination_count[p] == 0:
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        nxt = []
        for p in fronts[i]:
            for q in dominated_by[p]:
                domination_count[q] -= 1
                if domination_count[q] == 0:
                    ranks[q] = i + 1
                    nxt.append(q)
        i += 1
        fronts.append(nxt)
    return ranks


def parse_llm_response_to_action(parsed: Dict[str, Any]) -> Optional[Action]:
    """
    Convert parsed LLM JSON to an Action object, validating types/ranges.
    Returns None if invalid.
    """
    if not isinstance(parsed, dict):
        return None
    action_type = str(parsed.get("action_type", "")).strip().lower()
    if action_type not in VALID_ACTIONS:
        return None
    params = parsed.get("params", {})
    if not isinstance(params, dict):
        return None
    reasoning = str(parsed.get("reasoning", ""))[:200]
    return Action(action_type=action_type, params=params, reasoning=reasoning)


def default_action() -> Action:
    """Fallback when LLM fails: conservative PARAM action."""
    return Action(
        action_type="param",
        params={"F": 0.5, "CR": 0.9, "strategy": "rand"},
        reasoning="default (LLM unavailable)",
    )