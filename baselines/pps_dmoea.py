"""
PPS-DMOEA baseline (Population Prediction Strategy, Zhou et al. 2014).
Simplified implementation for our TLE comparison.

Reference: Zhou, A., Jin, Y., Zhang, Q. (2014). A population prediction
strategy for evolutionary dynamic multiobjective optimization.
IEEE Trans. Cybernetics, 44(1), 40-53.

Core idea:
- Maintain two consecutive historical population centers
- When change is detected, predict the next population center
  via linear extrapolation: x_pred(t+1) = 2*x(t) - x(t-1)
- Initialize half the new population around x_pred, half randomly
- If prediction is poor (center distance > threshold), use full restart
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any

from core.de_operators import de_rand_1_bin
from core.moo_utils import fast_non_dominated_sort


class PPSDEBaseline:
    """
    DE enhanced with Population Prediction Strategy for dynamic problems.
    """

    def __init__(self, d, bounds, n_obj, pop_size=50, max_gen=200,
                 F=0.5, CR=0.9, restart_ratio=0.5, seed=0):
        self.d = d
        self.bounds = bounds
        self.n_obj = n_obj
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.F = F
        self.CR = CR
        self.restart_ratio = restart_ratio
        self.seed = seed
        np.random.seed(seed)

        # State
        self.prev_center = None
        self.curr_center = None
        self.change_detected = False
        self.problem_taut = 10  # default, will be set by DMOProblem.taut

    def _detect_change(self, prev_fit, curr_fit, threshold=0.05):
        if prev_fit is None or curr_fit is None:
            return False
        if prev_fit.shape != curr_fit.shape:
            return True
        diff = np.abs(curr_fit - prev_fit)
        denom = np.abs(prev_fit) + 1e-6
        rel_change = np.mean(diff / denom)
        return rel_change > threshold

    def _should_change_at(self, gen):
        """Check if environmental change should happen at this generation."""
        # In our DMOProblem, change happens at t % taut == 0
        # t is incremented at the END of each gen, so change at gen+1 == t
        # i.e., change happens at gen where (gen+1) % taut == 0
        return (gen + 1) % self.problem_taut == 0

    def _reinitialize(self, pop, fit, problem):
        """PPS: predict next center, reinitialize half population."""
        n = pop.shape[0]
        n_pred = int(n * self.restart_ratio)
        n_rand = n - n_pred

        if self.prev_center is not None and self.curr_center is not None:
            # Linear extrapolation
            x_pred = 2 * self.curr_center - self.prev_center
            x_pred = np.clip(x_pred, self.bounds[0], self.bounds[1])
            # Add noise around prediction
            sigma = 0.1 * (self.bounds[1] - self.bounds[0])
            new_pred = x_pred + np.random.normal(0, sigma, (n_pred, self.d))
            new_pred = np.clip(new_pred, self.bounds[0], self.bounds[1])
        else:
            new_pred = np.random.uniform(self.bounds[0], self.bounds[1], (n_pred, self.d))

        # Random half
        new_rand = np.random.uniform(self.bounds[0], self.bounds[1], (n_rand, self.d))

        # Combine: keep top 20% from old, plus predicted + random
        n_keep = max(1, int(n * 0.2))
        n_pred = n - n_keep - n_rand

        if self.prev_center is not None and self.curr_center is not None:
            x_pred = 2 * self.curr_center - self.prev_center
            x_pred = np.clip(x_pred, self.bounds[0], self.bounds[1])
            sigma = 0.1 * (self.bounds[1] - self.bounds[0])
            new_pred = x_pred + np.random.normal(0, sigma, (n_pred, self.d))
            new_pred = np.clip(new_pred, self.bounds[0], self.bounds[1])
        else:
            new_pred = np.random.uniform(self.bounds[0], self.bounds[1], (n_pred, self.d))

        new_rand = np.random.uniform(self.bounds[0], self.bounds[1], (n_rand, self.d))

        # Keep top n_keep by sum of objectives
        scores = np.sum(fit, axis=1)
        top_idx = np.argsort(scores)[:n_keep]
        new_pop = np.vstack([pop[top_idx], new_pred, new_rand])

        # Update center
        self.prev_center = self.curr_center.copy() if self.curr_center is not None else None
        self.curr_center = np.mean(new_pop, axis=0)

        return new_pop

    def _dominates(self, a, b):
        return bool(np.all(a <= b) and np.any(a < b))

    def optimize(self, evaluate_fn, problem=None, on_change_fn=None):
        lower, upper = self.bounds
        pop = np.random.uniform(lower, upper, (self.pop_size, self.d))
        fit = evaluate_fn(pop)
        self.curr_center = np.mean(pop, axis=0)
        best_history = []
        prev_fit_snapshot = fit.copy()
        if problem is not None:
            self.problem_taut = problem.taut

        for gen in range(self.max_gen):
            # Detect change
            if problem is not None and hasattr(problem, "is_change_step"):
                if problem.is_change_step(gen) or self._should_change_at(gen):
                    self.change_detected = True
                    if on_change_fn is not None:
                        on_change_fn(gen, 0.0)
            # Also use statistical detection
            if self._detect_change(prev_fit_snapshot, fit):
                self.change_detected = True

            if self.change_detected:
                # Reinitialize using PPS
                pop = self._reinitialize(pop, fit, problem)
                fit = evaluate_fn(pop)
                self.change_detected = False

            # DE step
            trial = de_rand_1_bin(pop, fit, self.bounds, self.F, self.CR)
            trial_fit = evaluate_fn(trial)
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

        return pop, fit, {"invocations": 0, "best_fitness_history": best_history}
