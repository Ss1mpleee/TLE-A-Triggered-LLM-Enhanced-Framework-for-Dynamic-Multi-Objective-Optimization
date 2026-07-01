"""
CEC 2018 Dynamic Multi-Objective Optimization Benchmark
======================================================
Simplified implementation of the CEC2018 DMO benchmark (DF1-DF14).
We use a subset of the standard test suite with 2 and 3 objectives.

Reference: IEEE CEC 2018 Competition on Dynamic Multiobjective Optimization
"""
import numpy as np
from typing import Tuple, Optional, Callable


def _sphere(x: np.ndarray) -> float:
    return float(np.sum(x ** 2))


def _rosenbrock(x: np.ndarray) -> float:
    n = len(x)
    if n < 2:
        return 0.0
    return float(np.sum(100 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2))


# ============ Base DF1: Sphere + time-varying ============
def df1(pop: np.ndarray, t: int = 0, nt: int = 10, taut: int = 10) -> np.ndarray:
    """
    DF1 (CEC2018): 2-objective
      f1 = (1 + g) * x1
      f2 = (1 + g) * (1 - sqrt(x1 / (1 + g))) where g is time-varying
    """
    n, d = pop.shape
    tau = t / max(1, nt)  # time ratio
    G = np.sin(0.5 * np.pi * tau)  # time-varying factor
    g = 1.0 + G * np.sum(pop[:, 1:] ** 2, axis=1) / (d - 1)
    f1 = g * pop[:, 0]
    f2 = g * (1 - np.sqrt(pop[:, 0] / np.maximum(g, 1e-12)))
    return np.column_stack([f1, f2])


def df2(pop: np.ndarray, t: int = 0, nt: int = 10, taut: int = 10) -> np.ndarray:
    """
    DF2: 2-objective, ZDT2-like with time-varying g
    """
    n, d = pop.shape
    tau = t / max(1, nt)
    G = np.sin(0.5 * np.pi * tau)
    g = 1.0 + G * np.sum(pop[:, 1:] ** 2, axis=1) / (d - 1)
    f1 = g * pop[:, 0]
    f2 = g * (1 - (pop[:, 0] / np.maximum(g, 1e-12)) ** 2)
    return np.column_stack([f1, f2])


def df3(pop: np.ndarray, t: int = 0, nt: int = 10, taut: int = 10) -> np.ndarray:
    """
    DF3: 2-objective, rotated time-varying
    """
    n, d = pop.shape
    tau = t / max(1, nt)
    G = np.cos(0.5 * np.pi * tau)
    # Use rotation on first 2 variables
    rotated = pop.copy()
    if d >= 2:
        x0, x1 = pop[:, 0], pop[:, 1]
        rotated[:, 0] = x0 * np.cos(0.1 * tau) - x1 * np.sin(0.1 * tau)
        rotated[:, 1] = x0 * np.sin(0.1 * tau) + x1 * np.cos(0.1 * tau)
    g = 1.0 + G * np.sum(rotated[:, 1:] ** 2, axis=1) / (d - 1)
    # Clamp rotated[:, 0] to [0, g] to avoid sqrt of negative values
    # The reference PF assumes x1 ∈ [0, 1] (after scaling); rotation can push outside
    f1 = g * np.clip(rotated[:, 0], 0.0, 1.0)
    # For f2, use safe sqrt argument
    arg = np.clip(rotated[:, 0] / np.maximum(g, 1e-12), 0.0, 1.0)
    f2 = g * (1 - np.sqrt(arg))
    return np.column_stack([f1, f2])


def df5(pop: np.ndarray, t: int = 0, nt: int = 10, taut: int = 10) -> np.ndarray:
    """
    DF5: 2-objective with mixed convexity
    """
    n, d = pop.shape
    tau = t / max(1, nt)
    H = 1.25 - 0.5 * np.sin(0.5 * np.pi * tau)
    g = 1.0 + np.sum(pop[:, 1:] ** 2, axis=1) / (d - 1)
    f1 = g * pop[:, 0]
    f2 = g * (1 - (pop[:, 0] / np.maximum(g, 1e-12)) ** H)
    return np.column_stack([f1, f2])


def df7(pop: np.ndarray, t: int = 0, nt: int = 10, taut: int = 10) -> np.ndarray:
    """
    DF7: 2-objective, disconnected PF, time-varying
    """
    n, d = pop.shape
    tau = t / max(1, nt)
    G = np.sin(0.5 * np.pi * tau)
    g = 1.0 + G * np.sum(pop[:, 1:] ** 2, axis=1) / (d - 1)
    f1 = g * pop[:, 0]
    # Disconnected: shift the second part
    mask = pop[:, 0] > 0.5
    f2 = g * (1 - np.sqrt(pop[:, 0] / np.maximum(g, 1e-12)))
    f2[mask] = g[mask] * (1 - np.sqrt(pop[mask, 0] / np.maximum(g[mask], 1e-12))) * 0.7
    return np.column_stack([f1, f2])


def df10(pop: np.ndarray, t: int = 0, nt: int = 10, taut: int = 10) -> np.ndarray:
    """
    DF10: 3-objective, DTLZ1-like with time-varying g
    """
    n, d = pop.shape
    M = 3
    tau = t / max(1, nt)
    G = np.sin(0.5 * np.pi * tau)
    g = 1.0 + G * 100 * np.sum(
        (pop[:, M - 1:] - 0.5) ** 2 - np.cos(20 * np.pi * (pop[:, M - 1:] - 0.5)),
        axis=1
    ) / (d - M + 1)
    f = np.zeros((n, M))
    for m in range(M):
        f[:, m] = (1 + g)
        for j in range(M - m - 1):
            f[:, m] *= pop[:, j]
        if m > 0:
            f[:, m] *= (1 - pop[:, M - m - 1])
    return f


# ============ Dynamic wrapper ============
class DMOProblem:
    """
    Wrapper for dynamic multi-objective problems.
    Handles time-varying parameters and change detection.
    """

    def __init__(
        self,
        name: str = "DF1",
        d: int = 10,
        nt: int = 10,
        taut: int = 10,
        lower: float = 0.0,
        upper: float = 1.0,
    ):
        self.name = name
        self.d = d
        self.nt = nt
        self.taut = taut
        self.lower = np.full(d, lower)
        self.upper = np.full(d, upper)
        self.t = 0  # current time step
        self.change_steps = []  # generations where change happened

        # Select function
        func_map = {
            "DF1": df1, "DF2": df2, "DF3": df3,
            "DF5": df5, "DF7": df7, "DF10": df10,
        }
        if name not in func_map:
            raise ValueError(f"Unknown DMO function: {name}")
        self._func = func_map[name]

    @property
    def M(self) -> int:
        """Number of objectives (2 or 3)."""
        if self.name.startswith("DF10") or self.name.startswith("DF11"):
            return 3
        return 2

    def evaluate(self, pop: np.ndarray) -> np.ndarray:
        """Evaluate population at current time t."""
        return self._func(pop, self.t, self.nt, self.taut)

    def step(self):
        """Advance to next time step."""
        self.t += 1
        # A change occurs at every `taut` step (simplified)
        if self.t > 0 and self.t % self.taut == 0:
            self.change_steps.append(self.t)

    def is_change_step(self, generation: int) -> bool:
        """Whether a change happens at this generation."""
        return generation in self.change_steps

    def detect_change(self, prev_fit: np.ndarray, curr_fit: np.ndarray) -> float:
        """
        Compute change magnitude between two consecutive fitness snapshots.
        Returns a scalar [0, 1+].
        """
        if prev_fit is None or curr_fit is None:
            return 0.0
        if prev_fit.shape != curr_fit.shape:
            return 0.0
        # Normalize by range
        diff = np.abs(curr_fit - prev_fit)
        if diff.size == 0:
            return 0.0
        # Relative change
        denom = np.abs(prev_fit) + 1e-6
        rel_change = np.mean(diff / denom)
        return float(rel_change)


# ============ Reference PF generators ============
def reference_pf_2obj(name: str, n: int = 100) -> np.ndarray:
    """Generate reference Pareto front for 2-objective DMO."""
    x = np.linspace(0, 1, n)
    if name in ("DF1", "DF3", "DF7"):
        f1 = x
        f2 = 1 - np.sqrt(x)
    elif name == "DF2":
        f1 = x
        f2 = 1 - x ** 2
    elif name == "DF5":
        f1 = x
        f2 = 1 - x ** 1.25  # approximate
    else:
        f1 = x
        f2 = 1 - np.sqrt(x)
    return np.column_stack([f1, f2])


def reference_pf_3obj(name: str, n: int = 100) -> np.ndarray:
    """Generate reference PF for 3-objective DMO (DF10)."""
    if name == "DF10":
        x1 = np.linspace(0, 1, n)
        x2 = np.linspace(0, 1, n)
        f1 = x1 * x2
        f2 = x1 * (1 - x2)
        f3 = 1 - x1
        return np.column_stack([f1, f2, f3])
    return np.zeros((n, 3))


def get_reference_pf(name: str, n: int = 100) -> np.ndarray:
    M = 3 if name.startswith("DF10") else 2
    if M == 3:
        return reference_pf_3obj(name, n)
    return reference_pf_2obj(name, n)


# ============ Quick test ============
if __name__ == "__main__":
    for fname in ["DF1", "DF2", "DF5", "DF7", "DF10"]:
        prob = DMOProblem(name=fname, d=10, nt=10, taut=10)
        np.random.seed(42)
        pop = np.random.uniform(0, 1, (20, 10))
        fit = prob.evaluate(pop)
        ref = get_reference_pf(fname, 100)
        print(f"{fname}: pop shape={pop.shape}, fit shape={fit.shape}, "
              f"ref shape={ref.shape}, M={prob.M}")
        print(f"  fit range: [{fit.min():.3f}, {fit.max():.3f}]")
