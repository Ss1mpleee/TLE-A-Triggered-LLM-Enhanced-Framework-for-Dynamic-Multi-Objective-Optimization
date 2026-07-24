"""
Proposed method entry point.

`proposed.run_tle` is the single-file CLI that wires together the DE/NSGA-II
base engine and the three TLE modules (triple-signal trigger, dual-channel
LLM-to-EA mapping, UCB1 bandit scheduler) for end-to-end use without going
through the experiment-driver scripts in `experiments/`.

Typical use:

    python -m proposed.run_tle --problem DF1 --n_seeds 8 --llm qwen2.5:7b

See `python -m proposed.run_tle --help` for all options.

Note: we deliberately do NOT eagerly `from .run_tle import main` here, to
avoid a `RuntimeWarning` from `runpy` when this package is invoked as
`python -m proposed.run_tle` (which re-imports the module).
"""

