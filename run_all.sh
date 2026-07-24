#!/usr/bin/env bash
# =============================================================================
# run_all.sh — single-command full reproduction
#
# Re-executes, in order:
#   1. 8-seed main comparison on DF1--DF5
#   2. 5-seed ablation (V0--V3)
#   3. 5-seed UAV comparison (4-UAV and 8-UAV)
#   4. 2-seed cross-LLM analysis (3 models x 3 problems)
#   5. Friedman test + Nemenyi CD
#   6. All plot regeneration (including the graphical abstract)
#
# Total wall time: ~37 GPU-h on a single NVIDIA RTX 4090, ~90 GPU-h including
# reruns, debugging, and plot regeneration. CPU-only is 25--30x slower.
#
# Usage:
#   bash run_all.sh                   # full reproduction
#   bash run_all.sh --quick           # 2 seeds / 2 variants (smoke test)
#   bash run_all.sh --skip-cross-llm  # skip the 6-GPU-h cross-LLM block
# =============================================================================
set -euo pipefail

# Defaults
N_SEEDS_MAIN=8
N_SEEDS_ABLATION=5
N_SEEDS_UAV=5
N_SEEDS_CROSS=2
DO_CROSS_LLM=1

# Argument parsing
for arg in "$@"; do
  case $arg in
    --quick)
      N_SEEDS_MAIN=2
      N_SEEDS_ABLATION=2
      N_SEEDS_UAV=2
      N_SEEDS_CROSS=1
      shift
      ;;
    --skip-cross-llm)
      DO_CROSS_LLM=0
      shift
      ;;
    --main-seeds=*)
      N_SEEDS_MAIN="${arg#*=}"
      shift
      ;;
    --cross-seeds=*)
      N_SEEDS_CROSS="${arg#*=}"
      shift
      ;;
    -h|--help)
      sed -n '3,18p' "$0"
      exit 0
      ;;
  esac
done

# Environment
cd "$(dirname "$0")"
export PYTHONPATH=".:$PYTHONPATH"
export PYTHONHASHSEED=42

echo "=================================================================="
echo "TLE-DMO full reproduction"
echo "  main seeds   : $N_SEEDS_MAIN"
echo "  ablation seeds: $N_SEEDS_ABLATION"
echo "  UAV seeds    : $N_SEEDS_UAV"
echo "  cross-LLM    : $([ "$DO_CROSS_LLM" -eq 1 ] && echo "yes ($N_SEEDS_CROSS seeds)" || echo "no")"
echo "  start time   : $(date -Iseconds)"
echo "=================================================================="

# Make sure Ollama is running
if ! curl -fsS http://localhost:11434/api/version > /dev/null 2>&1; then
  echo "[!] Ollama is not running. Start it with:  ollama serve"
  exit 1
fi

# 1. Main 8-seed comparison
echo "[1/6] Main $N_SEEDS_MAIN-seed comparison on DF1--DF5..."
python -m experiments.run_main_cec2018 --n_seeds "$N_SEEDS_MAIN" 2>&1 | tee -a results/raw/main_run.log

# 2. Ablation
echo "[2/6] Ablation ($N_SEEDS_ABLATION seeds x 4 variants x 2 problems)..."
python -m experiments.run_sec_experiments --n_seeds "$N_SEEDS_ABLATION" 2>&1 | tee -a results/raw/ablation_run.log

# 3. UAV
echo "[3/6] UAV scenario ($N_SEEDS_UAV seeds x 2 fleet sizes)..."
python -m experiments.run_uav --n_seeds "$N_SEEDS_UAV" 2>&1 | tee -a results/raw/uav_run.log

# 4. Cross-LLM
if [ "$DO_CROSS_LLM" -eq 1 ]; then
  echo "[4/6] Cross-LLM ($N_SEEDS_CROSS seeds x 3 models x 3 problems)..."
  python -m experiments.run_cross_llm --n_seeds "$N_SEEDS_CROSS" 2>&1 | tee -a results/raw/cross_llm.log
else
  echo "[4/6] Cross-LLM -- skipped"
fi

# 5. Friedman test
echo "[5/6] Friedman test + Nemenyi CD..."
python -m experiments.friedman_test --input results/raw/sec_main_v3.json 2>&1 | tee results/raw/friedman.log

# 6. Plots
echo "[6/6] Regenerating all figures + graphical abstract..."
python -m experiments.plot_tevc --input results/raw/sec_main_v3.json
python -m experiments.plot_tevc --ablation results/raw/sec_ablation_v2.json
python -m experiments.plot_tevc --uav results/raw/exp3_uav_v2.json
python -m experiments.plot_cross_llm --input results/raw/exp6_cross_llm.json
python -m experiments.plot_extra --input results/raw/sec_main_v3.json
python -m experiments.graphical_abstract

echo "=================================================================="
echo "Reproduction complete: $(date -Iseconds)"
echo "Figures are in:  results/figures/"
echo "Raw JSON files:  results/raw/"
echo "=================================================================="
