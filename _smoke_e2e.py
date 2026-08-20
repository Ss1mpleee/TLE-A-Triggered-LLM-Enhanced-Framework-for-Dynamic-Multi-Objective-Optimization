#!/usr/bin/env python3
"""End-to-end TLE smoke test (1 seed, 5 gen, with cache)."""
import os
import sys
import json
from pathlib import Path

REPO = Path(r'D:\新论文\实验')
sys.path.insert(0, str(REPO))

# Run via subprocess to mimic shell behavior
import subprocess

env = os.environ.copy()
env['PYTHONPATH'] = str(REPO)

cmd = [sys.executable, '-m', 'proposed.run_tle',
       '--problem', 'DF1', '--seeds', '0',
       '--pop-size', '10', '--max-gen', '5',
       '--output', str(REPO / 'results' / 'raw' / 'smoke_test.json')]

print(f"Running: {' '.join(cmd)}")
print(f"CWD: {REPO}")
print(f"PYTHONPATH: {env['PYTHONPATH']}")
print()

result = subprocess.run(cmd, cwd=str(REPO), env=env,
                        capture_output=True, text=True, timeout=120)
print("=== STDOUT (last 30 lines) ===")
for line in result.stdout.split('\n')[-30:]:
    print(f"  {line}")
if result.stderr:
    print("=== STDERR (last 20 lines) ===")
    for line in result.stderr.split('\n')[-20:]:
        print(f"  {line}")
print(f"\nReturn code: {result.returncode}")

# Read output
out = REPO / 'results' / 'raw' / 'smoke_test.json'
if out.exists():
    print(f"\n=== Output JSON ===")
    with open(out, 'r', encoding='utf-8') as f:
        d = json.load(f)
    print(f"  type: {type(d).__name__}")
    if isinstance(d, list):
        print(f"  records: {len(d)}")
        if d:
            r = d[0]
            print(f"  first record keys: {list(r.keys())}")
            print(f"  algo: {r.get('algo', '?')}")
            print(f"  prob: {r.get('problem', r.get('prob', '?'))}")
            print(f"  seed: {r.get('seed', '?')}")
            igd = r.get('igd', None)
            if isinstance(igd, (int, float)):
                print(f"  igd: {igd:.6f}")
            else:
                print(f"  igd: {igd}")
            print(f"  invocations: {r.get('invocations', '?')}")
            print(f"  elapsed: {r.get('elapsed_sec', '?')}s")
    # Clean up
    out.unlink()
    print(f"\n  (cleaned up {out.name})")
else:
    print(f"\n  Output file {out} not created")
