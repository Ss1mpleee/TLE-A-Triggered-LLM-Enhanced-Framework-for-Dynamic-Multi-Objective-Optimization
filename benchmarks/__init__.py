"""
Benchmark problems package.

Exposes the dynamic multi-objective problems used in the paper:
- `DMOProblem`: a wrapper that advances time and reports change events.
- `get_reference_pf`: the reference Pareto fronts used for IGD / HV.
- `df1` ... `df10`: the raw problem functions (used internally).
- The dynamic multi-UAV scenario (`ScenarioConfig`, `generate_scenario`,
  `UAVSimulator`, `evaluate_uav_solution`, ...).

The CEC 2018 DF1-DF5 / DF7 set is the main benchmark. DF10 is included for
the 3-objective ablation; DF4, DF6, and DF8-DF14 are not bundled.
"""
from .cec2018 import (
    DMOProblem,
    df1, df2, df3, df5, df7, df10,
    get_reference_pf,
    reference_pf_2obj,
    reference_pf_3obj,
)
from .uav_scenario import (
    ScenarioConfig,
    Task,
    UAV,
    UAVSimulator,
    generate_scenario,
    evaluate_uav_solution,
    decode_chromosome_to_assignment,
)

__all__ = [
    "DMOProblem",
    "df1", "df2", "df3", "df5", "df7", "df10",
    "get_reference_pf",
    "reference_pf_2obj",
    "reference_pf_3obj",
    "ScenarioConfig", "Task", "UAV", "UAVSimulator",
    "generate_scenario", "evaluate_uav_solution",
    "decode_chromosome_to_assignment",
]
