import sys
sys.path.insert(0, "D:/新论文/实验")
import numpy as np
from baselines.pps_dmoea import PPSDEBaseline
from benchmarks import DMOProblem

problem = DMOProblem(name='DF1', d=10, nt=10, taut=10)
algo = PPSDEBaseline(d=10, bounds=(problem.lower, problem.upper), n_obj=2,
                     pop_size=30, max_gen=30, seed=0)

# Manually check change detection
problem.t = 0
print("Change steps:", problem.change_steps)

# Run a few generations
def ev(pop): return problem.evaluate(pop)
pop = np.random.uniform(0, 1, (30, 10))
fit = ev(pop)
print(f"Gen 0: fit[0,0]={fit[0,0]:.4f}, algo.curr_center={algo.curr_center}")

for gen in range(15):
    if problem.is_change_step(gen):
        print(f"  -> Gen {gen}: CHANGE detected (taut)")
    if algo._detect_change(fit if gen == 0 else None, fit):
        print(f"  -> Gen {gen}: CHANGE detected (statistical)")
    algo.change_detected = False
    problem.step()
    trial = np.random.uniform(0, 1, (30, 10))
    trial_fit = ev(trial)
    fit = trial_fit
