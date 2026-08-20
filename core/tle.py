"""
TLE: Triggered LLM-Orchestrated Evolutionary Algorithm
======================================================
Main algorithm integrating:
  - DE/rand/1 (default) with dynamic strategy switching
  - Triple-signal trigger for LLM invocation
  - Dual-channel mapping (strategic + parametric)
  - UCB bandit budget scheduler

This is our proposed method.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any, Callable, List

from .de_operators import de_rand_1_bin, de_best_1_bin, de_current_to_best_1_bin
from .moo_utils import fast_non_dominated_sort, nsga2_select
from .triggers import TripleSignalTrigger, DoubleSignalTrigger
from .triggers import SingleSignalTrigger, AlwaysInvokeTrigger, NeverInvokeTrigger
from .bandit import UCBBandit
from .prompts import call_llm_for_advice, apply_advice, call_llm_for_multi_action
from .llm_interface import LLMClient
from .multi_action import (
    Action,
    execute_param_action,
    execute_archive_reset_action,
    execute_restart_top_action,
    execute_diversity_injection_action,
    default_action,
)


class TLE:
    """
    Triggered LLM-Orchestrated EA for multi-objective optimization.
    """

    def __init__(
        self,
        d: int,
        bounds: Tuple[np.ndarray, np.ndarray],
        n_obj: int,
        pop_size: int = 100,
        max_gen: int = 300,
        llm: Optional[LLMClient] = None,
        trigger: str = "triple",  # "triple" | "single" | "always" | "never"
        budget: int = 50,
        scheduler: str = "bandit",  # "bandit" | "fixed" | "heuristic"
        seed: int = 0,
    ):
        self.d = d
        self.bounds = bounds
        self.n_obj = n_obj
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.llm = llm
        self.seed = seed

        np.random.seed(seed)

        # Trigger
        if trigger == "triple":
            self.trigger = TripleSignalTrigger()
        elif trigger == "double":
            self.trigger = DoubleSignalTrigger()
        elif trigger == "single":
            self.trigger = SingleSignalTrigger()
        elif trigger == "always":
            self.trigger = AlwaysInvokeTrigger()
        elif trigger == "never":
            self.trigger = NeverInvokeTrigger()
        else:
            raise ValueError(f"Unknown trigger: {trigger}")

        # Scheduler
        self.scheduler_name = scheduler
        if scheduler == "bandit":
            self.scheduler = UCBBandit()
        elif scheduler == "fixed":
            from .bandit import FixedBudgetScheduler
            self.scheduler = FixedBudgetScheduler(budget, max_gen)
        elif scheduler == "heuristic":
            from .bandit import HeuristicDecayScheduler
            self.scheduler = HeuristicDecayScheduler(budget)
        else:
            raise ValueError(f"Unknown scheduler: {scheduler}")

        # DE state (LLM can modify these)
        self.de_strategy = "rand"  # "rand" | "best" | "current_to_best"
        self.F = 0.5
        self.CR = 0.9
        self.cr_mask = None
        self.current_pop_size = pop_size
        self.last_advice = None
        self.advice_log = []

    def _initialize(self) -> Tuple[np.ndarray, np.ndarray]:
        """Initialize population and evaluate."""
        lower, upper = self.bounds
        pop = np.random.uniform(lower, upper, (self.current_pop_size, self.d))
        fitness = self.evaluate_fn(pop)
        return pop, fitness

    def _de_step(self, pop: np.ndarray, fit: np.ndarray) -> np.ndarray:
        """One DE step using current F, CR, strategy."""
        # Apply strategy
        if self.de_strategy == "best":
            trial = de_best_1_bin(pop, fit, self.bounds, self.F, self.CR)
        elif self.de_strategy == "current_to_best":
            trial = de_current_to_best_1_bin(pop, fit, self.bounds, self.F, self.CR)
        else:
            trial = de_rand_1_bin(pop, fit, self.bounds, self.F, self.CR)

        # Apply cr_mask (subspace focusing) if set
        if self.cr_mask is not None and self.de_strategy != "best":
            # Force crossover only on specified dimensions
            NP, D = pop.shape
            for i in range(NP):
                # In masked dims, use trial; outside, use parent
                mask = self.cr_mask > 0
                trial[i] = np.where(mask, trial[i], pop[i])
        return trial

    def _de_selection(self, pop: np.ndarray, fit: np.ndarray, trial: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """NSGA-II selection: keep the better of parent vs trial."""
        trial_fit = self.evaluate_fn(trial)

        new_pop = pop.copy()
        new_fit = fit.copy()

        for i in range(len(pop)):
            # Trial dominates parent?
            if self._dominates(trial_fit[i], fit[i]):
                new_pop[i] = trial[i]
                new_fit[i] = trial_fit[i]
            elif self._dominates(fit[i], trial_fit[i]):
                pass  # keep parent
            else:
                # Non-dominated: in dynamic case, prefer trial
                if np.random.rand() < 0.5:
                    new_pop[i] = trial[i]
                    new_fit[i] = trial_fit[i]
        return new_pop, new_fit

    def _dominates(self, a: np.ndarray, b: np.ndarray) -> bool:
        return bool(np.all(a <= b) and np.any(a < b))

    def _invoke_llm(
        self,
        pop: np.ndarray,
        fit: np.ndarray,
        gen: int,
        trigger_info: Dict[str, Any],
        change_signal: Optional[float] = None,
    ):
        """Call LLM and apply its advice."""
        if self.llm is None:
            return
        try:
            advice = call_llm_for_advice(
                self.llm, pop, fit, self.bounds,
                generation=gen,
                trigger_info=trigger_info,
                change_signal=change_signal,
            )
            self.last_advice = advice
            self.advice_log.append({"gen": gen, "advice": advice})

            # Apply advice
            _, actions = apply_advice(pop, advice, self.bounds)
            self.de_strategy = actions.get("de_strategy", self.de_strategy)
            self.F = actions.get("F", self.F)
            self.CR = actions.get("CR", self.CR)
            self.cr_mask = actions.get("cr_mask", None)
            # Note: we keep population size fixed for simplicity.
            # Future work: dynamic pop size with re-evaluation.
        except Exception as e:
            print(f"[TLE] LLM invocation error: {e}")

    def _bandit_reward(self, prev_fit: np.ndarray, curr_fit: np.ndarray) -> float:
        """Compute reward for bandit: fitness improvement - LLM cost."""
        if prev_fit is None or curr_fit is None:
            return 0.0
        if prev_fit.shape != curr_fit.shape:
            return 0.0
        # Sum of objectives (for minimization, lower = better)
        prev_score = np.mean(np.sum(prev_fit, axis=1))
        curr_score = np.mean(np.sum(curr_fit, axis=1))
        improvement = (prev_score - curr_score) / (np.abs(prev_score) + 1e-6)
        # Normalize to [-1, 1] range
        reward = float(np.clip(improvement * 10, -1, 1))
        return reward

    def optimize(
        self,
        evaluate_fn: Callable,
        problem=None,
        on_change_fn: Optional[Callable] = None,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Main optimization loop.

        Args:
            evaluate_fn: function(pop) -> fitness
            problem: optional DMO problem for dynamic change detection
            on_change_fn: optional callback when change detected

        Returns:
            (final_pop, final_fitness, info_dict)
        """
        self.evaluate_fn = evaluate_fn

        # Initialize
        pop, fit = self._initialize()

        prev_fit_snapshot = fit.copy()
        history = {
            "best_fitness_per_gen": [],
            "invocations": 0,
            "decisions": [],
            "igds": [],
        }

        for gen in range(self.max_gen):
            # Check for environmental change (dynamic problems)
            change_signal = None
            if problem is not None and hasattr(problem, "is_change_step"):
                if problem.is_change_step(gen):
                    # Compute change signal by comparing populations/fitness
                    if prev_fit_snapshot is not None:
                        change_signal = problem.detect_change(prev_fit_snapshot, fit)
                    if on_change_fn is not None:
                        on_change_fn(gen, change_signal)

            # === Trigger: should we invoke LLM? ===
            trigger_fire, trigger_info = self.trigger.should_invoke(
                pop, fit, change_signal=change_signal
            )

            # === Bandit/Scheduler: budget control ===
            if trigger_fire and self.scheduler_name == "bandit":
                arm = self.scheduler.select_arm()
                bandit_invokes = (arm == 1)
            elif trigger_fire and self.scheduler_name in ("fixed", "heuristic"):
                bandit_invokes = self.scheduler.should_invoke()
            else:
                bandit_invokes = False

            # === LLM invocation ===
            if trigger_fire and bandit_invokes:
                self._invoke_llm(pop, fit, gen, trigger_info, change_signal)
                history["invocations"] += 1

            # === DE step ===
            trial = self._de_step(pop, fit)
            new_pop, new_fit = self._de_selection(pop, fit, trial)

            # === Bandit feedback (if invoked) ===
            if trigger_fire and bandit_invokes and self.scheduler_name == "bandit":
                reward = self._bandit_reward(fit, new_fit)
                self.scheduler.update(1, reward)
            elif self.scheduler_name == "bandit":
                # Update arm 0 (skip) with observed reward
                # We need to compute what would have happened with LLM
                # For simplicity, just track arm 0
                reward_no_llm = self._bandit_reward(fit, new_fit)
                self.scheduler.update(0, reward_no_llm)

            # === Update state ===
            pop, fit = new_pop, new_fit
            prev_fit_snapshot = fit.copy()

            # === Bookkeeping ===
            best_score = float(np.min(np.sum(fit, axis=1)))
            history["best_fitness_per_gen"].append(best_score)
            history["decisions"].append({
                "gen": gen,
                "trigger_fire": trigger_fire,
                "bandit_invokes": bandit_invokes,
                "strategy": self.de_strategy,
                "F": self.F,
                "CR": self.CR,
            })

            # === Advance problem time (so change_steps fills, dynamics active) ===
            if problem is not None and hasattr(problem, "step"):
                problem.step()

        # Final info
        info = {
            "invocations": history["invocations"],
            "total_gens": self.max_gen,
            "invocation_rate": history["invocations"] / self.max_gen,
            "trigger_stats": self.trigger.get_stats(),
            "scheduler_stats": self.scheduler.get_stats(),
            "best_fitness_history": history["best_fitness_per_gen"],
            "llm_stats": (self.llm.get_stats() if self.llm is not None else None),
        }
        if self.llm is not None:
            info["llm_stats"] = self.llm.get_stats()
        return pop, fit, info


# ==================== SOTA Baselines ====================
class PPSDMOEA:
    """
    Population Prediction Strategy for DMO (Zhou, Jin, Zhang, IEEE TCYB 2014).

    Maintains an archive of past Pareto-optimal centers. When environmental
    change is detected, predicts the new Pareto front center via linear
    extrapolation from the two most recent centers, then seeds the population
    with 50% predicted individuals + 50% random individuals.

    Reference:
        Zhou, A., Jin, Y., & Zhang, Q. (2014). A population prediction
        strategy for evolutionary dynamic multiobjective optimization.
        IEEE Transactions on Cybernetics, 44(1), 40-53.
    """

    def __init__(self, d, bounds, n_obj, pop_size=100, max_gen=300,
                 F=0.5, CR=0.9, seed=0, predict_ratio=0.5):
        self.d = d
        self.bounds = bounds
        self.n_obj = n_obj
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.F = F
        self.CR = CR
        self.seed = seed
        self.predict_ratio = predict_ratio
        np.random.seed(seed)

        # Archive of past Pareto-front centers
        self.center_history = []   # list of (center_array, generation)
        self.last_change_gen = -1
        self.last_change_signal = 0.0

    def _dominates(self, a, b):
        return bool(np.all(a <= b) and np.any(a < b))

    def _non_dominated_front(self, pop, fit):
        N = fit.shape[0]
        is_nd = np.ones(N, dtype=bool)
        for i in range(N):
            if not is_nd[i]:
                continue
            for j in range(N):
                if i == j or not is_nd[j]:
                    continue
                if self._dominates(fit[j], fit[i]):
                    is_nd[i] = False
                    break
        return pop[is_nd], fit[is_nd]

    def _center(self, fit):
        """Scalarized score: sum of objectives (minimization)."""
        return float(np.mean(np.sum(fit, axis=1)))

    def optimize(self, evaluate_fn, problem=None, on_change_fn=None):
        lower, upper = self.bounds
        pop = np.random.uniform(lower, upper, (self.pop_size, self.d))
        fit = evaluate_fn(pop)
        best_history = []

        prev_fit_snapshot = fit.copy()
        for gen in range(self.max_gen):
            # Environmental change handling
            if problem is not None and problem.is_change_step(gen):
                # Save current center for prediction
                nd_pop, nd_fit = self._non_dominated_front(pop, fit)
                if len(nd_pop) > 0:
                    center = np.mean(nd_pop, axis=0)
                    self.center_history.append((center, gen))
                # Keep only last 2
                if len(self.center_history) > 2:
                    self.center_history = self.center_history[-2:]

                # Predict new population
                n_pred = int(self.pop_size * self.predict_ratio)
                n_rand = self.pop_size - n_pred

                if len(self.center_history) == 2:
                    (c0, g0), (c1, g1) = self.center_history
                    dt = max(1, g1 - g0)
                    velocity = (c1 - c0) / dt
                    steps_ahead = gen + problem.taut - g1
                    predicted_center = c1 + velocity * steps_ahead
                    # Spread predictions around predicted center
                    spread = (upper - lower) * 0.1
                    new_pred = np.random.normal(
                        loc=predicted_center, scale=spread, size=(n_pred, self.d)
                    )
                else:
                    new_pred = np.random.uniform(lower, upper, (n_pred, self.d))

                new_rand = np.random.uniform(lower, upper, (n_rand, self.d))
                pop = np.vstack([new_pred, new_rand])
                pop = np.clip(pop, lower, upper)
                fit = evaluate_fn(pop)
                prev_fit_snapshot = fit.copy()

                if on_change_fn is not None:
                    on_change_fn(gen, 1.0)
                self.last_change_gen = gen

            # DE/rand/1/bin step
            trial = de_rand_1_bin(pop, fit, self.bounds, self.F, self.CR)
            trial_fit = evaluate_fn(trial)

            # NSGA-II-style selection
            new_pop = pop.copy()
            new_fit = fit.copy()
            for i in range(self.pop_size):
                if self._dominates(trial_fit[i], fit[i]):
                    new_pop[i] = trial[i]
                    new_fit[i] = trial_fit[i]
                elif self._dominates(fit[i], trial_fit[i]):
                    pass
                else:
                    if np.random.rand() < 0.5:
                        new_pop[i] = trial[i]
                        new_fit[i] = trial_fit[i]

            pop, fit = new_pop, new_fit
            best_history.append(float(np.min(np.sum(fit, axis=1))))

            # === Advance problem time ===
            if problem is not None and hasattr(problem, "step"):
                problem.step()

        return pop, fit, {"invocations": 0, "best_fitness_history": best_history}


# ==================== TLE-MA: Multi-Action Controller (A3) ====================
class TLEMultiAction:
    """
    TLE with multi-action LLM controller.

    Difference from TLE (the legacy config-advisor version):
      - At each LLM invocation, the LLM chooses ONE structural intervention
        from {param, archive_reset, restart_top, diversity_injection}
        instead of always returning F/CR/strategy changes.
      - History of past actions and their measured reward is fed back to
        the LLM so it can learn from its decisions.

    This is A3 in our "boosting contribution" plan. The architectural change
    is small (4-action dispatch) but the leverage is much higher because the
    LLM can now perform structural interventions (e.g., restart the top of
    the population after a change) that pure parameter tuning cannot.
    """

    def __init__(
        self,
        d: int,
        bounds: Tuple[np.ndarray, np.ndarray],
        n_obj: int,
        pop_size: int = 100,
        max_gen: int = 300,
        llm: Optional[LLMClient] = None,
        trigger: str = "triple",
        scheduler: str = "heuristic",
        seed: int = 0,
        history_window: int = 5,
        restrict_actions: Optional[List[str]] = None,
        budget: int = 50,
    ):
        """
        Args:
            restrict_actions: if not None, restrict LLM to a subset of
                actions (used for per-action ablation in B3).
                Example: restrict_actions=["param"] for the "only-param" ablation.
        """
        self.d = d
        self.bounds = bounds
        self.n_obj = n_obj
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.llm = llm
        self.seed = seed
        self.history_window = history_window
        self.restrict_actions = restrict_actions
        self.budget = budget

        np.random.seed(seed)

        # Trigger
        if trigger == "triple":
            self.trigger = TripleSignalTrigger()
        elif trigger == "always":
            from .triggers import AlwaysInvokeTrigger
            self.trigger = AlwaysInvokeTrigger()
        elif trigger == "never":
            from .triggers import NeverInvokeTrigger
            self.trigger = NeverInvokeTrigger()
        else:
            raise ValueError(f"Unknown trigger: {trigger}")

        # Scheduler: heuristic decay is known to beat UCB on DF5 ablation.
        if scheduler == "bandit":
            self.scheduler = UCBBandit()
        elif scheduler == "heuristic":
            from .bandit import HeuristicDecayScheduler
            self.scheduler = HeuristicDecayScheduler(self.budget)
        elif scheduler == "fixed":
            from .bandit import FixedBudgetScheduler
            self.scheduler = FixedBudgetScheduler(self.budget, max_gen)
        else:
            raise ValueError(f"Unknown scheduler: {scheduler}")
        self.scheduler_name = scheduler

        # DE state (modified by PARAM action)
        self.de_strategy = "rand"
        self.F = 0.5
        self.CR = 0.9

        # Multi-action history
        self.action_history: List[Dict[str, Any]] = []
        # Best fitness history (for progress signal in prompt)
        self.best_fitness_history: List[float] = []

    def _de_step(self, pop: np.ndarray, fit: np.ndarray) -> np.ndarray:
        """One DE step using current F, CR, strategy."""
        if self.de_strategy == "best":
            trial = de_best_1_bin(pop, fit, self.bounds, self.F, self.CR)
        elif self.de_strategy == "current_to_best":
            trial = de_current_to_best_1_bin(pop, fit, self.bounds, self.F, self.CR)
        else:
            trial = de_rand_1_bin(pop, fit, self.bounds, self.F, self.CR)
        return trial

    def _dominates(self, a: np.ndarray, b: np.ndarray) -> bool:
        return bool(np.all(a <= b) and np.any(a < b))

    def _de_selection(self, pop, fit, trial):
        trial_fit = self.evaluate_fn(trial)
        new_pop = pop.copy()
        new_fit = fit.copy()
        for i in range(len(pop)):
            if self._dominates(trial_fit[i], fit[i]):
                new_pop[i] = trial[i]
                new_fit[i] = trial_fit[i]
            elif self._dominates(fit[i], trial_fit[i]):
                pass
            else:
                if np.random.rand() < 0.5:
                    new_pop[i] = trial[i]
                    new_fit[i] = trial_fit[i]
        return new_pop, new_fit

    def _invoke_llm_action(
        self,
        pop: np.ndarray,
        fit: np.ndarray,
        gen: int,
        trigger_info: Dict[str, Any],
        change_signal: Optional[float] = None,
    ) -> Optional[Action]:
        """Call LLM, parse, validate. Returns Action or None."""
        if self.llm is None:
            return None
        try:
            advice = call_llm_for_multi_action(
                self.llm, pop, fit, self.bounds,
                generation=gen,
                trigger_info=trigger_info,
                change_signal=change_signal,
                action_history=self.action_history[-self.history_window:],
                best_fitness_history=self.best_fitness_history,
            )
            action = Action(
                action_type=advice["action_type"],
                params=advice.get("params", {}),
                reasoning=advice.get("reasoning", ""),
            )
            # Apply restrict_actions filter (B3 ablation)
            if self.restrict_actions is not None and action.action_type not in self.restrict_actions:
                # If LLM picked a disallowed action, fall back to first allowed
                action.action_type = self.restrict_actions[0]
            return action
        except Exception as e:
            print(f"[TLE-MA] LLM invocation error: {e}")
            return None

    def _apply_action(
        self,
        action: Action,
        pop: np.ndarray,
        fit: np.ndarray,
        archive: Optional[List],
    ) -> Tuple[np.ndarray, np.ndarray, List, Dict[str, Any]]:
        """
        Dispatch action to its implementation. Returns (new_pop, new_fit,
        new_archive, info). Caller is responsible for re-evaluating fit
        if any action returned a sentinel (NaN in fit).
        """
        info = {"action_type": action.action_type}
        new_archive = list(archive) if archive is not None else []

        if action.action_type == "param":
            changes = execute_param_action(action, {
                "F": self.F, "CR": self.CR, "de_strategy": self.de_strategy,
            })
            if "F" in changes: self.F = changes["F"]
            if "CR" in changes: self.CR = changes["CR"]
            if "de_strategy" in changes: self.de_strategy = changes["de_strategy"]
            info["state_changes"] = changes
            return pop, fit, new_archive, info

        elif action.action_type == "archive_reset":
            pop, fit, new_archive = execute_archive_reset_action(
                action, pop, fit, self.bounds, archive=new_archive,
            )
            return pop, fit, new_archive, info

        elif action.action_type == "restart_top":
            pop, fit = execute_restart_top_action(action, pop, fit, self.bounds)
            return pop, fit, new_archive, info

        elif action.action_type == "diversity_injection":
            pop, fit = execute_diversity_injection_action(action, pop, fit, self.bounds)
            return pop, fit, new_archive, info

        else:
            # Unknown action: no-op
            return pop, fit, new_archive, info

    def _reward(self, prev_fit: np.ndarray, curr_fit: np.ndarray) -> float:
        """Same reward as TLE._bandit_reward for consistency."""
        if prev_fit is None or curr_fit is None:
            return 0.0
        if prev_fit.shape != curr_fit.shape:
            return 0.0
        prev_score = np.mean(np.sum(prev_fit, axis=1))
        curr_score = np.mean(np.sum(curr_fit, axis=1))
        improvement = (prev_score - curr_score) / (np.abs(prev_score) + 1e-6)
        return float(np.clip(improvement * 10, -1, 1))

    def optimize(
        self,
        evaluate_fn: Callable,
        problem=None,
        on_change_fn: Optional[Callable] = None,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Main optimization loop with multi-action controller."""
        self.evaluate_fn = evaluate_fn
        archive: List = []

        lower, upper = self.bounds
        pop = np.random.uniform(lower, upper, (self.pop_size, self.d))
        fit = evaluate_fn(pop)

        history = {
            "best_fitness_per_gen": [],
            "invocations": 0,
            "actions_taken": [],   # NEW: record action distribution
            "igds": [],
        }

        prev_fit_snapshot = fit.copy()

        for gen in range(self.max_gen):
            # Detect environmental change
            change_signal = None
            if problem is not None and hasattr(problem, "is_change_step"):
                if problem.is_change_step(gen):
                    if prev_fit_snapshot is not None:
                        change_signal = problem.detect_change(prev_fit_snapshot, fit)
                    if on_change_fn is not None:
                        on_change_fn(gen, change_signal)

            # === Trigger ===
            trigger_fire, trigger_info = self.trigger.should_invoke(
                pop, fit, change_signal=change_signal,
            )

            # === Scheduler ===
            if trigger_fire and self.scheduler_name == "bandit":
                arm = self.scheduler.select_arm()
                bandit_invokes = (arm == 1)
            elif trigger_fire and self.scheduler_name in ("fixed", "heuristic"):
                bandit_invokes = self.scheduler.should_invoke()
            else:
                bandit_invokes = False

            # === LLM action ===
            action = None
            if trigger_fire and bandit_invokes:
                action = self._invoke_llm_action(pop, fit, gen, trigger_info, change_signal)
                if action is not None:
                    prev_fit_for_reward = fit.copy()
                    pop, fit, archive, info = self._apply_action(action, pop, fit, archive)
                    history["invocations"] += 1
                    history["actions_taken"].append(action.action_type)

            # If any action invalidated fit (NaN sentinel), re-evaluate
            if np.any(np.isnan(fit)):
                nan_idx = np.where(np.isnan(fit[:, 0]))[0]
                if len(nan_idx) > 0:
                    fit[nan_idx] = evaluate_fn(pop[nan_idx])

            # === DE step ===
            trial = self._de_step(pop, fit)
            new_pop, new_fit = self._de_selection(pop, fit, trial)

            # === Reward (if action was taken) ===
            if action is not None:
                reward = self._reward(fit, new_fit)
                self.action_history.append({
                    "gen": gen,
                    "action_type": action.action_type,
                    "params": dict(action.params),
                    "reward": reward,
                })
                if self.scheduler_name == "bandit":
                    self.scheduler.update(1, reward)

            # === Advance ===
            pop, fit = new_pop, new_fit
            prev_fit_snapshot = fit.copy()

            best_score = float(np.min(np.sum(fit, axis=1)))
            history["best_fitness_per_gen"].append(best_score)
            self.best_fitness_history.append(best_score)

            # === Advance problem time ===
            if problem is not None and hasattr(problem, "step"):
                problem.step()

        # Final info
        from collections import Counter
        action_dist = Counter(history["actions_taken"])
        info = {
            "invocations": history["invocations"],
            "total_gens": self.max_gen,
            "invocation_rate": history["invocations"] / self.max_gen,
            "action_distribution": dict(action_dist),
            "best_fitness_history": history["best_fitness_per_gen"],
            "llm_stats": (self.llm.get_stats() if self.llm is not None else None),
            "history_length": len(self.action_history),
        }
        return pop, fit, info


# ==================== Baselines ====================
class DEBaseline:
    """Plain DE without LLM."""

    def __init__(self, d, bounds, n_obj, pop_size=100, max_gen=300,
                 F=0.5, CR=0.9, strategy="rand", seed=0):
        self.d = d
        self.bounds = bounds
        self.n_obj = n_obj
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.F = F
        self.CR = CR
        self.strategy = strategy
        self.seed = seed
        np.random.seed(seed)

    def _dominates(self, a, b):
        return bool(np.all(a <= b) and np.any(a < b))

    def optimize(self, evaluate_fn, problem=None, on_change_fn=None):
        lower, upper = self.bounds
        pop = np.random.uniform(lower, upper, (self.pop_size, self.d))
        fit = evaluate_fn(pop)
        best_history = []

        prev_fit_snapshot = fit.copy()
        for gen in range(self.max_gen):
            if problem is not None and problem.is_change_step(gen):
                if on_change_fn is not None:
                    on_change_fn(gen, 0.0)
            # DE step
            if self.strategy == "best":
                trial = de_best_1_bin(pop, fit, self.bounds, self.F, self.CR)
            elif self.strategy == "current_to_best":
                trial = de_current_to_best_1_bin(pop, fit, self.bounds, self.F, self.CR)
            else:
                trial = de_rand_1_bin(pop, fit, self.bounds, self.F, self.CR)
            trial_fit = evaluate_fn(trial)
            # Selection
            for i in range(self.pop_size):
                if self._dominates(trial_fit[i], fit[i]):
                    pop[i] = trial[i]
                    fit[i] = trial_fit[i]
                elif self._dominates(fit[i], trial_fit[i]):
                    pass
                else:
                    if np.random.rand() < 0.5:
                        pop[i] = trial[i]
                        fit[i] = trial_fit[i]
            best_history.append(float(np.min(np.sum(fit, axis=1))))
            prev_fit_snapshot = fit.copy()
            # === Advance problem time ===
            if problem is not None and hasattr(problem, "step"):
                problem.step()
        return pop, fit, {"invocations": 0, "best_fitness_history": best_history}


class StaticLMEABaseline:
    """LLM-EA that invokes LLM every generation (no trigger)."""

    def __init__(self, d, bounds, n_obj, pop_size=100, max_gen=300,
                 llm=None, seed=0):
        self.d = d
        self.bounds = bounds
        self.n_obj = n_obj
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.llm = llm
        self.seed = seed
        np.random.seed(seed)

    def optimize(self, evaluate_fn, problem=None, on_change_fn=None):
        # Wrap TLE with always-trigger, no bandit (always invoke)
        inner = TLE(
            d=self.d, bounds=self.bounds, n_obj=self.n_obj,
            pop_size=self.pop_size, max_gen=self.max_gen,
            llm=self.llm, trigger="always", scheduler="fixed",
            budget=self.max_gen, seed=self.seed,
        )
        return inner.optimize(evaluate_fn, problem, on_change_fn)


class RandomLMEABaseline:
    """LLM-EA that invokes LLM at random times (10% of generations)."""

    def __init__(self, d, bounds, n_obj, pop_size=100, max_gen=300,
                 llm=None, rate=0.1, seed=0):
        self.d = d
        self.bounds = bounds
        self.n_obj = n_obj
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.llm = llm
        self.rate = rate
        self.seed = seed
        np.random.seed(seed)

    def optimize(self, evaluate_fn, problem=None, on_change_fn=None):
        # Custom random trigger TLE
        from .triggers import TripleSignalTrigger
        trigger = TripleSignalTrigger()
        # Override should_invoke behavior
        original_should = trigger.should_invoke
        def random_should(*args, **kwargs):
            fire = np.random.rand() < self.rate
            return fire, {"random_trigger": fire}
        trigger.should_invoke = random_should
        trigger.fire_count = 0
        trigger.total_count = 0
        inner = TLE(
            d=self.d, bounds=self.bounds, n_obj=self.n_obj,
            pop_size=self.pop_size, max_gen=self.max_gen,
            llm=self.llm, trigger="always", scheduler="fixed",
            budget=int(self.max_gen * self.rate), seed=self.seed,
        )
        # Replace trigger
        inner.trigger = trigger
        return inner.optimize(evaluate_fn, problem, on_change_fn)


# ==================== DNSGA-II-A: Dynamic NSGA-II with random immigrants ====================
class DNSGAIIA:
    """
    DNSGA-II-A (Deb et al. 2007): NSGA-II backbone for DMO with random
    immigrants on environmental change. When a change is detected, replace
    a fraction (default 20%) of the population with random individuals to
    maintain diversity and track the new Pareto front.

    Reference:
        Deb, K., Rao N., U. B., & Karthik, S. (2007). Dynamic multi-objective
        optimization and decision-making using modified NSGA-II: A case study
        on hydro-thermal power scheduling. In International Conference on
        Evolutionary Multi-Criterion Optimization (EMO) (pp. 803-817). Springer.
    """

    def __init__(self, d, bounds, n_obj, pop_size=100, max_gen=300,
                 eta_c=20, eta_m=20, immigrant_frac=0.2, seed=0):
        self.d = d
        self.bounds = bounds
        self.n_obj = n_obj
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.eta_c = eta_c       # SBX crossover distribution index
        self.eta_m = eta_m       # polynomial mutation distribution index
        self.immigrant_frac = immigrant_frac
        self.seed = seed
        np.random.seed(seed)

    def _sbx_crossover(self, p1, p2):
        """Simulated Binary Crossover."""
        c1, c2 = p1.copy(), p2.copy()
        if np.random.rand() > 0.5:
            return c1, c2
        for i in range(self.d):
            if np.random.rand() > 0.5:
                continue
            u = np.random.rand()
            if u <= 0.5:
                beta = (2 * u) ** (1.0 / (self.eta_c + 1))
            else:
                beta = (1.0 / (2 * (1 - u))) ** (1.0 / (self.eta_c + 1))
            c1[i] = 0.5 * ((1 + beta) * p1[i] + (1 - beta) * p2[i])
            c2[i] = 0.5 * ((1 - beta) * p1[i] + (1 + beta) * p2[i])
        return c1, c2

    def _polynomial_mutation(self, x):
        """Polynomial mutation."""
        y = x.copy()
        lower, upper = self.bounds
        for i in range(self.d):
            if np.random.rand() > (1.0 / self.d):
                continue
            u = np.random.rand()
            if u < 0.5:
                delta = (2 * u) ** (1.0 / (self.eta_m + 1)) - 1
            else:
                delta = 1 - (2 * (1 - u)) ** (1.0 / (self.eta_m + 1))
            y[i] = x[i] + delta * (upper[i] - lower[i])
        return np.clip(y, lower, upper)

    def _non_dominated_sort_idx(self, fit):
        N = fit.shape[0]
        domination_count = np.zeros(N, dtype=int)
        dominated_set = [[] for _ in range(N)]
        fronts = [[]]
        for p in range(N):
            for q in range(N):
                if p == q:
                    continue
                if np.all(fit[p] <= fit[q]) and np.any(fit[p] < fit[q]):
                    dominated_set[p].append(q)
                elif np.all(fit[q] <= fit[p]) and np.any(fit[q] < fit[p]):
                    domination_count[p] += 1
            if domination_count[p] == 0:
                fronts[0].append(p)
        i = 0
        while fronts[i]:
            nxt = []
            for p in fronts[i]:
                for q in dominated_set[p]:
                    domination_count[q] -= 1
                    if domination_count[q] == 0:
                        nxt.append(q)
            i += 1
            fronts.append(nxt)
        fronts.pop()
        return fronts

    def _crowding_distance(self, fit, front):
        n = len(front)
        if n == 0:
            return np.array([])
        if n <= 2:
            return np.full(n, np.inf)
        d = np.zeros(n)
        front_fit = fit[front]
        M = front_fit.shape[1]
        for m in range(M):
            order = np.argsort(front_fit[:, m])
            d[order[0]] = np.inf
            d[order[-1]] = np.inf
            rng = front_fit[order[-1], m] - front_fit[order[0], m]
            if rng < 1e-12:
                continue
            for i in range(1, n - 1):
                d[order[i]] += (front_fit[order[i + 1], m] - front_fit[order[i - 1], m]) / rng
        return d

    def optimize(self, evaluate_fn, problem=None, on_change_fn=None):
        lower, upper = self.bounds
        pop = np.random.uniform(lower, upper, (self.pop_size, self.d))
        fit = evaluate_fn(pop)
        best_history = []

        for gen in range(self.max_gen):
            # === On environmental change: introduce random immigrants ===
            if problem is not None and problem.is_change_step(gen):
                n_immig = max(1, int(self.pop_size * self.immigrant_frac))
                idx = np.random.choice(self.pop_size, n_immig, replace=False)
                pop[idx] = np.random.uniform(lower, upper, (n_immig, self.d))
                fit[idx] = evaluate_fn(pop[idx])
                if on_change_fn is not None:
                    on_change_fn(gen, 1.0)

            # === NSGA-II offspring generation ===
            offspring_pop = np.empty_like(pop)
            for i in range(0, self.pop_size, 2):
                p1, p2 = pop[i % self.pop_size], pop[(i + 1) % self.pop_size]
                c1, c2 = self._sbx_crossover(p1, p2)
                c1 = self._polynomial_mutation(c1)
                c2 = self._polynomial_mutation(c2)
                offspring_pop[i] = c1
                if i + 1 < self.pop_size:
                    offspring_pop[i + 1] = c2
            offspring_fit = evaluate_fn(offspring_pop)

            # === Combine and select ===
            combined_pop = np.vstack([pop, offspring_pop])
            combined_fit = np.vstack([fit, offspring_fit])
            fronts = self._non_dominated_sort_idx(combined_fit)

            new_pop = np.empty_like(pop)
            new_fit = np.empty_like(fit)
            sel = 0
            for front in fronts:
                if sel + len(front) <= self.pop_size:
                    for idx in front:
                        new_pop[sel] = combined_pop[idx]
                        new_fit[sel] = combined_fit[idx]
                        sel += 1
                else:
                    cd = self._crowding_distance(combined_fit, front)
                    order = np.array(front)[np.argsort(-cd)]
                    need = self.pop_size - sel
                    for idx in order[:need]:
                        new_pop[sel] = combined_pop[idx]
                        new_fit[sel] = combined_fit[idx]
                        sel += 1
                    break
            pop, fit = new_pop, new_fit
            best_history.append(float(np.min(np.sum(fit, axis=1))))

            # === Advance problem time ===
            if problem is not None and hasattr(problem, "step"):
                problem.step()

        return pop, fit, {"invocations": 0, "best_fitness_history": best_history}
