# TLE: Triggered LLM-Enhanced Evolutionary Algorithm

> An open-source Python implementation of the **TLE** framework for
> **dynamic multi-objective optimization (DMO)**, with a triple-signal
> trigger, a dual-channel LLM-to-EA mapping, and a UCB1 bandit-based LLM
> call budget scheduler. All experimental artifacts of the accompanying
> paper (Tables 1-5, Figures 1-6, plus the graphical abstract) are
> reproducible from a single command.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)]()
[![Status](https://img.shields.io/badge/status-paper%20under%20review-yellow.svg)]()

**Authors:** Shu-Chuan Chu, Ya-Yu Zhang, Tong-Bang Jiang, Shyi-Ming Chen,
Vaclav Snasel, Jeng-Shyang Pan (corresponding) — in submission order.
**Peer review:** single-blind (reviewers see author names; we still
recommend anonymising any new GitHub issues you file about the code).

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
(DF1, DF2, DF3, DF5, DF7, $n = 8$ seeds per problem) and on a dynamic
multi-UAV task-allocation scenario ($n = 5$ seeds, four fleet sizes, 200
generations per configuration). A cross-LLM sensitivity analysis uses
three locally deployed open-source models: **Qwen-2.5-7B-Instruct**,
**Qwen-3.5-9B-Instruct**, and **OmniCoder-9B-Instruct**.

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
├── baselines/                # baseline algorithms that need their own class
│   ├── __init__.py           #     re-exports MOEADD, PPSDEBaseline
│   ├── moea_dd.py            #     MOEA/DD-like (Li & Zhang 2015)
│   └── pps_dmoea.py          #     PPS-DMOEA (Zhou et al. 2014)
│
├── benchmarks/               # problem definitions
│   ├── __init__.py           #     re-exports DMOProblem, get_reference_pf, ...
│   ├── cec2018.py            #     CEC 2018 DF1/DF2/DF3/DF5/DF7/DF10 (DF10 is 3-obj)
│   └── uav_scenario.py       #     dynamic multi-UAV task-allocation simulator
│
├── core/                     # TLE framework core (all algorithms live here)
│   ├── __init__.py           #     re-exports TLE, DEBaseline, DNSGAIIA, ...
│   ├── bandit.py             #     UCB1 bandit + HeuristicDecayScheduler + fixed budget
│   ├── de_operators.py       #     DE/rand/1/bin + polynomial mutation
│   ├── llm_interface.py      #     Ollama client + persistent LLM response cache
│   ├── moo_utils.py          #     non-dominated sort, crowding distance, IGD/HV
│   ├── multi_action.py       #     multi-action variant of TLE (TLE-MA in the paper)
│   ├── prompts.py            #     system + user prompt templates
│   ├── tle.py                #     the TLE class (DE/NSGA-II backbone + 3 TLE modules)
│   └── triggers.py           #     triple-signal trigger
│
├── proposed/                 # single-file CLI entry point (Algorithm 1 in the paper)
│   ├── __init__.py
│   └── run_tle.py            #     `python -m proposed.run_tle --problem DF1 --n_seeds 8`
│
├── experiments/              # run scripts and plot scripts (reproduces the paper)
│   ├── run_main_cec2018.py   # 5-algorithm × 5-problem × 8-seed main comparison
│   ├── run_v3_seeds.py       # 75 extra runs that produced sec_main_v3.json
│   ├── run_sec_experiments.py# 4-variant ablation (V0--V3)
│   ├── run_uav.py            # 4-/8-UAV scenario
│   ├── run_uav_30seeds.py    # 30-seed UAV (the headline 8-UAV table)
│   ├── run_uav_b3_ablation.py# per-action ablation on the UAV scenario
│   ├── run_cross_llm.py      # 3 models × 3 problems × 2 seeds
│   ├── run_moeadd.py         # MOEA/DD baseline (separate to keep the main script light)
│   ├── run_pareto_fronts.py  # 3 Pareto-front snapshots for Fig.6
│   ├── run_trigger_sweep.py  # trigger-threshold sweep (used by Fig.S3)
│   ├── run_trigger_threshold.py
│   ├── friedman_test.py      # Friedman + Nemenyi critical-difference computation
│   ├── plot_tevc.py          # 9 publication-quality IGD / HV / convergence / scatter plots
│   ├── plot_cross_llm.py     # cross-LLM diamond + per-call latency plots
│   ├── plot_extra.py         # architecture / cost-quality / LLM-call plots
│   ├── plot_nemenyi_cd.py    # critical-difference diagram
│   ├── plot_seed_boxplots.py # per-seed IGD box plots
│   ├── plot_trigger_sweep.py # trigger-threshold sweep plot
│   ├── plot_pareto_dispatch.py
│   └── graphical_abstract.py # 5×5 cm graphical abstract
│
├── results/                  # all experimental output (mostly regenerable)
│   ├── raw/                  # 11 small JSON result files (committed for reproducibility)
│   ├── figures/              # generated PNG/PDF (regenerated by plot_*.py; gitignored)
│   └── llm_cache/            # per-prompt Ollama response cache (gitignored)
│
├── .gitignore                # Python / IDE / OS / large-binary exclusions
├── requirements.txt
├── run_all.sh                # one-command full reproduction
└── README.md                 # this file
```

**Package layout.** Every directory under `core/`, `baselines/`, `benchmarks/`,
`experiments/`, `proposed/` has an `__init__.py` that re-exports the public
API, so you can `import core`, `from benchmarks import DMOProblem`,
`from proposed import run_tle` etc. without touching `sys.path`. The
`experiments/*.py` and `proposed/run_tle.py` scripts additionally ship a
small preamble that puts the repository root on `sys.path` and exposes
`RAW_DIR`, `FIG_DIR`, and `CACHE_DIR` as `Path` constants, so each
script is runnable from any working directory.

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
# Optional: clean previous results (raw/ is committed for reproducibility;
# you usually want to keep it)
# rm -rf results/raw/*

# Full reproduction (~90 GPU-h on RTX 4090)
bash run_all.sh

# OR: just the headline 8-seed main comparison (~25 GPU-h)
python -m experiments.run_main_cec2018 --seeds 0 1 2 3 4 5 6 7 --pop-size 50 --max-gen 200

# OR: a single-seed smoke test of the proposed method (cache-hits make this ~3s)
python -m proposed.run_tle --problem DF1 --seeds 0 --max-gen 5 --pop-size 10
```

`run_all.sh` re-executes, in order:

1. The 8-seed main comparison on DF1/DF2/DF3/DF5/DF7
2. The 5-seed ablation (V0--V3)
3. The 5-seed UAV comparison (4-UAV and 8-UAV)
4. The 2-seed cross-LLM analysis (3 models × 3 problems)
5. The Friedman test + Nemenyi CD
6. All plot regeneration (including the graphical abstract)

The total wall time is dominated by LLM inference. If you only have CPU
hardware, expect ~30x slowdown.

---

## 5. Code architecture

### 5.1 The `core` package

| Module | Lines | Role |
|---|---|---|
| `tle.py` | ~480 | The `TLE` class. Subclass of the shared DE/NSGA-II engine; adds the three TLE modules. Public API: `optimize()`. |
| `triggers.py` | ~140 | The three trigger functions: `entropy_descent_trigger`, `fitness_stagnation_trigger`, `environmental_change_trigger`. Returns a boolean per generation. |
| `bandit.py` | ~120 | `UCBBandit` and `HeuristicDecayScheduler` for the LLM call budget. |
| `de_operators.py` | ~180 | `de_rand_1_bin`, `polynomial_mutation`, `crossover` operators. |
| `llm_interface.py` | ~220 | `LLMClient` (synchronous Ollama wrapper), `LLMResponseCache` (md5-keyed JSON cache), and the `query_llm()` high-level helper. |
| `moo_utils.py` | ~310 | `fast_non_dominated_sort`, `crowding_distance`, `compute_igd`, `compute_hv` (numba-accelerated inner loop optional). |
| `multi_action.py` | ~340 | The `TLEMultiAction` class (TLE-MA in the paper): multi-action variant where the LLM picks one of `VALID_ACTIONS` per generation. |
| `prompts.py` | ~330 | `SYSTEM_PROMPT` and `build_user_prompt(state)` --- see Appendix A.1 of the paper for the full template. |

### 5.2 The `proposed` package

Contains the single-file entry point `proposed.run_tle` that runs the full
TLE loop end-to-end without going through the multi-algorithm experiment
driver.  Useful for a quick smoke test or a single-(problem, seed) run:

```bash
python -m proposed.run_tle --problem DF1 --seeds 0 --max-gen 5 --pop-size 10
```

### 5.3 The `baselines` package

The five baselines compared against TLE in the paper are:

| Baseline | Where it lives | Why not in `pymoo`? |
|---|---|---|
| DE + NSGA-II selection | `core.tle.DEBaseline` | our own DE/NSGA-II engine (shared across all algos) |
| DNSGA-II-A | `core.tle.DNSGAIIA` | small dynamic-specific tweak (random immigrants after change) |
| PPS-DMOEA | `baselines.pps_dmoea.PPSDEBaseline` | population-prediction logic is non-trivial |
| MOEA/DD | `baselines.moea_dd.MOEADD` | decomposition + DE update is non-trivial |
| DE-LM-static-trigger | `core.tle.StaticLMEABaseline` | static-trigger LLM-EA (for ablation) |

The 5th entry of the main comparison, **DE-LM-static-trigger**, is the
ablation baseline that invokes the LLM at every generation (vs. TLE's
triggered scheme). All five are re-exported from `core.__init__` and
`baselines.__init__` so the experiment scripts can import them
uniformly.

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
python -m experiments.run_sec_experiments --seeds 0 1 2 3 4
python -m experiments.plot_tevc
```

### 6.3 UAV scenario (Table 5)

```bash
# 4-/8-UAV comparison (the headline 8-UAV row in Table 5)
python -m experiments.run_uav --seeds 0 1 2 3 4 --n-uavs 4 8
python -m experiments.plot_tevc

# 30-seed UAV (the 8-UAV detailed table)
python -m experiments.run_uav_30seeds
```

### 6.4 Cross-LLM (Figure: fig_cross_llm)

```bash
python -m experiments.run_cross_llm --seeds 0 1
python -m experiments.plot_cross_llm
```

### 6.5 Regenerate the graphical abstract

```bash
python -m experiments.graphical_abstract
# -> results/figures/graphical_abstract.png (5×5 cm @ 600 dpi = 1181×1181 px)
```

---

## 7. Hyperparameters

All hyperparameters are defined as module-level constants at the top of
each `run_*.py` script. The full table is also reported in Appendix A.2 of
the paper. The default values are:

| Parameter | Value | Notes |
|---|---|---|
| Population size $N$ | 50 | standard CEC 2018 DMO convention |
| Number of generations $T$ | 200 | including environmental changes |
| Decision variables $D$ | 10 | consistent across all problems |
| DE scaling factor $F$ | 0.5 (initial) | modulated by LLM in $[0.3, 0.9]$ |
| DE crossover rate $CR$ | 0.9 (initial) | modulated by LLM in $[0.5, 1.0]$ |
| Polynomial mutation $\eta_m$ | 20 | SBX + PM |
| Environmental change frequency $\tau$ | 10 generations | small-step (matches PlatEMO) |
| Change severity $\sigma$ | problem-specific | see CEC 2018 spec |
| UCB1 exploration constant $c$ | $\sqrt{2}$ | Auer 2002 |
| UCB1 budget cap $B_{\max}$ | 60 (5--15% of $T$) | per-run |
| Trigger window $W$ | 10 generations | entropy + stagnation window |
| Stagnation threshold $\delta$ | $10^{-4}$ | relative IGD improvement |
| LLM temperature | 0.0 | deterministic (matches Ollama instruct defaults) |
| LLM max tokens | 500 | JSON output cap (covers the longest response we've seen) |

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
├── raw/                          # 11 small JSON files, committed for reproducibility
│   ├── sec_main_v3.json          # 6 algorithms × 5 problems × 8 seeds = 240 runs.
│   │                             #   MOEA/DD's DF2 entry is imputed for the
│   │                             #   Friedman test (its 8 raw DF2 IGDs are
│   │                             #   catastrophic, of order 1e7 to 1e27).
│   ├── sec_ablation_v2.json      # 5-seed ablation, 4 variants x 2 problems
│   ├── exp3_uav_v2.json          # 5-seed UAV comparison, 4-/8-UAV
│   ├── exp3_uav_v3.json          # 8-UAV detailed (used by Table 5)
│   ├── exp3_uav_b3.json          # per-action ablation on 8-UAV
│   ├── exp3_uav_b6.json          # 6 seed pairs for the b6 sub-table
│   ├── exp3_uav_combined.json    # combined UAV runs across scripts
│   ├── exp4_moeadd.json          # MOEA/DD baseline runs
│   ├── exp6_cross_llm.json       # 2-seed cross-LLM, 3 models × 3 problems
│   ├── exp_pareto_fronts.json    # 3 Pareto-front snapshots for Fig.6
│   └── exp_trigger_threshold.json# trigger-threshold sweep
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
│   └── graphical_abstract.png    # 5×5 cm @ 600 dpi
│
└── llm_cache/                    # per-prompt Ollama response cache, gitignored
    └── <md5_hash>.json           # {"prompt": ..., "response": ..., "ts": ...}
```

**JSON result schema** (a single run):

```json
{
  "algo": "TLE",
  "problem": "DF1",
  "seed": 7,
  "max_gen": 200,
  "pop_size": 50,
  "igd": 0.6476,
  "hv": 0.1827,
  "elapsed_sec": 12.4,
  "invocations": 42
}
```

(The `v3` files do not embed per-generation IGD/HV trajectories or the
hyperparameter snapshot — those live in the per-generation LLM cache
under `results/llm_cache/` and can be reconstructed by re-running the
matching script with the same seed. The committed `raw/` files are the
*minimal* end-of-run summary used by the plot scripts.)

---

## 10. Figures

The main paper uses **4 figures + 1 graphical abstract** in its body. The
companion PDF (`supplementary_material.pdf`, attached separately) contains
the additional plots. The `results/figures/` directory in this repository
holds 10 regenerable plots (PNG + PDF, 300 dpi); they are gitignored and
regenerated from `results/raw/*.json` by `experiments/plot_tevc.py` and
`experiments/plot_cross_llm.py`.

| File (regenerable) | Where it appears |
|---|---|
| `fig_main_igd.png` / `.pdf` | (plot companion) — the IGD bar plot in §5 |
| `fig_main_hv.png` / `.pdf` | (plot companion) — the HV bar plot in §5 |
| `fig_convergence_curves.png` / `.pdf` | (supplementary) — exponential-decay fit to per-generation IGD |
| `fig_pareto_front_df2.png` / `.pdf` | (supplementary) — the "PPS-DMOEA catastrophic" image |
| `fig_ablation.png` / `.pdf` | (plot companion) — the ablation bar plot |
| `fig_uav.png` / `.pdf` | (plot companion) — the UAV fleet-size comparison |
| `fig_llm_calls.png` / `.pdf` | (plot companion) — the LLM-call budget bar plot |
| `fig_cost_quality.png` / `.pdf` | (plot companion) — the cost-vs-quality scatter |
| `fig_budget_comparison.png` / `.pdf` | (plot companion) — bandit vs. heuristic scheduler |
| `graphical_abstract.png` | 5×5 cm @ 600 dpi for use as a thumbnail |

To regenerate all 10:

```bash
python -m experiments.plot_tevc
python -m experiments.plot_cross_llm
python -m experiments.graphical_abstract
```

---

## 11. License

This repository is released under the **MIT License**. See `LICENSE` (or the
top of every source file) for the full text.

The CEC 2018 benchmark functions are implemented from the published spec in
`benchmarks/cec2018.py`; no external binary is bundled.

The LLM model weights are not bundled — they are pulled from the
[Ollama model registry](https://ollama.com/library).

---

## 12. Citation

If you use this code in academic work, please cite the accompanying paper:

```bibtex
@article{chu2026tle,
  title   = {TLE: A Triggered {LLM}-Enhanced Framework for Dynamic
             Multi-Objective Optimization --- An Empirical Study},
  author  = {Chu, Shu-Chuan and Zhang, Ya-Yu and Jiang, Tong-Bang
             and Chen, Shyi-Ming and Snasel, Vaclav and Pan, Jeng-Shyang},
  journal = {Swarm and Evolutionary Computation},
  year    = {2026},
  note    = {Under review}
}
```

The author list above is the full author list in submission order.

---

## 13. Contact

For questions about the code:

- Open a GitHub issue at <https://github.com/Ss1mpleee/A-Triggered-LLM-Enhanced-Framework-for-Dynamic-Multi-Objective-Optimization-An-Empirical-Study/issues>
- Or contact the corresponding author, Jeng-Shyang Pan, at
  `100112@nuist.edu.cn`

For questions about the paper itself, contact the corresponding author
through the journal submission system.

---

## 14. Self-test (reviewer sanity check)

A 1-minute end-to-end check is shipped at the repository root as
`_smoke_test.py`. It verifies that:

1. All five packages (`core`, `baselines`, `benchmarks`, `proposed`,
   `experiments`) import cleanly.
2. Every essential script in `experiments/` and `proposed/` has a
   working `--help`.
3. `proposed.run_tle` actually runs a 5-generation TLE and reports a
   finite IGD.
4. Every algorithm class (`DEBaseline`, `TLE`, `DNSGAIIA`, `PPSDMOEA`,
   `MOEADD`, `StaticLMEABaseline`) instantiates and runs end-to-end.
5. The LLM cache hits on a second call with an identical prompt.
6. No `.py` file in the repo contains a hardcoded Windows path.

Run it any time after cloning:

```bash
python _smoke_test.py
```

Expected output ends with `ALL SMOKE TESTS PASSED`. If a reviewer
clones the repo on a clean machine and this script fails, please
file an issue with the full output.

---

## 15. Cache limitations and reviewer-side re-runs

The `results/llm_cache/` directory is **gitignored** — a fresh clone
will not contain any cache. The first time you run an LLM-backed
script (`experiments.run_main_cec2018`, `experiments.run_cross_llm`,
`proposed.run_tle`, etc.), the LLM client will issue fresh Ollama
calls. The cache will then be repopulated and subsequent calls
will be instant.

The 8-seed main comparison (240 runs) takes ~25 GPU-h on an RTX 4090
when the cache is cold. The cross-LLM section (18 runs) needs the
three Ollama models pulled locally:

```bash
ollama pull qwen2.5:7b
ollama pull qwen3.5:9b
ollama pull carstenuhlig/omnicoder-9b:q8_0
```

If you do not have all three, only the `qwen2.5:7b` part of the
cross-LLM experiment will work; the other two model variants will
fall back to the (empty) per-model cache and issue fresh calls.

---

## 16. About the data

All 11 JSON files in `results/raw/` are the **end-of-run** summary
schema described in Section 9. The 240-run `sec_main_v3.json` is
the authoritative source for the headline Table 1 (IGD) and
Table 2 (HV); the four other tables (Table 3 ablation, Table 4
Friedman, Table 5 UAV) come from the other 10 JSONs. None of the
JSONs include per-generation trajectories — those are not needed
to regenerate any of the paper's tables or figures.

The `MOEA/DD` baseline is the one exception: its 8 raw DF2 IGDs
(1e7 to 1e27) are the catastrophic failure mode discussed in
Section 6.2 of the paper, and they are imputed in the Friedman
test rather than averaged in. All other algorithms' DF2 IGDs
are filtered at the $\mathrm{IGD} > 2$ level for display in
Table 1 (the raw values are still in the JSON).
