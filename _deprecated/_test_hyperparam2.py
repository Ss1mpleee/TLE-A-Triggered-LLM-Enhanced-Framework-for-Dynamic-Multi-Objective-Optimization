import sys
sys.path.insert(0, r'D:\新论文\实验')
import time
import numpy as np
from core import LLMClient, TLE, DEFAULT_MODEL
from core.moo_utils import compute_igd, fast_non_dominated_sort
from benchmarks import DMOProblem, get_reference_pf

PROB = 'DF5'
problem = DMOProblem(name=PROB, d=10, nt=10, taut=10)
ref_pf = get_reference_pf(PROB, n=100)
bounds = (problem.lower, problem.upper)


def evaluate(pop):
    return problem.evaluate(pop)


llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)

# Run 3 seeds x 1 hyperparam setting
for F in [0.3, 0.5, 0.7]:
    for seed in [0]:
        np.random.seed(seed)
        algo = TLE(d=10, bounds=bounds, n_obj=problem.M, pop_size=50, max_gen=200, llm=llm,
                   trigger='triple', scheduler='bandit', seed=seed)
        algo.F = F
        algo.CR = 0.9
        algo.scheduler.cost_per_call = 0.05
        t0 = time.time()
        pop, fit, info = algo.optimize(evaluate, problem=problem)
        fronts = fast_non_dominated_sort(fit)
        nd = fit[fronts[0]] if fronts else fit
        igd = float(compute_igd(nd, ref_pf))
        inv = info['invocations']
        elapsed = time.time() - t0
        print(f'F={F} seed={seed} IGD={igd:.4f} inv={inv} t={elapsed:.1f}s', flush=True)
print('DONE', flush=True)
