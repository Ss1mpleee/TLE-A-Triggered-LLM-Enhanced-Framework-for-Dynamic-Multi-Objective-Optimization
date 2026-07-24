"""Combine B6 + B3 + v3 data into one master file."""
import json

v3 = json.load(open(r'D:\新论文\实验\results\raw\exp3_uav_v3.json', encoding='utf-8'))
b6 = json.load(open(r'D:\新论文\实验\results\raw\exp3_uav_b6.json', encoding='utf-8'))
b3 = json.load(open(r'D:\新论文\实验\results\raw\exp3_uav_b3.json', encoding='utf-8'))

# Add B6 16/32-UAV (algorithmic = DE, DNSGA-II-A, TLE)
b6_new = [r for r in b6 if r['n_uavs'] in (16, 32) and r['algo'] in ('DE', 'DNSGA-II-A', 'TLE')]

# Add all of B3 (ablation)
b3_new = list(b3)

print(f'v3 baseline: {len(v3)}')
print(f'B6 (16/32 main algos): {len(b6_new)}')
print(f'B3 ablation: {len(b3_new)}')

# Merge: dedupe by (algo, n_uavs, seed)
seen = set()
combined = []
for r in v3:
    key = (r['algo'], r['n_uavs'], r['seed'])
    if key not in seen:
        seen.add(key)
        combined.append(r)
for r in b6_new + b3_new:
    key = (r['algo'], r['n_uavs'], r['seed'])
    if key not in seen:
        seen.add(key)
        combined.append(r)

print(f'Combined total: {len(combined)}')

# Save
json.dump(combined, open(r'D:\新论文\实验\results\raw\exp3_uav_combined.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('Saved to exp3_uav_combined.json')