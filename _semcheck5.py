import json
from collections import defaultdict
with open(r'results\raw\exp7_ablation_combined.json', encoding='utf-8') as f:
    abl = json.load(f)
by_vp = defaultdict(list)
for r in abl:
    by_vp[(r['version'], r['problem'])].append(r)

# V1_entropy on DF1
v1_df1 = by_vp.get(('V1_entropy', 'DF1'), [])
print(f'V1_entropy DF1: n={len(v1_df1)}')
for r in v1_df1:
    inv = r['invocations']
    igd = r['igd']
    print(f'  inv={inv} igd={igd:.4f}')

# V1_entropy overall
print('\nV1_entropy per-problem invocations (mean):')
for p in ['DF1','DF2','DF3','DF4','DF5','DF6','DF7','DF8','DF9','DF10','DF11','DF12','DF13','DF14']:
    invs = [r['invocations'] for r in by_vp.get(('V1_single', p), [])]
    if invs:
        print(f'  {p}: mean_inv={sum(invs)/len(invs):.3f} max={max(invs)}')

# V0 always-trigger on all problems (should be 50)
print('\nV0_baseline per-problem invocations:')
for p in ['DF1','DF2','DF3','DF4','DF5','DF6','DF7','DF8','DF9','DF10','DF11','DF12','DF13','DF14']:
    invs = [r['invocations'] for r in by_vp.get(('V0_baseline', p), [])]
    if invs:
        print(f'  {p}: mean_inv={sum(invs)/len(invs):.2f} max={max(invs)}')

# V2_double per-problem
print('\nV2_double per-problem invocations:')
for p in ['DF1','DF2','DF3','DF4','DF5','DF6','DF7','DF8','DF9','DF10','DF11','DF12','DF13','DF14']:
    invs = [r['invocations'] for r in by_vp.get(('V2_double', p), [])]
    if invs:
        print(f'  {p}: mean_inv={sum(invs)/len(invs):.2f} max={max(invs)}')

# Verify V2 stats: 11.3 mean / 13.0 median
v2_all = []
for p in ['DF1','DF2','DF3','DF4','DF5','DF6','DF7','DF8','DF9','DF10','DF11','DF12','DF13','DF14']:
    invs = [r['invocations'] for r in by_vp.get(('V2_double', p), [])]
    v2_all.extend(invs)
print(f'\nV2_double: total {len(v2_all)} values, mean={sum(v2_all)/len(v2_all):.3f}, median={sorted(v2_all)[len(v2_all)//2]}, max={max(v2_all)}')
print(f'V3_triple: total {len([r for k in by_vp for r in by_vp[k] if k[0]=="V3_triple"])} values')

# All V3 invocations
v3_all = []
for p in ['DF1','DF2','DF3','DF4','DF5','DF6','DF7','DF8','DF9','DF10','DF11','DF12','DF13','DF14']:
    invs = [r['invocations'] for r in by_vp.get(('V3_triple', p), [])]
    v3_all.extend(invs)
print(f'V3_triple: mean={sum(v3_all)/len(v3_all):.3f} median={sorted(v3_all)[len(v3_all)//2]} max={max(v3_all)}')

# 30.5% of T3's budget, 22.7% of T0's budget
print(f'\n11.3 / 38.6 = {11.3/38.6*100:.1f}%')
print(f'11.3 / 50.0 = {11.3/50.0*100:.1f}%')
