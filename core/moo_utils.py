"""
Multi-Objective Utilities: NSGA-II / NSGA-III non-dominated sorting
==================================================================
Minimal implementations for our TLE framework.
"""
import numpy as np
from typing import List, Tuple


def fast_non_dominated_sort(fitness: np.ndarray) -> List[List[int]]:
    """
    NSGA-II fast non-dominated sort.
    fitness: shape (N, M)
    Returns: list of fronts, each is list of indices.
    """
    N = fitness.shape[0]
    domination_count = np.zeros(N, dtype=int)
    dominated_set = [[] for _ in range(N)]
    fronts = [[]]

    for p in range(N):
        for q in range(N):
            if p == q:
                continue
            if dominates(fitness[p], fitness[q]):
                dominated_set[p].append(q)
            elif dominates(fitness[q], fitness[p]):
                domination_count[p] += 1
        if domination_count[p] == 0:
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in dominated_set[p]:
                domination_count[q] -= 1
                if domination_count[q] == 0:
                    next_front.append(q)
        i += 1
        fronts.append(next_front)
    fronts.pop()  # remove last empty
    return fronts


def dominates(a: np.ndarray, b: np.ndarray) -> bool:
    """a dominates b iff a <= b on all and a < b on at least one."""
    return np.all(a <= b) and np.any(a < b)


def crowding_distance(fitness: np.ndarray, front: List[int]) -> np.ndarray:
    """
    NSGA-II crowding distance.
    Returns: distances of same length as front.
    """
    n = len(front)
    if n == 0:
        return np.array([])
    if n <= 2:
        return np.full(n, np.inf)

    distances = np.zeros(n)
    front_fit = fitness[front]
    M = front_fit.shape[1]

    for m in range(M):
        sorted_idx = np.argsort(front_fit[:, m])
        distances[sorted_idx[0]] = np.inf
        distances[sorted_idx[-1]] = np.inf
        m_range = front_fit[sorted_idx[-1], m] - front_fit[sorted_idx[0], m]
        if m_range < 1e-12:
            continue
        for i in range(1, n - 1):
            distances[sorted_idx[i]] += (
                (front_fit[sorted_idx[i + 1], m] - front_fit[sorted_idx[i - 1], m])
                / m_range
            )
    return distances


def nsga2_select(population: np.ndarray, fitness: np.ndarray, n_select: int):
    """
    NSGA-II environmental selection.
    Returns: selected indices, sorted by (front, -crowding_distance).
    """
    fronts = fast_non_dominated_sort(fitness)
    selected = []
    for front in fronts:
        if len(selected) + len(front) <= n_select:
            selected.extend(front)
        else:
            cd = crowding_distance(fitness, front)
            sorted_in_front = np.array(front)[np.argsort(-cd)]
            remaining = n_select - len(selected)
            selected.extend(sorted_in_front[:remaining].tolist())
            break
    return selected


def compute_igd(obtained: np.ndarray, reference: np.ndarray) -> float:
    """
    Inverted Generational Distance.
    obtained: shape (N, M)
    reference: shape (N_ref, M) — ideally uniformly distributed on true PF
    """
    if obtained.size == 0 or reference.size == 0:
        return float("inf")
    # Drop NaN / Inf rows
    obtained = obtained[np.all(np.isfinite(obtained), axis=1)]
    if obtained.size == 0:
        return float("inf")
    dists = np.min(np.linalg.norm(
        reference[:, None, :] - obtained[None, :, :], axis=2), axis=1)
    return float(np.mean(dists))


def compute_hv(obtained: np.ndarray, ref_point: np.ndarray) -> float:
    """
    Hypervolume indicator (2D / 3D only, exact via inclusion-exclusion).
    """
    M = obtained.shape[1]
    # Filter dominated by ref_point
    mask = np.all(obtained < ref_point, axis=1)
    pts = obtained[mask]
    if pts.size == 0:
        return 0.0
    if M == 2:
        return _hv_2d(pts, ref_point)
    elif M == 3:
        return _hv_3d(pts, ref_point)
    else:
        # Fallback: Monte Carlo
        return _hv_monte_carlo(pts, ref_point)


def _hv_2d(points: np.ndarray, ref: np.ndarray) -> float:
    pts = points[np.argsort(points[:, 0])]
    hv = 0.0
    prev_x = 0.0
    for p in pts:
        hv += (p[0] - prev_x) * (ref[1] - p[1])
        prev_x = p[0]
    return hv


def _hv_3d(points: np.ndarray, ref: np.ndarray) -> float:
    """3D HV using sweep line."""
    # Sort by first dimension
    pts = points[np.argsort(points[:, 0])]
    hv = 0.0
    for i, p in enumerate(pts):
        if i == 0:
            slab = (p[0], ref[0])
        else:
            slab = (p[0], pts[i - 1][0])
        # In slab, 2D HV
        slab_pts = pts[pts[:, 0] >= slab[0]]
        slab_2d = slab_pts[:, 1:]
        hv += (slab[0] - slab[1]) * _hv_2d(slab_2d, ref[1:])
    return abs(hv)


def _hv_monte_carlo(points: np.ndarray, ref: np.ndarray, n_samples: int = 100000) -> float:
    """Fallback for M > 3."""
    M = points.shape[1]
    samples = np.random.uniform(
        low=np.zeros(M),
        high=ref,
        size=(n_samples, M)
    )
    # dominated by any point in obtained
    dominated = np.zeros(n_samples, dtype=bool)
    for p in points:
        dominated |= np.all(samples >= p, axis=1)
    box_vol = np.prod(ref)
    return box_vol * np.sum(dominated) / n_samples
