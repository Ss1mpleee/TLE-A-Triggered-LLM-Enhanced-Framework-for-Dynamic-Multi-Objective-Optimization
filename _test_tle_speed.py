import sys
sys.path.insert(0, r'D:\新论文\实验')
import time
import numpy as np
from core import LLMClient, TLE, DEFAULT_MODEL
from core.moo_utils import compute_igd, fast_non_dominated_sort
from benchmarks import DMOProblem, get_reference_pf

t0 = time.time()
np.random.seed(0)
prob = 'DF5'
problem = DMOProblem(name=prob, d=10, nt=10, taut=10)
ref_pf = get_reference_pf(prob, n=100)
bounds = (problem.lower, problem.upper)


def evaluate(pop):
    return problem.evaluate(pop)


llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
llm.reset_stats()
print(f'Start; cache initial = {llm.stats() if hasattr(llm, "stats") else "?"}')

algo = TLE(
    d=10, bounds=bounds, n_obj=problem.M,
    pop_size=50, max_gen=200, llm=llm,
    trigger='triple', scheduler='bandit', seed=0,
)
print(f'Before optimize; t={time.time()-t0:.1f}s')
pop, fit, info = algo.optimize(evaluate, problem=problem)
print(f'After optimize; t={time.time()-t0:.1f}s')
print(f'Invocations: {info["invocations"]}')
print(f'LLM stats: {info.get("llm_stats")}')
