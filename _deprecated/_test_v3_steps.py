import sys
sys.path.insert(0, r'D:\新论文\实验')
import time
import numpy as np
from core import LLMClient, TLE, DEFAULT_MODEL
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort

print('Step 1: setup', flush=True)
t = time.time()
llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
problem = DMOProblem(name='DF5', d=10, nt=10, taut=10)
ref_pf = get_reference_pf('DF5', n=100)
print(f'  setup done in {time.time()-t:.2f}s', flush=True)


def evaluate(pop):
    return problem.evaluate(pop)


print('Step 2: create TLE', flush=True)
t = time.time()
algo = TLE(d=10, bounds=(problem.lower, problem.upper), n_obj=2,
           pop_size=50, max_gen=200, llm=llm,
           trigger='triple', scheduler='bandit', seed=5)
print(f'  TLE created in {time.time()-t:.2f}s', flush=True)

print('Step 3: optimize', flush=True)
t = time.time()
np.random.seed(5)
pop, fit, info = algo.optimize(evaluate, problem=problem)
print(f'  optimize done in {time.time()-t:.2f}s, invocations={info["invocations"]}', flush=True)

print('Step 4: IGD', flush=True)
fronts = fast_non_dominated_sort(fit)
nd = fit[fronts[0]] if fronts else fit
igd = float(compute_igd(nd, ref_pf))
print(f'  IGD = {igd:.4f}', flush=True)
print('DONE', flush=True)