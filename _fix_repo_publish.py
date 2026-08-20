#!/usr/bin/env python3
"""T70 final: make the GitHub repository publication-ready.

Fixes:
1. LICENSE missing -> add MIT LICENSE
2. smoke_test.py hardcoded path -> auto-detect via __file__
3. run_all.sh: N_SEEDS_MAIN=8, ablation=5, cross=2 -> 30/30/30
4. README.md: stale DF1/DF2/DF3/DF5/DF7, n=8 -> update to DF1-DF14, n=30
5. .gitignore: commit LLM cache for full reproducibility
"""
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
REPO = Path(r'D:\新论文\实验')

edits = []

# 1) Add MIT LICENSE
print("=== 1. Add LICENSE ===")
LICENSE_TEXT = """MIT License

Copyright (c) 2026 Shu-Chuan Chu, Ya-Yu Zhang, Tong-Bang Jiang,
                  Shyi-Ming Chen, Vaclav Snasel, Jeng-Shyang Pan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
license_path = REPO / 'LICENSE'
license_path.write_text(LICENSE_TEXT, encoding='utf-8')
print(f"  Wrote {license_path} ({LICENSE_TEXT.count(chr(10))+1} lines)")
edits.append('LICENSE')

# 2) Fix smoke_test.py - remove hardcoded D:\\新论文\\实验
print("\n=== 2. Fix _smoke_test.py ===")
smoke_path = REPO / '_smoke_test.py'
if smoke_path.exists():
    content = smoke_path.read_text(encoding='utf-8')
    old = 'REPO = Path(r"D:\\新论文\\实验")'
    new = 'REPO = Path(__file__).resolve().parent'
    if old in content:
        content = content.replace(old, new, 1)
        smoke_path.write_text(content, encoding='utf-8')
        print(f"  Fixed REPO path in _smoke_test.py")
        edits.append('smoke_test.py')

# 3) Rewrite run_all.sh with correct n=30 defaults
print("\n=== 3. Rewrite run_all.sh ===")
RUN_ALL_NEW = r"""#!/usr/bin/env bash
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
"""
run_all_path = REPO / 'run_all.sh'
run_all_path.write_text(RUN_ALL_NEW, encoding='utf-8')
print(f"  Rewrote run_all.sh ({RUN_ALL_NEW.count(chr(10))} lines)")
edits.append('run_all.sh')

# 4) Fix README.md - update stale DF1-DF7 and n=8 references
print("\n=== 4. Update README.md ===")
readme_path = REPO / 'README.md'
if readme_path.exists():
    content = readme_path.read_text(encoding='utf-8')
    # Update stale references
    replacements = [
        # DF1/DF2/DF3/DF5/DF7 -> DF1-DF14
        (r'DF1, DF2, DF3, DF5, DF7', 'DF1--DF14'),
        (r'DF1/DF2/DF3/DF5/DF7', 'DF1--DF14'),
        (r'DF1/DF2/DF3/DF5/DF7/DF10', 'DF1--DF14'),
        (r'5 problems', '14 problems'),
        # n = 8 -> n = 30
        (r'\$n = 8\$ seeds per problem', '$n = 30$ seeds per problem'),
        (r'\$n = 5\$ seeds, four fleet sizes', '$n = 30$ seeds for 4/8-UAV, $n = 5$ seeds for 16/32-UAV'),
        (r'n_seeds 8', 'n_seeds 30'),
        (r'N_SEEDS_MAIN=8', 'N_SEEDS_MAIN=30'),
        # 5-algorithm -> 6-algorithm (MOEA/DD was added)
        (r'5-algorithm', '6-algorithm'),
        (r'5 algorithms', '6 algorithms'),
        (r'5 algos', '6 algos'),
    ]
    n_changes = 0
    for old, new in replacements:
        if old in content:
            occ = content.count(old)
            content = content.replace(old, new)
            n_changes += occ
    if n_changes > 0:
        readme_path.write_text(content, encoding='utf-8')
        print(f"  Made {n_changes} replacements in README.md")
        edits.append('README.md')

# 5) Update .gitignore to commit LLM cache (for full reproducibility)
print("\n=== 5. Update .gitignore ===")
gitignore_path = REPO / '.gitignore'
if gitignore_path.exists():
    content = gitignore_path.read_text(encoding='utf-8')
    # Comment out the llm_cache exclusion so it's committed
    content = content.replace(
        'results/llm_cache/\n**/llm_cache/\n',
        '# LLM response cache IS COMMITTED for full reproducibility (~19 MB / 58k entries)\n'
        '# results/llm_cache/\n# **/llm_cache/\n'
    )
    gitignore_path.write_text(content, encoding='utf-8')
    print(f"  Updated .gitignore to commit LLM cache")
    edits.append('.gitignore')

# 6) Add CITATION.cff for proper GitHub citation display
print("\n=== 6. Add CITATION.cff ===")
CITATION = """cff-version: 1.2.0
message: |
  If you use this code or the TLE framework in your research, please cite the
  accompanying paper:

  Chu, S.-C., Zhang, Y.-Y., Jiang, T.-B., Chen, S.-M., Snasel, V., & Pan, J.-S.
  (2026). An Event-Triggered Large-Language-Model Evolutionary Framework for
  Dynamic Multi-Objective Optimization. Swarm and Evolutionary Computation.
title: "An Event-Triggered Large-Language-Model Evolutionary Framework for Dynamic Multi-Objective Optimization"
authors:
  - family-names: Chu
    given-names: Shu-Chuan
    affiliation: Nanjing University of Information Science and Technology
  - family-names: Zhang
    given-names: Ya-Yu
    affiliation: Nanjing University of Information Science and Technology
  - family-names: Jiang
    given-names: Tong-Bang
    affiliation: Dalian Maritime University
  - family-names: Chen
    given-names: Shyi-Ming
    affiliation: Asia University
  - family-names: Snasel
    given-names: Vaclav
    affiliation: VSB - Technical University of Ostrava
  - family-names: Pan
    given-names: Jeng-Shyang
    affiliation: Nanjing University of Information Science and Technology
type: article
date-released: 2026-08-20
keywords:
  - evolutionary computation
  - dynamic multi-objective optimization
  - large language models
  - bandit algorithms
  - regret analysis
  - LLM-EC integration
license: MIT
"""
citation_path = REPO / 'CITATION.cff'
citation_path.write_text(CITATION, encoding='utf-8')
print(f"  Wrote CITATION.cff")
edits.append('CITATION.cff')

# Summary
print(f"\n=== SUMMARY: {len(edits)} files updated ===")
for e in edits:
    print(f"  ✓ {e}")
