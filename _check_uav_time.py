import json
import numpy as np
data = json.load(open(r'D:\新论文\实验\results\raw\exp3_uav_v2.json', encoding='utf-8'))
for a in ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'TLE']:
    rs = [r for r in data if r['algo']==a]
    avg = np.mean([r['elapsed_sec'] for r in rs])
    tot = sum(r['elapsed_sec'] for r in rs)
    print(f'{a:25s}: {avg:.1f}s avg, {tot:.0f}s total for 10 runs')

# Estimate for 30 seeds × 2 fleets × 5 algos
total_time_per_seed = sum(np.mean([r['elapsed_sec'] for r in data if r['algo']==a]) for a in ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'TLE'])
print()
print(f'Estimated time for 5 algos x 30 seeds x 2 fleets = 300 runs')
print(f'  at {total_time_per_seed:.0f}s/seed (5 algos, 2 fleets) = {300*total_time_per_seed/3600:.1f} hours')