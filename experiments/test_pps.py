import sys
sys.path.insert(0, "D:/新论文/实验")
import numpy as np
from baselines.pps_dmoea import PPSDEBaseline
from benchmarks import DMOProblem

problem = DMOProblem(name='DF1', d=10, nt=10, taut=10)
algo = PPSDEBaseline(d=10, bounds=(problem.lower, problem.upper), n_obj=2,
                     pop_size=30, max_gen=50, seed=0)
def ev(pop): return problem.evaluate(pop)
pop, fit, info = algo.optimize(ev, problem=problem)
print(f'PPS-DE: best fitness = {min(np.sum(fit, axis=1)):.4f}')
print(f'Final history: {info["best_fitness_history"][-3:]}')
