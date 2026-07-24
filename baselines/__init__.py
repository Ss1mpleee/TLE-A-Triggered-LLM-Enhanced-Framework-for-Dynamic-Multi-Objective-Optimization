"""
Baselines package.

Contains the comparison algorithms whose reference implementations are not part
of the shared DE/NSGA-II engine in `core.tle`. The `DE`, `NSGA-II`, `MOEA/D`,
`DNSGA-II-A`, `PPS-DMOEA`, and `TLE` itself live in `core.tle` and are re-exported
by `core.__init__`. The two baselines that have non-trivial, problem-specific
logic (population prediction in PPS-DMOEA, weight-vector decomposition in
MOEA/DD) live here.

Public API:
    from baselines import MOEADD, PPSDEBaseline
"""
from .moea_dd import MOEADD
from .pps_dmoea import PPSDEBaseline

__all__ = ["MOEADD", "PPSDEBaseline"]
