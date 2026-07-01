"""
Differential Evolution Core Operators
====================================
Standard DE/rand/1/bin and variants.

Reference: Storn & Price, "Differential Evolution—A Simple and Efficient
Heuristic for Global Optimization over Continuous Spaces", 1997.
"""
import numpy as np
from typing import Tuple, Optional


def _scalar_fitness(fitness: np.ndarray) -> np.ndarray:
    """
    Convert 2D multi-objective fitness to 1D scalar via sum of objectives
    (or just return if already 1D).
    """
    if fitness.ndim == 1:
        return fitness
    return np.sum(fitness, axis=1)


def de_rand_1_bin(
    population: np.ndarray,
    fitness: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
    F: float = 0.5,
    CR: float = 0.9,
) -> np.ndarray:
    """
    DE/rand/1/bin: classic differential evolution.

    Args:
        population: shape (NP, D)
        fitness: shape (NP,) or (NP, M)
        bounds: (lower, upper) each shape (D,)
        F: scaling factor
        CR: crossover rate

    Returns:
        trial: shape (NP, D)
    """
    NP, D = population.shape
    lower, upper = bounds
    trial = np.empty_like(population)
    fit_scalar = _scalar_fitness(fitness)

    for i in range(NP):
        # Choose 3 distinct individuals != i
        candidates = [j for j in range(NP) if j != i]
        r1, r2, r3 = np.random.choice(candidates, 3, replace=False)

        # Mutation
        mutant = population[r1] + F * (population[r2] - population[r3])
        mutant = np.clip(mutant, lower, upper)

        # Binomial crossover
        cross_mask = np.random.rand(D) < CR
        # Ensure at least one dimension from mutant
        if not cross_mask.any():
            cross_mask[np.random.randint(D)] = True
        trial[i] = np.where(cross_mask, mutant, population[i])

    return trial


def de_best_1_bin(
    population: np.ndarray,
    fitness: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
    F: float = 0.5,
    CR: float = 0.9,
) -> np.ndarray:
    """DE/best/1/bin: use the best individual as base."""
    NP, D = population.shape
    lower, upper = bounds
    trial = np.empty_like(population)
    fit_scalar = _scalar_fitness(fitness)
    best_idx = int(np.argmin(fit_scalar))

    for i in range(NP):
        candidates = [j for j in range(NP) if j != i and j != best_idx]
        if len(candidates) < 2:
            candidates = [j for j in range(NP) if j != i]
        r1, r2 = np.random.choice(candidates, 2, replace=False)

        mutant = population[best_idx] + F * (population[r1] - population[r2])
        mutant = np.clip(mutant, lower, upper)

        cross_mask = np.random.rand(D) < CR
        if not cross_mask.any():
            cross_mask[np.random.randint(D)] = True
        trial[i] = np.where(cross_mask, mutant, population[i])

    return trial


def de_current_to_best_1_bin(
    population: np.ndarray,
    fitness: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
    F: float = 0.5,
    CR: float = 0.9,
) -> np.ndarray:
    """DE/current-to-best/1/bin: biased toward best."""
    NP, D = population.shape
    lower, upper = bounds
    trial = np.empty_like(population)
    fit_scalar = _scalar_fitness(fitness)
    best_idx = int(np.argmin(fit_scalar))

    for i in range(NP):
        candidates = [j for j in range(NP) if j != i and j != best_idx]
        if len(candidates) < 2:
            candidates = [j for j in range(NP) if j != i]
        r1, r2 = np.random.choice(candidates, 2, replace=False)

        mutant = (population[i]
                  + F * (population[best_idx] - population[i])
                  + F * (population[r1] - population[r2]))
        mutant = np.clip(mutant, lower, upper)

        cross_mask = np.random.rand(D) < CR
        if not cross_mask.any():
            cross_mask[np.random.randint(D)] = True
        trial[i] = np.where(cross_mask, mutant, population[i])

    return trial


def de_opposition(
    population: np.ndarray,
    fitness: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
    F: float = 0.5,
    CR: float = 0.9,
    strategy: str = "rand",
) -> np.ndarray:
    """
    Unified interface: select strategy by name.
    """
    if strategy == "rand":
        return de_rand_1_bin(population, fitness, bounds, F, CR)
    elif strategy == "best":
        return de_best_1_bin(population, fitness, bounds, F, CR)
    elif strategy == "current_to_best":
        return de_current_to_best_1_bin(population, fitness, bounds, F, CR)
    else:
        raise ValueError(f"Unknown DE strategy: {strategy}")


def jaya_update(
    population: np.ndarray,
    fitness: np.ndarray,
    bounds: Tuple[np.ndarray, np.ndarray],
) -> np.ndarray:
    """
    JAYA algorithm update: move toward best, away from worst.
    Reference: Rao, 2016.
    """
    NP, D = population.shape
    lower, upper = bounds
    new_pop = np.empty_like(population)

    best_idx = np.argmin(fitness)
    worst_idx = np.argmax(fitness)
    best = population[best_idx]
    worst = population[worst_idx]

    for i in range(NP):
        r1 = np.random.rand(D)
        r2 = np.random.rand(D)
        new_pop[i] = (population[i]
                      + r1 * (best - np.abs(population[i]))
                      - r2 * (worst - np.abs(population[i])))
    new_pop = np.clip(new_pop, lower, upper)
    return new_pop
