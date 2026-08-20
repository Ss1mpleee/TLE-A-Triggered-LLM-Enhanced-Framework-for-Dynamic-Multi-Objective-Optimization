import json, numpy as np
with open(r'results\raw\sec_main_v3.json', encoding='utf-8') as f:
    main = json.load(f)

ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']
PROBS = ['DF1', 'DF2', 'DF3', 'DF4', 'DF5', 'DF6', 'DF7']

print('ACTUAL 30-seed mean (no filter):')
for algo in ALGOS:
    means = []
    means_filt = []
    for prob in PROBS:
        rs = [r for r in main if r['algo'] == algo and r['problem'] == prob]
        igds = [r['igd'] for r in rs if r.get('igd') is not None]
        igds_filt = [g for g in igds if g < 1e3]
        if igds:
            means.append(np.mean(igds))
            means_filt.append(np.mean(igds_filt) if igds_filt else 0)
    print(f'  {algo:24s} 7mean_no_filt={np.mean(means):.4f}  7mean_filt={np.mean(means_filt):.4f}  median_no_filt={np.median(means):.4f}')

# Also try with all 8 2-obj problems
PROBS8 = ['DF1', 'DF2', 'DF3', 'DF4', 'DF5', 'DF6', 'DF7', 'DF8']
print('\nACTUAL 30-seed mean across 8 2-obj problems:')
for algo in ALGOS:
    means = []
    means_filt = []
    for prob in PROBS8:
        rs = [r for r in main if r['algo'] == algo and r['problem'] == prob]
        igds = [r['igd'] for r in rs if r.get('igd') is not None]
        igds_filt = [g for g in igds if g < 1e3]
        if igds:
            means.append(np.mean(igds))
            means_filt.append(np.mean(igds_filt) if igds_filt else 0)
    print(f'  {algo:24s} 8mean_filt={np.mean(means_filt):.4f}  median_8={np.median(means):.4f}')

# Median of 7 means
print('\nMedian of 7 means:')
for algo in ALGOS:
    means = []
    for prob in PROBS:
        rs = [r for r in main if r['algo'] == algo and r['problem'] == prob]
        igds = [r['igd'] for r in rs if r.get('igd') is not None]
        if igds:
            means.append(np.mean(igds))
    print(f'  {algo:24s} median={np.median(means):.4f}')

# Also test if paper used 6 problems (excl DF2)
print('\n6-mean (excl DF2):')
for algo in ALGOS:
    means = []
    for prob in ['DF1', 'DF3', 'DF4', 'DF5', 'DF6', 'DF7']:
        rs = [r for r in main if r['algo'] == algo and r['problem'] == prob]
        igds = [r['igd'] for r in rs if r.get('igd') is not None]
        if igds:
            means.append(np.mean(igds))
    print(f'  {algo:24s} 6mean={np.mean(means):.4f}')

# Test: mean of 6 means excl DF4 (well-conditioned) and DF2 (outlier)
print('\n5-mean (excl DF2, DF4):')
for algo in ALGOS:
    means = []
    for prob in ['DF1', 'DF3', 'DF5', 'DF6', 'DF7']:
        rs = [r for r in main if r['algo'] == algo and r['problem'] == prob]
        igds = [r['igd'] for r in rs if r.get('igd') is not None]
        if igds:
            means.append(np.mean(igds))
    print(f'  {algo:24s} 5mean={np.mean(means):.4f}')

# Check paper table values vs computed (filter IGD<1e3)
print('\n--- Mean IGD per algo (filter IGD<1e3, 7 problems) ---')
print('Algorithm               paper    actual  delta')
for algo in ALGOS:
    means = []
    for prob in PROBS:
        rs = [r for r in main if r['algo'] == algo and r['problem'] == prob]
        igds = [r['igd'] for r in rs if r.get('igd') is not None and r['igd'] < 1e3]
        if igds:
            means.append(np.mean(igds))
    # Paper mean IGD from table
    paper_mean = {'DE': 0.5475, 'DE-LM-static-trigger': 0.6334, 'PPS-DMOEA': 0.5419,
                  'DNSGA-II-A': 0.4105, 'MOEA/DD': 0.4412, 'TLE': 0.6405}[algo]
    print(f'  {algo:24s} {paper_mean:.4f}  {np.mean(means):.4f}  {np.mean(means) - paper_mean:+.4f}')
