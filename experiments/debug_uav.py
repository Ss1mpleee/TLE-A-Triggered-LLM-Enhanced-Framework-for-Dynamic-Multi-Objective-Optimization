import sys
sys.path.insert(0, "D:/新论文/实验")
import numpy as np
from benchmarks import ScenarioConfig, generate_scenario, evaluate_uav_solution, decode_chromosome_to_assignment

cfg = ScenarioConfig(n_uavs=4, simulation_time=300.0, task_arrival_rate=0.3, seed=0)
scenario = generate_scenario(cfg)
print(f'Tasks: {len(scenario["tasks"])}, Events: {len(scenario["events"])}')

# Build random chromosome
n_uavs = cfg.n_uavs
n_tasks = len(scenario['tasks'])
D = n_uavs * n_tasks
chrom = np.random.uniform(0, 1, D)
assignment = decode_chromosome_to_assignment(chrom, n_uavs, n_tasks)
print(f'Assignment shape: {assignment.shape}')
print(f'Total assignments: {assignment.sum()}')
print(f'Per-UAV assignments: {assignment.sum(axis=1)}')

# Run eval
obj = evaluate_uav_solution(chrom, scenario)
print(f'Objectives: {obj}')
print(f'  - Task value completed: {-obj[0]:.1f}')
print(f'  - Avg response time: {-obj[1]:.1f}s')
print(f'  - Avg remaining battery: {-obj[2]:.1f}%')

# Check completed tasks
sim_tasks_assigned = sum(1 for t in scenario['tasks'] if t.assigned_uav is not None)
print(f'Tasks assigned: {sim_tasks_assigned}/{len(scenario["tasks"])}')
