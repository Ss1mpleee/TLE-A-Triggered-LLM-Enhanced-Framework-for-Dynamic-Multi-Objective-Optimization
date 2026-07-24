import json
from collections import defaultdict

data = json.load(open(r'D:\新论文\实验\results\raw\exp3_uav_v3.json', encoding='utf-8'))
print(f'Total records: {len(data)}')

# count unique (algo, n_uavs, seed) in v3
gb = {}
for r in data:
    gb.setdefault((r['algo'], r['n_uavs']), []).append(r['seed'])

# Expected: v2 had 5 algos x 5 seeds x 2 fleets = 50 (the FIRST 50 of v3)
# New runs: 5 algos x 25 new seeds (5-29) x 2 fleets = 250
# Total if all done: 300 records (50 from v2 + 250 new)
new_done = 0
for (a, nu), ss in sorted(gb.items()):
    new = [s for s in ss if s >= 5]
    new_done += len(new)
    print(f'  {a:25s} n_uavs={nu}: total {len(ss)} seeds, {len(new)} are new (>=5)')

print()
print(f'NEW runs done: {new_done} / 250 = {100*new_done/250:.1f}%')
print(f'Total records: {len(data)} (50 from v2 + {new_done} new = {50+new_done})')
print()

# Compute ETA based on actual run rates
# v2 was loaded at 09:05
# Now is later; CPU time = ~1900s = 31.7 min
import time
import os
mtime = os.path.getmtime(r'D:\新论文\实验\results\raw\uav30.log')
print(f'log last modified: {time.strftime("%H:%M:%S", time.localtime(mtime))}')

# Last 3 log lines with details
import os
print()
print('=== Log progress (last 5 [N/250] blocks) ===')
with open(r'D:\新论文\实验\results\raw\uav30.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()
# Find lines starting with [
idx = [i for i, l in enumerate(lines) if l.startswith('[')]
for i in idx[-5:]:
    print(f'  {lines[i].rstrip()}')
    if i+1 < len(lines):
        print(f'  {lines[i+1].rstrip()}')  # value=...
    if i+2 < len(lines):
        print(f'  {lines[i+2].rstrip()}')  # total elapsed
