#!/usr/bin/env bash
# =============================================================================
# run_all.sh -- single-command full reproduction
#
# Re-executes, in order:
#   1. 30-seed main comparison: 6 algos x 14 problems = 2,520 runs
#   2. 30-seed 4-version trigger ablation: 4 x 14 = 1,680 runs
#   3. 30-seed 4/8-UAV main, 5-seed 16/32-UAV scalability
#   4. 30-seed cross-LLM (3 models x 14 problems = 1,260 runs)
#   5. Friedman + Nemenyi post-hoc + Wilcoxon per-problem
#   6. All plot regeneration (including the graphical abstract)
#
# Total wall time on a single NVIDIA RTX 4090 (estimated):
#   - 22-24 hours clean (no cache, all 78,500 fresh LLM calls)
#   - 1.5-2 hours with the released 17,226-entry LLM cache
#   - 20 minutes for 8-UAV scenario alone (with cache)
# CPU-only is 25-30x slower.
#
# Usage:
#   bash run_all.sh                  # full reproduction with cache
#   bash run_all.sh --quick          # 2 seeds / 2 variants (smoke test)
#   bash run_all.sh --skip-cross-llm # skip the ~12h cross-LLM block
#   bash run_all.sh --clean          # ignore cache, all fresh LLM calls
# =============================================================================
set -euo pipefail

# Defaults match the published paper (T70 round 2):
#   n = 30 seeds per problem for the main / ablation / cross-LLM / 4-8 UAV,
#   n = 5 seeds for 16/32-UAV scalability (paper notes this is borderline)
N_SEEDS_MAIN=30
N_SEEDS_ABLATION=30
N_SEEDS_UAV_MAIN=30   # for 4-UAV and 8-UAV
N_SEEDS_UAV_SCALABILITY=5  # for 16-UAV and 32-UAV
N_SEEDS_CROSS=30
DO_CROSS_LLM=1
USE_CACHE=1

# Argument parsing
for arg in "$@"; do
  case $arg in
    --quick)
      N_SEEDS_MAIN=2
      N_SEEDS_ABLATION=2
      N_SEEDS_UAV_MAIN=2
      N_SEEDS_UAV_SCALABILITY=2
      N_SEEDS_CROSS=1
      shift
      ;;
    --skip-cross-llm)
      DO_CROSS_LLM=0
      shift
      ;;
    --clean)
      USE_CACHE=0
      rm -rf results/llm_cache 2>/dev/null || true
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
      sed -n '3,32p' "$0"
      exit 0
      ;;
  esac
done

# Environment
cd "$(dirname "$0")"
export PYTHONPATH=".:$PYTHONPATH"
export PYTHONHASHSEED=42

echo "=================================================================="
echo "TLE-DMO full reproduction (paper: TLE @ SWEVO 2026)"
echo "  main seeds       : $N_SEEDS_MAIN   (6 algos x 14 problems = 840 runs total)"
echo "  ablation seeds   : $N_SEEDS_ABLATION   (4 versions x 14 problems = 56 runs)"
echo "  4/8-UAV seeds    : $N_SEEDS_UAV_MAIN"
echo "  16/32-UAV seeds  : $N_SEEDS_UAV_SCALABILITY"
echo "  cross-LLM        : $([ "$DO_CROSS_LLM" -eq 1 ] && echo "yes ($N_SEEDS_CROSS seeds x 3 models x 14 problems = $((N_SEEDS_CROSS * 3 * 14)) runs)" || echo "no")"
echo "  cache            : $([ "$USE_CACHE" -eq 1 ] && echo "use released cache" || echo "clean (no cache)")"
echo "  start time       : $(date -Iseconds)"
echo "=================================================================="

# Make sure Ollama is running
if ! curl -fsS http://localhost:11434/api/version > /dev/null 2>&1; then
  echo "[!] Ollama is not running. Start it with:  ollama serve"
  echo "    Then pull the three models:"
  echo "      ollama pull qwen2.5:7b"
  echo "      ollama pull qwen3.5:9b"
  echo "      ollama pull carstenuhlig/omnicoder-9b:q8_0"
  exit 1
fi

# 1. Main 30-seed comparison
echo ""
echo "[1/6] Main $N_SEEDS_MAIN-seed comparison: 6 algos x 14 problems x $N_SEEDS_MAIN seeds = $((6 * 14 * N_SEEDS_MAIN)) runs"
python -m experiments.run_main_cec2018 --seeds $(seq 0 $((N_SEEDS_MAIN - 1))) 2>&1 | tee -a results/raw/main_run.log

# 2. Trigger ablation
echo ""
echo "[2/6] Trigger ablation: 4 versions x 14 problems x $N_SEEDS_ABLATION seeds = $((4 * 14 * N_SEEDS_ABLATION)) runs"
python -m experiments.run_sec_experiments --n_seeds $N_SEEDS_ABLATION 2>&1 | tee -a results/raw/ablation_run.log

# 3. UAV (4/8 + 16/32)
echo ""
echo "[3/6] UAV scenario: 4/8-UAV at $N_SEEDS_UAV_MAIN seeds, 16/32-UAV at $N_SEEDS_UAV_SCALABILITY seeds"
python -m experiments.run_uav_30seeds --seeds $(seq 0 $((N_SEEDS_UAV_MAIN - 1))) 2>&1 | tee -a results/raw/uav_30seeds.log
# 16/32-UAV scalability (5 seeds)
python -m experiments.run_uav --n-uavs 16 32 --seeds $(seq 0 $((N_SEEDS_UAV_SCALABILITY - 1))) 2>&1 | tee -a results/raw/uav_scalability.log

# 4. Cross-LLM (3 models x 14 problems x 30 seeds = 1260 runs)
if [ "$DO_CROSS_LLM" -eq 1 ]; then
  echo ""
  echo "[4/6] Cross-LLM: 3 models x 14 problems x $N_SEEDS_CROSS seeds = $((3 * 14 * N_SEEDS_CROSS)) runs"
  python -m experiments.run_cross_llm --n_seeds $N_SEEDS_CROSS 2>&1 | tee -a results/raw/cross_llm.log
else
  echo ""
  echo "[4/6] Cross-LLM -- skipped"
fi

# 5. Statistical analysis
echo ""
echo "[5/6] Statistical analysis (Friedman + Nemenyi + Wilcoxon)..."
python -m experiments.friedman_test --input results/raw/sec_main_v3.json 2>&1 | tee results/raw/friedman.log
python -m experiments.stats_ablation_crossllm 2>&1 | tee -a results/raw/stats.log

# 6. Plot regeneration
echo ""
echo "[6/6] Regenerating all figures + graphical abstract..."
python -m experiments.plot_tevc --input results/raw/sec_main_v3.json
python -m experiments.plot_ablation_lite --input results/raw/exp7_ablation_combined.json
python -m experiments.plot_cross_llm --input results/raw/exp6_cross_llm_n14.json
python -m experiments.plot_cross_llm_heatmap --input results/raw/exp6_cross_llm_n14.json
python -m experiments.plot_nemenyi_cd --input results/raw/sec_main_v3.json
python -m experiments.plot_outliers_and_invocations
python -m experiments.plot_seed_boxplots --input results/raw/sec_main_v3.json
python -m experiments.plot_pareto_dispatch
python -m experiments.plot_extra --input results/raw/sec_main_v3.json
python -m experiments.graphical_abstract

echo ""
echo "=================================================================="
echo "Reproduction complete: $(date -Iseconds)"
echo "Figures: results/figures/  ($(ls results/figures/ 2>/dev/null | wc -l) files)"
echo "Raw JSON: results/raw/"
echo "=================================================================="
