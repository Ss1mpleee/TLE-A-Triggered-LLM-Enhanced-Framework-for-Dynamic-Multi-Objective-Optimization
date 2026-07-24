"""Minimal hyperparameter sweep test - just verify it works."""
import sys
sys.path.insert(0, r'D:\新论文\实验')
import time
import numpy as np
from core import LLMClient, TLE, DEFAULT_MODEL
from core.moo_utils import compute_igd, fast_non_dominated_sort
from benchmarks import DMOProblem, get_reference_pf

print('test 1: F=0.5, CR=0.9, lambda=0.05 (default)', flush=True)
t0 = time.time()
np.random.seed(0)
prob = 'DF5'
problem = DMOProblem(name=prob, d=10, nt=10, taut=10)
ref_pf = get_reference_pf(prob, n=100)
bounds = (problem.lower, problem.upper)


def evaluate(pop):
    return problem.evaluate(pop)


llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
algo = TLE(
    d=10, bounds=bounds, n_obj=problem.M,
    pop_size=50, max_gen=200, llm=llm,
    trigger='triple', scheduler='bandit', seed=0,
)
print(f'  algo.F={algo.F}, algo.CR={algo.CR}', flush=True)
print(f'  has scheduler: {hasattr(algo, "scheduler")}', flush=True)
print(f'  scheduler type: {type(algo.scheduler).__name__}', flush=True)
print(f'  scheduler.cost_per_call: {algo.scheduler.cost_per_call}', flush=True)

# Don't override, just run default
pop, fit, info = algo.optimize(evaluate, problem=problem)
fronts = fast_non_dominated_sort(fit)
nd = fit[fronts[0]] if fronts else fit
igd = float(compute_igd(nd, ref_pf))
print(f'  IGD={igd:.4f}, inv={info["invocations"]}, t={time.time()-t0:.1f}s', flush=True)

print('\ntest 2: F=0.3 (override)', flush=True)
t1 = time.time()
np.random.seed(0)
algo2 = TLE(
    d=10, bounds=bounds, n_obj=problem.M,
    pop_size=50, max_gen=200, llm=LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True),
    trigger='triple', scheduler='bandit', seed=0,
)
algo2.F = 0.3
print(f'  algo2.F={algo2.F}', flush=True)
pop, fit, info = algo2.optimize(evaluate, problem=problem)
fronts = fast_non_dominated_sort(fit)
nd = fit[fronts[0]] if fronts else fit
igd = float(compute_igd(nd, ref_pf))
print(f'  IGD={igd:.4f}, inv={info["invocations"]}, t={time.time()-t1:.1f}s', flush=True)
