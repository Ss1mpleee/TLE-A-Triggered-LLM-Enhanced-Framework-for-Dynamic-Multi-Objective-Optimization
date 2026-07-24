import json
from collections import defaultdict
data = json.load(open(r'D:\新论文\实验\results\raw\exp3_uav_v3.json', encoding='utf-8'))
print(f'Total runs in v3: {len(data)}')
g = {}
for r in data:
    g.setdefault((r['algo'], r['n_uavs']), []).append(r['seed'])
for (a,nu), ss in sorted(g.items()):
    print(f'  {a:25s} n_uavs={nu}: {len(ss)} seeds')

# Stat: TLE vs DE on 8-UAV with current data
import numpy as np
from scipy.stats import wilcoxon
tle_8 = [r['f1_value'] for r in data if r['algo']=='TLE' and r['n_uavs']==8]
de_8 = [r['f1_value'] for r in data if r['algo']=='DE' and r['n_uavs']==8]
if tle_8 and de_8:
    print()
    print(f'TLE 8-UAV: n={len(tle_8)}, mean={np.mean(tle_8):.1f}, std={np.std(tle_8):.1f}')
    print(f'DE  8-UAV: n={len(de_8)}, mean={np.mean(de_8):.1f}, std={np.std(de_8):.1f}')
    if len(tle_8) == len(de_8) and len(tle_8) > 1:
        try:
            w, p = wilcoxon(tle_8, de_8, alternative='greater')
            print(f'Wilcoxon TLE > DE one-sided: p={p:.4f}')
            print(f'Improvement: {100*(np.mean(tle_8)-np.mean(de_8))/np.mean(de_8):+.1f}%')
        except Exception as e:
            print(f'Wilcoxon failed: {e}')