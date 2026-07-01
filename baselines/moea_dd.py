"""MOEA/DD-like baseline: a simplified MOEA/DD for DMO.

We implement a streamlined version of Li & Zhang (2015) MOEA/DD
adapted for DMO.  The key idea: decompose the multi-objective
problem into $K$ sub-problems via uniform random weight vectors,
each sub-problem optimised by a DE/DE/rand/1/bin step (sharing
individuals across neighbouring sub-problems).

Reference:
    Li, H., & Zhang, Q. (2015). Multiobjective optimization problems
    with complicated Pareto sets, MOEA/D and NSGA-II. IEEE Trans. Evol.
    Comput., 13(2), 284-302.
"""
import numpy as np
from core.moo_utils import fast_non_dominated_sort, compute_igd


class MOEADD:
    """A simplified MOEA/DD-like baseline for DMO.

    Differences from full MOEA/DD:
        - Uses uniform random weights instead of simplex-lattice (faster init)
        - DE/rand/1/bin mutation instead of polynomial (consistent with TLE)
        - No dominance-based decomposition enhancement (simpler)
    """
    def __init__(self, d, bounds, n_obj, pop_size=50, max_gen=200,
                 F=0.5, CR=0.9, n_neigh=10, seed=0):
        self.d = d
        self.bounds = bounds
        self.n_obj = n_obj
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.F = F
        self.CR = CR
        self.n_neigh = min(n_neigh, pop_size - 1)
        self.seed = seed
        np.random.seed(seed)

    def _init_weights(self, K):
        """Uniform random weight vectors on the (n_obj-1)-simplex."""
        w = np.random.exponential(1.0, (K, self.n_obj))
        return w / w.sum(axis=1, keepdims=True)

    def _tchebycheff(self, fit, w, z_star):
        """Tchebycheff scalarisation (smaller = better)."""
        # z_star is the ideal point (per-objective best)
        diff = np.abs(fit - z_star)
        return np.max(w * diff, axis=1)

    def _de_step(self, pop, fit, neighbours, B, ref_v):
        """Generate trial vector for sub-problem B using neighbour B_i."""
        trials = pop.copy()
        N = pop.shape[0]
        for i in range(N):
            # Pick 3 random neighbours (including itself) of i
            cand = neighbours[i]
            if len(cand) < 3:
                r1, r2, r3 = np.random.choice(N, 3, replace=False)
            else:
                r1, r2, r3 = np.random.choice(cand, 3, replace=False)
            j_rand = np.random.randint(self.d)
            cr_v = np.random.rand(self.d) < self.CR
            v = pop[r1] + self.F * (pop[r2] - pop[r3])
            mask = cr_v | (np.arange(self.d) == j_rand)
            trials[i] = np.where(mask, v, pop[i])
        return trials

    def optimize(self, evaluate_fn, problem=None, on_change_fn=None):
        lo, hi = self.bounds
        pop = lo + (hi - lo) * np.random.rand(self.pop_size, self.d)
        fit = evaluate_fn(pop)
        # Initial weight vectors
        weights = self._init_weights(self.pop_size)
        # Compute neighbours in weight space (top-T closest)
        from scipy.spatial.distance import cdist
        W_dist = cdist(weights, weights, metric='euclidean')
        neighbours = np.argsort(W_dist, axis=1)[:, :self.n_neigh + 1]
        # Ideal point
        z_star = fit.min(axis=0)

        for gen in range(self.max_gen):
            # === On environmental change: re-evaluate pop ===
            if problem is not None and problem.is_change_step(gen):
                fit = evaluate_fn(pop)
                z_star = fit.min(axis=0)
                if on_change_fn is not None:
                    on_change_fn(gen, 1.0)

            # === DE step on neighbours ===
            trial_pop = self._de_step(pop, fit, neighbours, None, None)
            trial_fit = evaluate_fn(trial_pop)

            # === Update: keep trial if Tchebycheff is better ===
            for i in range(self.pop_size):
                if self._tchebycheff(trial_fit[i:i+1], weights[i:i+1], z_star)[0] \
                        <= self._tchebycheff(fit[i:i+1], weights[i:i+1], z_star)[0]:
                    pop[i] = trial_pop[i]
                    fit[i] = trial_fit[i]

            # Update ideal
            z_star = np.minimum(z_star, fit.min(axis=0))

            if problem is not None and hasattr(problem, 'step'):
                problem.step()

        info = {
            'invocations': 0,  # no LLM
            'total_gens': self.max_gen,
            'invocation_rate': 0.0,
        }
        return pop, fit, info
