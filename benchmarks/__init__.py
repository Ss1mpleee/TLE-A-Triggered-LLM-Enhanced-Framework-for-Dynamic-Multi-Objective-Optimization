"""
__init__.py for benchmarks
"""
from .cec2018 import DMOProblem, get_reference_pf
from .uav_scenario import (
    ScenarioConfig, generate_scenario, UAVSimulator,
    evaluate_uav_solution, decode_chromosome_to_assignment,
    Task, UAV
)
