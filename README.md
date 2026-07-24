# TLE: Triggered LLM-Enhanced Evolutionary Algorithm

> An open-source Python implementation of the **TLE** framework for
> **dynamic multi-objective optimization (DMO)**, with a triple-signal trigger,
> a dual-channel LLM-to-EA mapping, and a UCB1 bandit-based LLM call budget
> scheduler. All experimental artifacts of the accompanying paper are
> reproducible from a single command.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)]()
[![Status](https://img.shields.io/badge/status-paper%20under%20review-yellow.svg)]()

---

## Table of contents

- [1. About the paper](#1-about-the-paper)
- [2. Highlights](#2-highlights)
- [3. Repository layout](#3-repository-layout)
- [4. Quick start](#4-quick-start)
- [5. Code architecture](#5-code-architecture)
- [6. Reproducing the experiments](#6-reproducing-the-experiments)
- [7. Hyperparameters](#7-hyperparameters)
- [8. Hardware requirements](#8-hardware-requirements)
- [9. Results directory layout](#9-results-directory-layout)
- [10. Figures: what is in the paper, what is supplementary](#10-figures-what-is-in-the-paper-what-is-supplementary)
- [11. License](#11-license)
- [12. Citation](#12-citation)
- [13. Contact](#13-contact)

---

## 1. About the paper

**Title:** *TLE: A Triggered LLM-Enhanced Framework for Dynamic
Multi-Objective Optimization --- An Empirical Study*

**Target journal:** *Swarm and Evolutionary Computation* (Elsevier, IF 8.5,
CAS Zone 1).

The paper proposes a unified framework that augments a classical
DE/rand/1/bin + NSGA-II search engine with three LLM-related modules:

1. A **triple-signal trigger** (population-entropy descent, fitness
   stagnation, environmental change) that decides when to invoke the LLM.
2. A **dual-channel LLM-to-EA mapping** that converts a natural-language
   recommendation into a strategic decision (operator mode, search focus) and
   a parametric adjustment (DE/CR scaling).
3. A **UCB1 bandit-based budget scheduler** that adaptively governs the LLM
   call rate, with a provable $O(\sqrt{T \log T})$ static-regret bound and an
   $\Omega(\sqrt{KT})$ dynamic-regret lower bound.

The framework is evaluated on the CEC 2018 DMO benchmark suite
(DF1--DF5, $n = 8$ seeds per problem) and on a dynamic multi-UAV
task-allocation scenario ($n = 5$ seeds, two fleet sizes, 200 generations
per configuration). A cross-LLM sensitivity analysis uses three locally
deployed open-source models: **Qwen-2.5-7B-Instruct**, **Qwen-3.5-9B-Instruct**,
and **OmniCoder-9B-Instruct**.

Two non-trivial findings are reported in the paper:

- On simpler DMO landscapes (DF1, DF2, DF7), TLE provides no measurable
  benefit over pure DE. TLE improves only on the more complex 8-UAV scenario
  (+16.8% cumulative task value, Wilcoxon $p = 0.018$).
- Under non-stationary rewards, the UCB1 scheduler is not the strongest
  component --- a simple time-decaying heuristic scheduler outperforms it on
  DF5, motivating non-stationary bandit extensions as future work.

---

## 2. Highlights

| Aspect | TLE |
|---|---|
| LLM invocation rate | **5--15% of generations** (vs.\ 100% for static-trigger baselines) |
| LLM-agnostic | any open-source model served via Ollama |
| Theoretical guarantees | static-regret $O(\sqrt{T \log T})$, dynamic-regret lower bound $\Omega(\sqrt{KT})$ |
| Hardware | a single RTX 4090, ~12 GPU-h for the 8-UAV scenario alone, ~90 GPU-h for a full reproduction |
| Code licence | MIT |

---

## 3. Repository layout

```
.
├── baselines/                # six comparison algorithms
│   ├── __init__.py
│   ├── moea_dd.py            # MOEA/DD-like (Zhang & Liu 2018)
│   └── pps_dmoea.py          # PPS-DMOEA (Zhou et al. 2014)
│
├── benchmarks/               # problem definitions
│   ├── __init__.py
│   ├── cec2018.py            # CEC 2018 DF1--DF5 dynamic multi-objective suite
│   └── uav_scenario.py       # dynamic multi-UAV task-allocation simulator
│
├── core/                     # TLE framework core
│   ├── __init__.py
│   ├── bandit.py             # UCB1 bandit + HeuristicDecayScheduler
│   ├── de_operators.py       # DE/rand/1/bin + polynomial mutation
│   ├── llm_interface.py      # Ollama client + persistent LLM response cache
│   ├── moo_utils.py          # non-dominated sort, crowding distance, IGD/HV
│   ├── prompts.py            # system + user prompt templates
│   ├── tle.py                # the TLE class (DE/NSGA-II + 3 TLE modules)
│   └── triggers.py           # triple-signal trigger
│
├── proposed/                 # TLE-specific glue + entry point (Algorithm 1)
│
├── experiments/              # run scripts and plot scripts
│   ├── run_main_cec2018.py   # 8-seed main comparison (DE, NSGA-II, MOEA/D, MOEA/DD, DNSGA-II-A, PPS-DMOEA, TLE)
│   ├── run_v3_seeds.py       # 75 extra runs for the final 8-seed main result
│   ├── run_sec_experiments.py# 5-seed ablation
│   ├── run_uav.py            # 5-seed UAV scenario
│   ├── run_cross_llm.py      # 2-seed cross-LLM sensitivity
│   ├── run_moeadd.py         # MOEA/DD baseline
│   ├── friedman_test.py      # Friedman test + Nemenyi critical-difference computation
│   ├── plot_tevc.py          # publication-quality IGD/HV/convergence plots
│   ├── plot_cross_llm.py     # cross-LLM diamond plots
│   ├── plot_extra.py         # Pareto-front, budget-comparison, LLM-call plots
│   ├── graphical_abstract.py # 5x5 cm graphical abstract for SWEVO submission
│   └── *.py                  # ~15 more analysis / debug scripts (legacy)
│
├── results/                  # all experimental output (mostly regenerable)
│   ├── raw/                  # small JSON result files (committed for reproducibility)
│   ├── figures/              # generated PNG/PDF (regenerated from raw + plot scripts)
│   └── llm_cache/            # per-prompt Ollama response cache (gitignored)
│
├── .gitignore                # Python / IDE / OS / large-binary exclusions
└── README.md                 # this file
```

**Note**: the `__init__.py` files in `baselines/`, `benchmarks/`, and
`core/` make the directory a proper Python package; you can `import
core.tle` from any subdirectory once `PYTHONPATH=.` is set.

---

## 4. Quick start

### 4.1 Prerequisites

| Tool | Tested version |
|---|---|
| Python | 3.10, 3.11, 3.12 |
| Ollama | 0.3.x (local LLM server) |
| CUDA-enabled GPU | NVIDIA RTX 3060 or better (8 GB VRAM minimum) |
| Disk | ~25 GB (model weights + raw results + cache) |

### 4.2 Install

```bash
# 1. Clone the repository
git clone https://github.com/[username]/TLE-DMO.git
cd TLE-DMO

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Ollama and pull the three LLMs
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
ollama pull qwen3.5:9b
ollama pull carstenuhlig/omnicoder-9b:q8_0

# 5. Verify
ollama list
python -c "import core.tle; print('TLE import OK')"
```

### 4.3 One-command full reproduction

```bash
# Optional: clean previous results
rm -rf results/raw/*

# Full reproduction (~90 GPU-h on RTX 4090)
bash run_all.sh

# OR: just the headline 8-seed main comparison (~25 GPU-h)
python -m experiments.run_main_cec2018 --n_seeds 8
```

`run_all.sh` re-executes, in order:

1. The 8-seed main comparison on DF1--DF5
2. The 5-seed ablation (V0--V3)
3. The 5-seed UAV comparison (4-UAV and 8-UAV)
4. The 2-seed cross-LLM analysis (3 models x 3 problems)
5. All plot regeneration (including the graphical abstract)

The total wall time is dominated by LLM inference. If you only have CPU
hardware, expect ~30x slowdown.

---

## 5. Code architecture

### 5.1 The `core` package

| Module | Lines | Role |
|---|---|---|
| `tle.py` | ~480 | The `TLE` class. Subclass of `DE_NSGA2`; adds the three TLE modules. Public API: `step()`, `recommend()`, `update_bandit()`. |
| `triggers.py` | ~140 | The three trigger functions: `entropy_descent_trigger()`, `fitness_stagnation_trigger()`, `environmental_change_trigger()`. Returns a boolean per generation. |
| `bandit.py` | ~120 | `UCBBandit` and `HeuristicDecayScheduler` for the LLM call budget. |
| `de_operators.py` | ~180 | `DE_rand_1_bin`, `polynomial_mutation`, `crossover` operators. |
| `llm_interface.py` | ~220 | `OllamaClient` (synchronous), `LLMResponseCache` (SHA-256 keyed JSON cache), and the `query_llm()` high-level helper. |
| `moo_utils.py` | ~310 | `non_dominated_sort`, `crowding_distance`, `compute_igd`, `compute_hv` (numba-accelerated inner loop). |
| `prompts.py` | ~90 | `SYSTEM_PROMPT` and `build_user_prompt(state)` --- see Appendix A.1 of the paper for the full template. |

### 5.2 The `proposed` package

Contains the top-level entry point that runs the full TLE loop end-to-end and
prints the population statistics that become Tables 1--5 in the paper.

### 5.3 The `baselines` package

Only the non-trivial baselines (MOEA/DD and PPS-DMOEA) live here, because
they are not in the `pymoo` library. DE, NSGA-II, MOEA/D, and DNSGA-II-A are
implemented inside `core/tle.py` and switched via a constructor flag.

### 5.4 The `experiments` package

Every `run_*.py` script is a standalone CLI tool that reads its hyperparameters
from a `config` dictionary at the top of the file, runs the experiment, and
writes a JSON file to `results/raw/`. Every `plot_*.py` script is a
publication-quality matplotlib figure generator that reads the same JSON
files and writes a PDF + PNG pair to `results/figures/`.

---

## 6. Reproducing the experiments

### 6.1 Main 8-seed comparison (Tables 1, 2 + Friedman)

```bash
# Step 1: run the 8 seeds (writes results/raw/sec_main_v3.json)
python -m experiments.run_main_cec2018 --n_seeds 8

# Step 2: compute the Friedman test + Nemenyi CD
python -m experiments.friedman_test --input results/raw/sec_main_v3.json

# Step 3: regenerate the IGD / HV bar plots (Figures: fig_main_igd, fig_main_hv)
python -m experiments.plot_tevc --input results/raw/sec_main_v3.json
```

### 6.2 Ablation (Table 3, V0--V3)

```bash
python -m experiments.run_sec_experiments --variants V0,V1,V2,V3 --n_seeds 5
python -m experiments.plot_tevc --ablation results/raw/sec_ablation_v2.json
```

### 6.3 UAV scenario (Table 5)

```bash
python -m experiments.run_uav --n_fleets 4 8 --n_seeds 5
python -m experiments.plot_tevc --uav results/raw/exp3_uav_v2.json
```

### 6.4 Cross-LLM (Figure: fig_cross_llm)

```bash
python -m experiments.run_cross_llm --models qwen2.5:7b,qwen3.5:9b,omnicoder-9b --n_seeds 2
python -m experiments.plot_cross_llm --input results/raw/exp6_cross_llm.json
```

### 6.5 Regenerate the graphical abstract

```bash
python -m experiments.graphical_abstract
# -> results/figures/graphical_abstract.png (5x5 cm @ 600 dpi)
```

---

## 7. Hyperparameters

All hyperparameters are defined as module-level constants at the top of
each `run_*.py` script. The full table is also reported in Appendix A.2 of
the paper. The default values are:

| Parameter | Value | Notes |
|---|---|---|
| Population size $N$ | 100 | DE/NSGA-II population |
| Number of generations $T$ | 200 | including environmental changes |
| DE scaling factor $F$ | 0.5 (initial) | modulated by LLM in $[0.3, 0.9]$ |
| DE crossover rate $CR$ | 0.9 (initial) | modulated by LLM in $[0.5, 1.0]$ |
| Polynomial mutation $\eta_m$ | 20 | SBX + PM |
| Environmental change frequency $\tau$ | 20 generations | small-step |
| Change severity $\sigma$ | problem-specific | see CEC 2018 spec |
| UCB1 exploration constant $c$ | $\sqrt{2}$ | Auer 2002 |
| UCB1 budget cap $B_{\max}$ | 60 (5--15% of $T$) | per-run |
| Trigger window $W$ | 10 generations | entropy + stagnation window |
| Stagnation threshold $\delta$ | $10^{-4}$ | relative IGD improvement |
| LLM temperature | 0.7 | Ollama default for instruct models |
| LLM max tokens | 256 | JSON output cap |

---

## 8. Hardware requirements

| Scenario | Wall time | GPU-h |
|---|---|---|
| 8-seed main comparison (DF1--DF5) | ~25 h | 25 |
| 5-seed ablation (4 variants x 2 problems) | ~3 h | 3 |
| 5-seed UAV (2 fleet sizes) | ~3 h | 3 |
| 2-seed cross-LLM (3 models x 3 problems) | ~6 h | 6 |
| **Total** | **~37 h** | **~37** |
| Total with reruns, debugging, plot regen | ~90 h | 90 |

(Tested on a single NVIDIA RTX 4090, 24 GB VRAM, AMD Ryzen 9 7950X, 64 GB
RAM.) The bottleneck is LLM inference, not DE/NSGA-II compute (which is
negligible in comparison).

CPU-only reproduction is supported but 25--30x slower.

---

## 9. Results directory layout

```
results/
├── raw/                          # small JSON files, committed for reproducibility
│   ├── sec_main_v3.json          # 8-seed main comparison, 215 runs
│   ├── sec_ablation_v2.json      # 5-seed ablation, 4 variants x 2 problems
│   ├── exp3_uav_v2.json          # 5-seed UAV comparison
│   ├── exp4_moeadd.json          # MOEA/DD baseline runs
│   ├── exp6_cross_llm.json       # 2-seed cross-LLM, 3 models x 3 problems
│   ├── sec_pps_real_df1_df5.json # extended PPS-DMOEA runs on DF1+DF5
│   └── *.log, *.err              # stdout/stderr from the run scripts
│
├── figures/                      # generated PNG/PDF, gitignored
│   ├── fig_main_igd.{png,pdf}
│   ├── fig_main_hv.{png,pdf}
│   ├── fig_convergence_curves.{png,pdf}
│   ├── fig_pareto_front_df2.{png,pdf}
│   ├── fig_ablation.{png,pdf}
│   ├── fig_uav.{png,pdf}
│   ├── fig_cross_llm.{png,pdf}
│   ├── fig_budget_comparison.{png,pdf}
│   ├── fig_cost_quality.{png,pdf}
│   ├── fig_llm_calls.{png,pdf}
│   ├── tle_architecture_v2.{png,pdf}
│   └── graphical_abstract.png    # 5x5 cm @ 600 dpi
│
└── llm_cache/                    # per-prompt Ollama response cache, gitignored
    └── <sha256_hash>.json        # {"prompt": ..., "response": ..., "ts": ...}
```

**JSON result schema** (a single run):

```json
{
  "problem": "DF1",
  "algorithm": "TLE",
  "seed": 7,
  "n_gen": 200,
  "pop_size": 100,
  "llm_model": "qwen2.5:7b",
  "metrics": {
    "igd_per_gen":    [0.92, 0.81, ..., 0.6476],
    "hv_per_gen":     [0.0, 0.05, ..., 0.1827],
    "llm_calls":      42,
    "llm_call_gens":  [12, 24, 36, 48, ...]
  },
  "hyperparams": {
    "F": 0.5, "CR": 0.9, "pop_size": 100, "T": 200,
    "bandit": "UCB1", "trigger_window": 10
  }
}
```

---

## 10. Figures: what is in the paper, what is supplementary

The main paper uses **4 figures + 1 graphical abstract** in its body. The
remaining ~20 PNGs in `results/figures/` are committed to this repository
as **GitHub-side supplementary material** to provide additional evidence
and reproducibility context. They are NOT a formally typeset supplementary
PDF; they are raw plots with the same data the paper uses.

| File | Where it appears | Why it is not in the paper body |
|---|---|---|
| `tle_architecture_v2.png` | §3 Method (fig:arch) | in the paper |
| `fig_cost_quality.png` | §5 Results (fig:costqual) | in the paper |
| `fig_llm_calls.png` | §5 Results (fig:llmcalls) | in the paper |
| `fig_cross_llm.png` | §6 Discussion (fig:cross) | in the paper |
| `graphical_abstract.png` | EVISE upload | in EVISE |
| `fig_main_igd.png` | (supplementary) | data already in **Table 1** |
| `fig_main_hv.png` | (supplementary) | data already in **Table 2** |
| `fig_convergence_curves.png` | (supplementary) | the 8-seed dynamic-trajectory story is hard to convey in a table; kept here for transparency |
| `fig_pareto_front_df2.png` | (supplementary) | the "PPS-DMOEA catastrophic" image — paper mentions it in §6.2, the figure lives here |
| `fig_ablation.png` | (supplementary) | data already in **Table 3** |
| `fig_uav.png` | (supplementary) | data already in **Table 5** |
| `fig_budget_comparison.png` | (supplementary) | bandit-vs-heuristic evidence; the paper mentions it in §5.3 ablation but the figure is here |
| `tle_architecture.png` | _deprecated_ | v1 architecture (superseded by v2) |
| `cec2018_hv.png`, `cec2018_igd.png` | _deprecated_ | early bar-chart versions |
| `convergence.png`, `cost_quality.png` | _deprecated_ | early plot-script outputs |
| `invocations.png`, `uav_metrics.png`, `llm_sensitivity.png` | _deprecated_ | early UAV / LLM sensitivity plots |
| `fig_convergence.png`, `fig_hv_comparison.png`, `fig_main_comparison.png` | _deprecated_ | mid-iteration versions |
| `llm_calls_long_vs_short.png`, `long_budget_validation.png` | _deprecated_ | early validation plots |

If a reviewer asks for one of the supplementary figures to be moved into the
paper body (which is a common revision outcome), the corresponding PNG is
already at the right resolution and aspect ratio and can be `\includegraphics`ed
without re-plotting.

---

## 11. License

This repository is released under the **MIT License**. See `LICENSE` (or the
top of every source file) for the full text.

The CEC 2018 benchmark functions are not bundled --- they are downloaded
from the official CEC archive on first run.

The LLM model weights are not bundled --- they are pulled from the
[Ollama model registry](https://ollama.com/library).

---

## 12. Citation

If you use this code in academic work, please cite the accompanying paper:

```bibtex
@article{anon2026tle,
  title   = {TLE: A Triggered {LLM}-Enhanced Framework for Dynamic
             Multi-Objective Optimization --- An Empirical Study},
  author  = {Anonymous, Anonymous and Anonymous, Anonymous},
  journal = {Swarm and Evolutionary Computation},
  year    = {2026},
  note    = {Under review}
}
```

(The full author list and DOI will be filled in once the paper is accepted.
For now the metadata is anonymized for double-blind review.)

---

## 13. Contact

For questions about the code:

- Open a GitHub issue at <https://github.com/[username]/TLE-DMO/issues>
- Or contact the corresponding author (see the cover letter for details)

For questions about the paper itself, contact the corresponding author
through the journal submission system.
