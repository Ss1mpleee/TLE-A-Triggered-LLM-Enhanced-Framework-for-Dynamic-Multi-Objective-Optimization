"""
Bandit-Based Budget Scheduler
=============================
UCB1 algorithm for adaptively deciding whether to invoke the LLM
based on historical reward.

Reference: Auer, Cesa-Bianchi, Fischer, "Finite-time Analysis of the
Multiarmed Bandit Problem", Machine Learning, 2002.
"""
import numpy as np
from typing import Optional


class UCBBandit:
    """
    2-arm Bernoulli bandit for LLM invocation:
    - arm 0: skip LLM this generation
    - arm 1: invoke LLM this generation

    Reward = improvement in fitness - cost of LLM call (normalized).

    Regret bound: O(sqrt(T log T)) over T generations.
    """

    def __init__(
        self,
        c: float = 1.414,  # exploration parameter
        cost_per_call: float = 0.05,  # normalized cost
    ):
        self.c = c
        self.cost_per_call = cost_per_call

        # For each arm
        self.counts = np.zeros(2)
        self.values = np.zeros(2)  # estimated reward
        self.t = 0
        self.history = []  # for analysis

    def select_arm(self) -> int:
        """Select arm via UCB1."""
        self.t += 1
        # Initial exploration: try each arm once
        for arm in [0, 1]:
            if self.counts[arm] == 0:
                return arm

        ucb = self.values + self.c * np.sqrt(np.log(self.t) / self.counts)
        return int(np.argmax(ucb))

    def update(self, arm: int, reward: float):
        """Update arm statistics with observed reward."""
        self.counts[arm] += 1
        # Incremental average
        n = self.counts[arm]
        self.values[arm] += (reward - self.values[arm]) / n
        self.history.append({
            "t": self.t,
            "arm": arm,
            "reward": reward,
        })

    def should_invoke(self) -> bool:
        """Whether to invoke LLM this round (UCB decision)."""
        return self.select_arm() == 1

    def get_stats(self) -> dict:
        return {
            "arm0_count": int(self.counts[0]),
            "arm1_count": int(self.counts[1]),
            "arm0_value": float(self.values[0]),
            "arm1_value": float(self.values[1]),
            "total_rounds": self.t,
        }


class FixedBudgetScheduler:
    """Fixed LLM call budget (e.g., total 50 calls). Used as ablation."""

    def __init__(self, total_budget: int, total_generations: int):
        self.total_budget = total_budget
        self.total_generations = total_generations
        # Pre-allocate: call every Nth generation
        self.interval = max(1, total_generations // total_budget)
        self.t = 0
        self.calls_made = 0

    def should_invoke(self) -> bool:
        self.t += 1
        if self.t % self.interval == 0 and self.calls_made < self.total_budget:
            self.calls_made += 1
            return True
        return False

    def get_stats(self) -> dict:
        return {
            "total_budget": self.total_budget,
            "calls_made": self.calls_made,
            "interval": self.interval,
        }


class HeuristicDecayScheduler:
    """
    Heuristic scheduler from Liu et al. 2024 [5].
    w(t) = w0 * exp(-t/T)
    Call LLM if random() < w(t) AND budget remaining.
    """

    def __init__(self, total_budget: int, w0: float = 0.5, T: float = 100):
        self.total_budget = total_budget
        self.w0 = w0
        self.T = T
        self.t = 0
        self.calls_made = 0

    def should_invoke(self) -> bool:
        self.t += 1
        w_t = self.w0 * np.exp(-self.t / self.T)
        if np.random.rand() < w_t and self.calls_made < self.total_budget:
            self.calls_made += 1
            return True
        return False

    def get_stats(self) -> dict:
        return {
            "total_budget": self.total_budget,
            "calls_made": self.calls_made,
        }
