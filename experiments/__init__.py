"""
Experiments package.

Run scripts and plot scripts that drive the reproduction. Each module is a
standalone CLI tool: it reads its hyperparameters from a `config` block at the
top of the file, runs the experiment, and writes a JSON file to
`results/raw/` (run scripts) or a PDF + PNG pair to `results/figures/`
(plot scripts).

The `bash run_all.sh` script at the repository root chains the run_*.py
modules in this package to reproduce every table and figure in the paper.
"""
