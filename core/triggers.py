"""
Triple-Signal Trigger Mechanism
==============================
Three signals that decide when to invoke the LLM during EA search:

  Signal 1: Population diversity entropy descent
  Signal 2: Fitness stagnation counter
  Signal 3: Environmental change detection (for dynamic problems)
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any


class TripleSignalTrigger:
    """
    Combines 3 signals to decide when to invoke the LLM.

    Returns True (invoke LLM) if ANY signal fires.
    """

    def __init__(
        self,
        entropy_threshold: float = 0.05,
        stagnation_threshold: int = 10,
        change_threshold: float = 0.05,
        history_window: int = 5,
    ):
        self.entropy_threshold = entropy_threshold
        self.stagnation_threshold = stagnation_threshold
        self.change_threshold = change_threshold
        self.history_window = history_window

        # Internal state
        self.prev_entropy = None
        self.stagnation_counter = 0
        self.prev_best_fitness = None
        self.prev_population_snapshot = None
        self.fitness_history = []
        self.fire_count = 0
        self.total_count = 0
        self.fire_history = []  # for analysis

    def reset(self):
        self.prev_entropy = None
        self.stagnation_counter = 0
        self.prev_best_fitness = None
        self.prev_population_snapshot = None
        self.fitness_history = []

    def should_invoke(
        self,
        population: np.ndarray,
        fitness: np.ndarray,
        change_signal: Optional[float] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Decide whether to invoke the LLM at the current generation.

        Args:
            population: shape (NP, D)
            fitness: shape (NP, M) — multi-objective fitness
            change_signal: optional externally provided change indicator
                           (e.g., from environment detection in dynamic problems)

        Returns:
            (should_invoke, info_dict)
        """
        self.total_count += 1
        info = {
            "signal_1_entropy": False,
            "signal_2_stagnation": False,
            "signal_3_change": False,
            "entropy_value": None,
            "stagnation_count": 0,
            "change_value": change_signal,
        }

        # ============ Signal 1: Entropy Descent ============
        entropy = self._compute_population_entropy(population)
        info["entropy_value"] = float(entropy)
        signal_1_fired = False
        if self.prev_entropy is not None:
            entropy_drop = self.prev_entropy - entropy
            if entropy_drop > self.entropy_threshold:
                signal_1_fired = True
                info["signal_1_entropy"] = True
        self.prev_entropy = entropy

        # ============ Signal 2: Fitness Stagnation ============
        # Average best fitness over current generation
        # For multi-objective, use sum of objectives as scalar (lower = better for min)
        # For maximization, flip sign.
        if fitness.ndim == 2:
            current_scalar = float(np.min(np.sum(fitness, axis=1)))
        else:
            current_scalar = float(np.min(fitness))

        if self.prev_best_fitness is not None:
            improvement = self.prev_best_fitness - current_scalar
            if abs(improvement) < 1e-6:
                self.stagnation_counter += 1
            else:
                self.stagnation_counter = 0
        self.prev_best_fitness = current_scalar
        info["stagnation_count"] = self.stagnation_counter

        signal_2_fired = (self.stagnation_counter >= self.stagnation_threshold)
        if signal_2_fired:
            info["signal_2_stagnation"] = True
            # Reset after firing (avoid continuous firing)
            self.stagnation_counter = 0

        # ============ Signal 3: Environmental Change Detection ============
        signal_3_fired = False
        if change_signal is not None and change_signal > self.change_threshold:
            signal_3_fired = True
            info["signal_3_change"] = True
        # Also detect by population snapshot shift (for dynamic problems)
        elif self.prev_population_snapshot is not None:
            # Compute shift in best individual's position
            best_idx = np.argmin(np.sum(fitness, axis=1)) if fitness.ndim == 2 else np.argmin(fitness)
            best_now = population[best_idx]
            shift = np.linalg.norm(best_now - self.prev_population_snapshot)
            if shift > self.change_threshold * 10:  # scaled
                signal_3_fired = True
                info["signal_3_change"] = True
        # Save snapshot
        if fitness.ndim == 2:
            best_idx = np.argmin(np.sum(fitness, axis=1))
        else:
            best_idx = np.argmin(fitness)
        self.prev_population_snapshot = population[best_idx].copy()

        # ============ Combine: any signal fires ============
        should = signal_1_fired or signal_2_fired or signal_3_fired

        if should:
            self.fire_count += 1

        self.fire_history.append({
            "should_invoke": should,
            "entropy": info["entropy_value"],
            "stagnation": self.stagnation_counter,
            "change": change_signal,
        })

        return should, info

    def _compute_population_entropy(self, population: np.ndarray) -> float:
        """
        Compute population diversity entropy.
        Higher entropy = more diverse population.
        We use the average pairwise distance normalized by bounds range.
        """
        NP, D = population.shape
        if NP < 2:
            return 0.0

        # Use a sample to make it O(N) instead of O(N^2)
        n_sample = min(NP, 50)
        idx = np.random.choice(NP, n_sample, replace=False)
        sub_pop = population[idx]

        # Average pairwise L2 distance
        dists = np.mean(np.linalg.norm(
            sub_pop[:, None, :] - sub_pop[None, :, :], axis=2
        ))

        # Normalize by sqrt(D) (max possible distance is bounded by range)
        # In [0,1] normalized space, max dist = sqrt(D)
        return float(dists / np.sqrt(D))

    def get_stats(self) -> Dict[str, Any]:
        """Return trigger statistics."""
        rate = self.fire_count / max(1, self.total_count)
        return {
            "total_generations": self.total_count,
            "llm_invocations": self.fire_count,
            "invocation_rate": rate,
        }


class DoubleSignalTrigger:
    """Double-signal trigger (entropy + stagnation, no change detection) — ablation.

    Same as TripleSignalTrigger but ignores the environmental-change signal.
    Used in Section 5.5 to isolate the contribution of the change signal.
    """

    def __init__(
        self,
        entropy_threshold: float = 0.05,
        stagnation_threshold: int = 10,
    ):
        self.entropy_threshold = entropy_threshold
        self.stagnation_threshold = stagnation_threshold
        # Internal state (mirror of TripleSignalTrigger without change tracking)
        self.prev_entropy = None
        self.stagnation_counter = 0
        self.prev_best_fitness = None
        self.fire_count = 0
        self.total_count = 0
        self.fire_history = []

    def reset(self):
        self.prev_entropy = None
        self.stagnation_counter = 0
        self.prev_best_fitness = None

    def should_invoke(
        self,
        population: np.ndarray,
        fitness: np.ndarray,
        change_signal: Optional[float] = None,  # accepted but IGNORED
    ) -> Tuple[bool, Dict[str, Any]]:
        self.total_count += 1
        info = {
            "signal_1_entropy": False,
            "signal_2_stagnation": False,
            "entropy_value": None,
            "stagnation_count": 0,
        }
        # Signal 1: entropy descent
        entropy = self._compute_population_entropy(population)
        info["entropy_value"] = float(entropy)
        s1 = False
        if self.prev_entropy is not None:
            if self.prev_entropy - entropy > self.entropy_threshold:
                s1 = True
                info["signal_1_entropy"] = True
        self.prev_entropy = entropy
        # Signal 2: stagnation
        if fitness.ndim == 2:
            cur = float(np.min(np.sum(fitness, axis=1)))
        else:
            cur = float(np.min(fitness))
        if self.prev_best_fitness is not None:
            imp = self.prev_best_fitness - cur
            if abs(imp) < 1e-6:
                self.stagnation_counter += 1
            else:
                self.stagnation_counter = 0
        self.prev_best_fitness = cur
        info["stagnation_count"] = self.stagnation_counter
        s2 = (self.stagnation_counter >= self.stagnation_threshold)
        if s2:
            info["signal_2_stagnation"] = True
            self.stagnation_counter = 0  # reset after firing
        should = s1 or s2
        if should:
            self.fire_count += 1
        self.fire_history.append({
            "should_invoke": should,
            "entropy": info["entropy_value"],
            "stagnation": self.stagnation_counter,
        })
        return should, info

    def _compute_population_entropy(self, population: np.ndarray) -> float:
        NP, D = population.shape
        if NP < 2:
            return 0.0
        n_sample = min(NP, 50)
        idx = np.random.choice(NP, n_sample, replace=False)
        sub_pop = population[idx]
        dists = float(np.mean(np.linalg.norm(
            sub_pop[:, None, :] - sub_pop[None, :, :], axis=2
        )))
        return dists / np.sqrt(D)

    def get_stats(self) -> Dict[str, Any]:
        rate = self.fire_count / max(1, self.total_count)
        return {
            "total_generations": self.total_count,
            "llm_invocations": self.fire_count,
            "invocation_rate": rate,
        }


class SingleSignalTrigger:
    """Single-signal trigger (entropy only) — used as ablation."""

    def __init__(self, entropy_threshold: float = 0.05):
        self.entropy_threshold = entropy_threshold
        self.prev_entropy = None
        self.fire_count = 0
        self.total_count = 0

    def should_invoke(
        self,
        population: np.ndarray,
        fitness: np.ndarray,
        change_signal: Optional[float] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        self.total_count += 1
        entropy = self._compute_population_entropy(population)
        fire = False
        if self.prev_entropy is not None:
            if self.prev_entropy - entropy > self.entropy_threshold:
                fire = True
        self.prev_entropy = entropy
        if fire:
            self.fire_count += 1
        return fire, {"entropy": entropy}

    def _compute_population_entropy(self, population: np.ndarray) -> float:
        NP, D = population.shape
        if NP < 2:
            return 0.0
        n_sample = min(NP, 50)
        idx = np.random.choice(NP, n_sample, replace=False)
        sub_pop = population[idx]
        dists = np.mean(np.linalg.norm(
            sub_pop[:, None, :] - sub_pop[None, :, :], axis=2
        ))
        return float(dists / np.sqrt(D))

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_generations": self.total_count,
            "llm_invocations": self.fire_count,
            "invocation_rate": self.fire_count / max(1, self.total_count),
        }


class AlwaysInvokeTrigger:
    """Invoke LLM every generation — used as ablation upper bound."""

    def __init__(self):
        self.fire_count = 0
        self.total_count = 0

    def should_invoke(self, *args, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        self.total_count += 1
        self.fire_count += 1
        return True, {}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_generations": self.total_count,
            "llm_invocations": self.fire_count,
            "invocation_rate": 1.0,
        }


class NeverInvokeTrigger:
    """No LLM — pure EA baseline."""

    def __init__(self):
        self.fire_count = 0
        self.total_count = 0

    def should_invoke(self, *args, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        self.total_count += 1
        return False, {}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_generations": self.total_count,
            "llm_invocations": 0,
            "invocation_rate": 0.0,
        }
