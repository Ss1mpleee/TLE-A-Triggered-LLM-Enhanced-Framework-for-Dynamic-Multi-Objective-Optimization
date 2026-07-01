"""
Prompt Templates for LLM-Orchestrated EA
=========================================
Two-channel prompt design:
  Channel 1 (strategic): {strategy, subspace_indices, crossover_mode}
  Channel 2 (parametric): {F, CR, pop_size_delta}
"""
import json
from typing import Dict, Any, Optional, Tuple
import numpy as np

from .llm_interface import LLMClient


SYSTEM_PROMPT = """You are an expert in evolutionary computation, particularly
differential evolution (DE) for multi-objective optimization. You provide
real-time strategic advice during evolutionary search based on population
statistics.

Your output must be a JSON object with exactly two channels:
- "strategy": either "exploit" (intensify current best region),
               "explore" (broaden search to new regions),
               or "focus" (concentrate on a subset of variables).
- "subspace_indices": list of integer indices [0, D-1] of variables to
                      focus on (empty list means all variables).
- "crossover_mode": either "binomial" or "exponential".
- "F": scaling factor in [0.1, 1.0] (recommended 0.4-0.9).
- "CR": crossover rate in [0.1, 1.0] (recommended 0.6-0.95).
- "pop_size_delta": integer change in population size, range [-30, 30].
- "reasoning": one-sentence explanation of your recommendation.

Respond ONLY with valid JSON. No markdown, no extra text."""


def build_population_summary(
    population: np.ndarray,
    fitness: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
) -> str:
    """Build a compact text summary of population state."""
    NP, D = population.shape
    M = fitness.shape[1] if fitness.ndim == 2 else 1

    # Population stats per dimension
    pop_mean = np.mean(population, axis=0)
    pop_std = np.std(population, axis=0)
    pop_min = np.min(population, axis=0)
    pop_max = np.max(population, axis=0)

    # Normalize to [0,1] range for easier interpretation
    lower, upper = bounds
    norm_mean = (pop_mean - lower) / (upper - lower + 1e-12)
    norm_std = pop_std / (upper - lower + 1e-12)

    # Top-3 individuals (by sum of objectives for multi-objective)
    if fitness.ndim == 2:
        score = np.sum(fitness, axis=1)
    else:
        score = fitness
    top3_idx = np.argsort(score)[:3]

    # Build prompt
    lines = [
        f"Population size: {NP}, Dimensions: {D}, Objectives: {M}",
        f"Current generation statistics:",
    ]
    for d in range(min(D, 10)):  # show first 10 dims
        lines.append(
            f"  x[{d}]: mean={norm_mean[d]:.2f}, std={norm_std[d]:.3f}, "
            f"range=[{pop_min[d]:.2f}, {pop_max[d]:.2f}]"
        )
    if D > 10:
        lines.append(f"  ... (omitted {D - 10} dimensions)")

    lines.append("")
    lines.append(f"Top-3 individuals (lower is better for minimization):")
    for rank, idx in enumerate(top3_idx):
        if fitness.ndim == 2:
            obj_str = ", ".join([f"f{j}={fitness[idx, j]:.3f}" for j in range(M)])
        else:
            obj_str = f"f={fitness[idx]:.3f}"
        lines.append(f"  rank {rank+1}: {obj_str}, x_norm[0:3]={norm_mean[0:3].tolist()}")

    lines.append("")
    lines.append(f"Total objective range: min={np.min(score):.3f}, max={np.max(score):.3f}")

    return "\n".join(lines)


def build_change_signal_info(change_signal: Optional[float],
                              trigger_info: Dict[str, Any]) -> str:
    """Add environmental change info if available."""
    if change_signal is None and not trigger_info.get("signal_3_change"):
        return ""
    lines = [
        "",
        "Environmental change detected! The optimization landscape has shifted.",
        "Recommend a strategy that adapts to new conditions.",
    ]
    return "\n".join(lines)


def call_llm_for_advice(
    llm: LLMClient,
    population: np.ndarray,
    fitness: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
    generation: int,
    trigger_info: Optional[Dict[str, Any]] = None,
    change_signal: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Query LLM for strategic + parametric advice.

    Returns dict with keys: strategy, subspace_indices, crossover_mode,
                            F, CR, pop_size_delta, reasoning.
    """
    # Build prompt
    pop_summary = build_population_summary(population, fitness, bounds)
    change_info = build_change_signal_info(change_signal, trigger_info or {})

    user_prompt = f"""Current generation: {generation}

{pop_summary}
{change_info}

Based on the above population state, provide your strategic and parametric
recommendation for the next few generations of differential evolution.

Output JSON only."""

    response = llm.call(user_prompt, system=SYSTEM_PROMPT, temperature=0.0,
                        max_tokens=300, force_json=True)
    parsed = llm.parse_json(response)

    if parsed is None:
        return _default_advice()

    # Validate & clamp
    return _validate_advice(parsed)


def _default_advice() -> Dict[str, Any]:
    """Conservative default if LLM fails."""
    return {
        "strategy": "exploit",
        "subspace_indices": [],
        "crossover_mode": "binomial",
        "F": 0.5,
        "CR": 0.9,
        "pop_size_delta": 0,
        "reasoning": "default (LLM unavailable)",
    }


def _validate_advice(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clamp LLM output to valid ranges."""
    out = _default_advice()

    # Strategy
    s = raw.get("strategy", "exploit")
    if s in ("exploit", "explore", "focus"):
        out["strategy"] = s

    # Subspace indices
    indices = raw.get("subspace_indices", [])
    if isinstance(indices, list):
        out["subspace_indices"] = [int(i) for i in indices if isinstance(i, (int, float)) and i >= 0]

    # Crossover mode
    cm = raw.get("crossover_mode", "binomial")
    if cm in ("binomial", "exponential"):
        out["crossover_mode"] = cm

    # F
    F = raw.get("F", 0.5)
    try:
        F = float(F)
        out["F"] = np.clip(F, 0.1, 1.0)
    except Exception:
        pass

    # CR
    CR = raw.get("CR", 0.9)
    try:
        CR = float(CR)
        out["CR"] = np.clip(CR, 0.1, 1.0)
    except Exception:
        pass

    # pop_size_delta
    delta = raw.get("pop_size_delta", 0)
    try:
        delta = int(delta)
        out["pop_size_delta"] = int(np.clip(delta, -30, 30))
    except Exception:
        pass

    out["reasoning"] = str(raw.get("reasoning", ""))[:200]
    return out


def apply_advice(population: np.ndarray, advice: Dict[str, Any],
                 bounds: Tuple[np.ndarray, np.ndarray]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply LLM's strategic advice to the population.

    Returns:
        modified_population, applied_actions_dict
    """
    NP, D = population.shape
    lower, upper = bounds
    actions = {}

    # Action 1: Strategy -> operator selection
    strategy = advice.get("strategy", "exploit")
    if strategy == "exploit":
        actions["de_strategy"] = "best"
    elif strategy == "explore":
        actions["de_strategy"] = "rand"
    else:  # focus
        actions["de_strategy"] = "current_to_best"
    actions["F"] = advice.get("F", 0.5)
    actions["CR"] = advice.get("CR", 0.9)
    actions["crossover_mode"] = advice.get("crossover_mode", "binomial")

    # Action 2: Subspace focusing
    # If LLM specifies subspace indices, we restrict DE to those dimensions
    # by setting CR=0 outside those dimensions
    subspace = advice.get("subspace_indices", [])
    if subspace and strategy == "focus":
        # Create a CR mask
        cr_mask = np.zeros(D)
        valid = [i for i in subspace if 0 <= i < D]
        for i in valid:
            cr_mask[i] = 1.0
        actions["cr_mask"] = cr_mask
    else:
        actions["cr_mask"] = None

    # Action 3: Population size change
    delta = advice.get("pop_size_delta", 0)
    if delta != 0:
        new_NP = max(20, min(300, NP + delta))
        if new_NP > NP:
            # Add new individuals via random sampling
            extra = np.random.uniform(lower, upper, (new_NP - NP, D))
            population = np.vstack([population, extra])
        elif new_NP < NP:
            # Remove worst individuals (random removal for simplicity)
            idx = np.random.choice(NP, new_NP, replace=False)
            population = population[idx]
        actions["new_pop_size"] = new_NP
    else:
        actions["new_pop_size"] = NP

    return population, actions
