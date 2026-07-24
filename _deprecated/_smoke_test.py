import sys
sys.path.insert(0, r'D:\新论文\实验')
from core import TLE, DEBaseline, PPSDMOEA, LLMClient
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort
import numpy as np
import time

# PPS quick test on DF5
np.random.seed(0)
t0 = time.time()
prob = DMOProblem('DF5', d=10, nt=10, taut=10)
ref = get_reference_pf('DF5', 100)
pps = PPSDMOEA(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M, pop_size=50, max_gen=20, seed=0)
pop, fit, info = pps.optimize(lambda p: prob.evaluate(p), problem=prob)
fronts = fast_non_dominated_sort(fit)
nd_fit = fit[fronts[0]]
igd = compute_igd(nd_fit, ref)
print(f'PPS smoke: DF5 20gen seed=0 -> IGD={igd:.4f}, elapsed={time.time()-t0:.2f}s')

# PPS on DF2
np.random.seed(0)
t0 = time.time()
prob2 = DMOProblem('DF2', d=10, nt=10, taut=10)
ref2 = get_reference_pf('DF2', 100)
pps2 = PPSDMOEA(d=10, bounds=(prob2.lower, prob2.upper), n_obj=prob2.M, pop_size=50, max_gen=20, seed=0)
pop2, fit2, info2 = pps2.optimize(lambda p: prob2.evaluate(p), problem=prob2)
fronts2 = fast_non_dominated_sort(fit2)
nd_fit2 = fit2[fronts2[0]]
igd2 = compute_igd(nd_fit2, ref2)
print(f'PPS smoke: DF2 20gen seed=0 -> IGD={igd2:.4f}, elapsed={time.time()-t0:.2f}s')

# TLE smoke
llm = LLMClient(model='qwen2.5:7b', use_cache=True)
np.random.seed(0)
t0 = time.time()
tle = TLE(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M, pop_size=50, max_gen=20, llm=llm, trigger='triple', scheduler='bandit', seed=0)
pop3, fit3, info3 = tle.optimize(lambda p: prob.evaluate(p), problem=prob)
fronts3 = fast_non_dominated_sort(fit3)
nd_fit3 = fit3[fronts3[0]]
igd3 = compute_igd(nd_fit3, ref)
print(f'TLE smoke: DF5 20gen seed=0 -> IGD={igd3:.4f}, invocations={info3["invocations"]}, elapsed={time.time()-t0:.2f}s')
print('All smoke tests passed')
