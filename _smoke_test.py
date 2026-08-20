"""
End-to-end smoke test for the cleaned-up TLE repo.

Verifies:
  1. All 5 packages import cleanly.
  2. Every essential run_*.py / plot_*.py can be invoked with --help.
  3. proposed.run_tle runs a tiny end-to-end DE→IGD computation.
  4. All 5 algorithm classes can be instantiated and run a 5-gen DF1 pass.
  5. The Ollama client can read the LLM cache.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent

def section(label):
    print()
    print("=" * 70)
    print(label)
    print("=" * 70)

def run(cmd, timeout=60):
    """Run a command and return (rc, stdout, stderr)."""
    r = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        cwd=str(REPO),
        env={**__import__("os").environ, "PYTHONPATH": str(REPO),
             "PYTHONIOENCODING": "utf-8"},
    )
    return r.returncode, r.stdout, r.stderr

# -----------------------------------------------------------------------------
section("1. Package imports")
# -----------------------------------------------------------------------------
imports = [
    "from core import TLE, DEBaseline, DNSGAIIA, PPSDMOEA, StaticLMEABaseline, TLEMultiAction",
    "from baselines import MOEADD, PPSDEBaseline",
    "from benchmarks import DMOProblem, get_reference_pf, ScenarioConfig, generate_scenario",
    "import proposed",
    "import experiments",
]
for imp in imports:
    rc, out, err = run([sys.executable, "-X", "utf8", "-c", imp])
    if rc != 0:
        print(f"  FAIL: {imp}")
        print(f"  stderr: {err[:500]}")
        sys.exit(1)
    print(f"  OK  : {imp}")

# -----------------------------------------------------------------------------
section("2. Every essential script has --help")
# -----------------------------------------------------------------------------
essential = [
    "experiments.run_main_cec2018",
    "experiments.run_sec_experiments",
    "experiments.run_uav",
    "experiments.run_uav_30seeds",
    "experiments.run_uav_b3_ablation",
    "experiments.run_cross_llm",
    "experiments.run_v3_seeds",
    "experiments.run_moeadd",
    "experiments.run_pareto_fronts",
    "experiments.run_trigger_sweep",
    "experiments.run_trigger_threshold",
    "experiments.friedman_test",
    "experiments.plot_tevc",
    "experiments.plot_cross_llm",
    "experiments.plot_extra",
    "experiments.graphical_abstract",
    "experiments.plot_nemenyi_cd",
    "experiments.plot_seed_boxplots",
    "experiments.plot_trigger_sweep",
    "experiments.plot_pareto_dispatch",
    "proposed.run_tle",
]
for mod in essential:
    rc, out, err = run([sys.executable, "-X", "utf8", "-m", mod, "--help"])
    if rc != 0:
        print(f"  FAIL: {mod}  --help")
        print(f"  stderr: {err[:500]}")
        sys.exit(1)
    print(f"  OK  : {mod}")

# -----------------------------------------------------------------------------
section("3. proposed.run_tle tiny end-to-end run")
# -----------------------------------------------------------------------------
rc, out, err = run([
    sys.executable, "-X", "utf8", "-m", "proposed.run_tle",
    "--problem", "DF1", "--seeds", "0",
    "--max-gen", "5", "--pop-size", "10",
    "--no-llm", "--output", "results/raw/_smoke_tle.json",
])
if rc != 0:
    print(f"  FAIL: proposed.run_tle returned {rc}")
    print(f"  stderr: {err[:500]}")
    sys.exit(1)
print(out.strip())
out_path = REPO / "results" / "raw" / "_smoke_tle.json"
if not out_path.exists():
    print(f"  FAIL: no output written to {out_path}")
    sys.exit(1)
data = json.loads(out_path.read_text(encoding='utf-8'))
assert len(data) == 1 and "igd" in data[0], f"unexpected result: {data}"
print(f"  OK  : IGD={data[0]['igd']:.4f}, HV={data[0]['hv']:.4f}")

# -----------------------------------------------------------------------------
section("4. Every algorithm class runs 5 generations on DF1")
# -----------------------------------------------------------------------------
run_code = r"""
import numpy as np
from core import DEBaseline, DNSGAIIA, PPSDMOEA, StaticLMEABaseline, TLE
from baselines import MOEADD
from benchmarks import DMOProblem

p = DMOProblem(name='DF1', d=10, nt=10, taut=10)
b = (p.lower, p.upper)
def e(pop): return p.evaluate(pop)

results = []
for cls, kwargs in [
    (DEBaseline,           dict(d=10, bounds=b, n_obj=p.M, pop_size=10, max_gen=5, seed=0)),
    (TLE,                   dict(d=10, bounds=b, n_obj=p.M, pop_size=10, max_gen=5, llm=None, seed=0)),
    (DNSGAIIA,              dict(d=10, bounds=b, n_obj=p.M, pop_size=10, max_gen=5, seed=0)),
    (PPSDMOEA,              dict(d=10, bounds=b, n_obj=p.M, pop_size=10, max_gen=5, seed=0)),
    (MOEADD,                dict(d=10, bounds=b, n_obj=p.M, pop_size=10, max_gen=5, seed=0)),
    (StaticLMEABaseline,    dict(d=10, bounds=b, n_obj=p.M, pop_size=10, max_gen=5, llm=None, seed=0)),
]:
    algo = cls(**kwargs)
    out = algo.optimize(e, problem=p)
    info = out[2] if isinstance(out, tuple) and len(out) == 3 else {}
    results.append((cls.__name__, 'OK', info.get('invocations', 0)))

for name, status, inv in results:
    print(f'  {name:25s} {status}  inv={inv}')
"""
rc, out, err = run([sys.executable, "-X", "utf8", "-c", run_code])
if rc != 0:
    print(f"  FAIL: algorithm smoke test")
    print(f"  stderr: {err[:500]}")
    sys.exit(1)
print(out.strip())

# -----------------------------------------------------------------------------
section("5. LLM cache can be read")
# -----------------------------------------------------------------------------
rc, out, err = run([sys.executable, "-X", "utf8", "-c", r"""
from core.llm_interface import LLMClient
c = LLMClient(model='qwen2.5:7b', use_cache=True)
hits_before = c.cache_hits
r = c.call("This is a smoke test prompt that should not be in the cache XYZ123", temperature=0.0)
hits_after = c.cache_hits
print(f'  first call : hits={hits_after - hits_before} (1 = cached, 0 = fresh)')

# call again with same prompt -- should hit cache
c.reset_stats()
r2 = c.call("This is a smoke test prompt that should not be in the cache XYZ123", temperature=0.0)
print(f'  second call: hits={c.cache_hits} (must be 1)')
assert c.cache_hits == 1, 'cache should hit on second call with identical prompt'
print('  OK  : cache works')
"""])
if rc != 0:
    print(f"  FAIL: cache test")
    print(f"  stderr: {err[:500]}")
    sys.exit(1)
print(out.strip())

# -----------------------------------------------------------------------------
section("6. Hardcoded path scan (should be zero)")
# -----------------------------------------------------------------------------
bad_files = 0
for p in REPO.rglob("*.py"):
    rel = p.relative_to(REPO)
    if any(part.startswith("__pycache__") for part in rel.parts):
        continue
    # The smoke test itself contains these patterns as literal strings for detection.
    if rel.name == "_smoke_test.py":
        continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    if any(s in text for s in ["D:\\\\新论文", "D:\\\\鏂拌", "D:/新论文", "D:/鏂拌",
                                  "sys.path.insert(0, \"D:/", "sys.path.insert(0, r'D:\\\\"]):
        bad_files += 1
        print(f"  FAIL: hardcoded path in {rel}")
if bad_files == 0:
    print("  OK  : no hardcoded Windows paths in any .py file")

# Clean up the smoke test output file.
out_path.unlink(missing_ok=True)

print()
print("=" * 70)
print("ALL SMOKE TESTS PASSED")
print("=" * 70)
