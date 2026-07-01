import sys
sys.path.insert(0, r'D:\新论文\实验')
from experiments.run_v3_seeds import make_algo, PROBS, NEW_SEEDS
import numpy as np
from core import LLMClient, DEFAULT_MODEL
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort
import time

seed = 5
prob = 'DF5'
llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
algo_obj = make_algo('TLE', llm, seed)
problem = DMOProblem(name=prob, d=10, nt=10, taut=10)
algo_obj.bounds = (problem.lower, problem.upper)
ref_pf = get_reference_pf(prob, n=100)


def evaluate(pop):
    return problem.evaluate(pop)


t0 = time.time()
pop, fit, info = algo_obj.optimize(evaluate, problem=problem)
elapsed = time.time() - t0
fronts = fast_non_dominated_sort(fit)
nd = fit[fronts[0]] if fronts else fit
igd = compute_igd(nd, ref_pf)
inv = info['invocations']
print(f'TLE DF5 seed={seed}: IGD={igd:.4f} t={elapsed:.1f}s inv={inv}', flush=True)