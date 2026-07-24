"""Verify that with step() now called, algorithms give different IGDs."""
import sys
sys.path.insert(0, r'D:\新论文\实验')
from core import DEBaseline, PPSDMOEA, DNSGAIIA, TLE, LLMClient
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort
import numpy as np

print('=== Smoke test: DE vs PPS vs DNSGA-II-A on DF5, 50 gen ===')

for algo_name, algo_cls in [('DE', DEBaseline), ('PPS-DMOEA', PPSDMOEA), ('DNSGA-II-A', DNSGAIIA)]:
    np.random.seed(0)
    prob = DMOProblem('DF5', d=10, nt=10, taut=10)
    ref = get_reference_pf('DF5', 100)
    algo = algo_cls(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M,
                    pop_size=50, max_gen=50, seed=0)
    pop, fit, info = algo.optimize(lambda p: prob.evaluate(p), problem=prob)
    fronts = fast_non_dominated_sort(fit)
    nd_fit = fit[fronts[0]]
    igd = compute_igd(nd_fit, ref)
    print(f'  {algo_name:12s}: IGD={igd:.4f}, '
          f'change_steps_in_problem={prob.change_steps[:10]}...')

# Also test TLE
print()
llm = LLMClient(model='qwen2.5:7b', use_cache=True)
np.random.seed(0)
prob = DMOProblem('DF5', d=10, nt=10, taut=10)
ref = get_reference_pf('DF5', 100)
tle = TLE(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M, pop_size=50,
          max_gen=50, llm=llm, trigger='triple', scheduler='bandit', seed=0)
pop, fit, info = tle.optimize(lambda p: prob.evaluate(p), problem=prob)
fronts = fast_non_dominated_sort(fit)
nd_fit = fit[fronts[0]]
igd = compute_igd(nd_fit, ref)
print(f'  TLE          : IGD={igd:.4f}, invocations={info["invocations"]}, '
      f'change_steps_in_problem={prob.change_steps[:10]}...')
print('All 4 algorithms should now show DIFFERENT IGDs and change_steps should be [10,20,30,40]')
