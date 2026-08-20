"""semcheck6: find the correct mean IGD formula that matches paper."""
import json
import numpy as np
from collections import defaultdict

with open(r'results\raw\sec_main_v3.json', encoding='utf-8') as f:
    main = json.load(f)

ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']
PROBS = ['DF1', 'DF2', 'DF3', 'DF4', 'DF5', 'DF6', 'DF7']
PROBS_8 = ['DF1', 'DF2', 'DF3', 'DF4', 'DF5', 'DF6', 'DF7', 'DF8']
PROBS_14 = ['DF1', 'DF2', 'DF3', 'DF4', 'DF5', 'DF6', 'DF7', 'DF8', 'DF9', 'DF10', 'DF11', 'DF12', 'DF13', 'DF14']

PAPER = {
    'DE': (0.5475, 0.55, 0),         # mean_IGD, IGD/1000, LLM_calls
    'DE-LM-static-trigger': (0.6334, 39.59, 16),
    'PPS-DMOEA': (0.5419, 0.54, 0),
    'DNSGA-II-A': (0.4105, 0.41, 0),
    'MOEA/DD': (0.4412, 0.44, 0),
    'TLE': (0.6405, 16.85, 38),
}

# Gather per (algo, problem) statistics
stats = {}
for algo in ALGOS:
    for prob in PROBS_14:
        rs = [r for r in main if r['algo']==algo and r['problem']==prob]
        igds = [r['igd'] for r in rs if r.get('igd') is not None]
        igds_filt = [g for g in igds if g < 1e3]
        invs = [r['invocations'] for r in rs if r.get('invocations') is not None]
        if rs:
            stats[(algo, prob)] = {
                'mean': np.mean(igds) if igds else 0,
                'mean_filt': np.mean(igds_filt) if igds_filt else 0,
                'median': np.median(igds) if igds else 0,
                'median_filt': np.median(igds_filt) if igds_filt else 0,
                'inv_mean': np.mean(invs) if invs else 0,
                'n': len(igds),
                'n_cat': len(igds) - len(igds_filt),
            }

print('=== TEST 1: 6-mean (excl DF2) of mean (filter<1e3) ===')
for algo in ALGOS:
    means = []
    inv_means = []
    for prob in ['DF1', 'DF3', 'DF4', 'DF5', 'DF6', 'DF7']:
        means.append(stats[(algo, prob)]['mean_filt'])
        inv_means.append(stats[(algo, prob)]['inv_mean'])
    m = np.mean(means)
    inv = np.mean(inv_means)
    igd_1000 = m * 1000 / max(inv, 1) if inv > 0 else m
    paper_m, paper_1000, paper_inv = PAPER[algo]
    print(f'  {algo:24s} 6mean_filt={m:.4f} inv={inv:.2f} IGD/1000={igd_1000:.2f}  paper: {paper_m:.4f}, {paper_1000:.2f}, {paper_inv}')

print('\n=== TEST 2: 7-mean (incl DF2) of mean (filter<1e3) ===')
for algo in ALGOS:
    means = []
    inv_means = []
    for prob in PROBS:
        means.append(stats[(algo, prob)]['mean_filt'])
        inv_means.append(stats[(algo, prob)]['inv_mean'])
    m = np.mean(means)
    inv = np.mean(inv_means)
    igd_1000 = m * 1000 / max(inv, 1) if inv > 0 else m
    print(f'  {algo:24s} 7mean_filt={m:.4f} inv={inv:.2f} IGD/1000={igd_1000:.2f}')

print('\n=== TEST 3: 6-mean of medians (excl DF2) ===')
for algo in ALGOS:
    meds = []
    inv_means = []
    for prob in ['DF1', 'DF3', 'DF4', 'DF5', 'DF6', 'DF7']:
        meds.append(stats[(algo, prob)]['median_filt'])
        inv_means.append(stats[(algo, prob)]['inv_mean'])
    m = np.mean(meds)
    inv = np.mean(inv_means)
    igd_1000 = m * 1000 / max(inv, 1) if inv > 0 else m
    print(f'  {algo:24s} 6-median-mean={m:.4f} inv={inv:.2f} IGD/1000={igd_1000:.2f}')

print('\n=== TEST 4: 7-mean of medians (incl DF2) ===')
for algo in ALGOS:
    meds = []
    inv_means = []
    for prob in PROBS:
        meds.append(stats[(algo, prob)]['median_filt'])
        inv_means.append(stats[(algo, prob)]['inv_mean'])
    m = np.mean(meds)
    inv = np.mean(inv_means)
    igd_1000 = m * 1000 / max(inv, 1) if inv > 0 else m
    print(f'  {algo:24s} 7-median-mean={m:.4f} inv={inv:.2f} IGD/1000={igd_1000:.2f}')

# Now: what about 18.9 / 44.9?
print('\n=== TEST 5: median across 14 problems x 30 seeds (overall median) ===')
for algo in ALGOS:
    all_igds = []
    all_invs = []
    for prob in PROBS_14:
        rs = [r for r in main if r['algo']==algo and r['problem']==prob]
        igds = [r['igd'] for r in rs if r.get('igd') is not None and r['igd'] < 1e3]
        invs = [r['invocations'] for r in rs if r.get('invocations') is not None]
        all_igds.extend(igds)
        all_invs.extend(invs)
    m_overall = np.median(all_igds)  # median of all 14*30=420 IGDs
    inv = np.mean(all_invs)
    igd_1000 = m_overall * 1000 / max(inv, 1) if inv > 0 else m_overall
    print(f'  {algo:24s} overall_median={m_overall:.4f} inv={inv:.2f} IGD/1000={igd_1000:.2f}')

# Paper §5.5 line 723 says:
# TLE 18.9, DE-LM-static 44.9, TLE is 2.37x better
# 18.9 / 38.6 = 0.4895 (so TLE overall median ≈ 0.49)
# 44.9 / 16.6 = 2.704 (so DE-LM-static overall median ≈ 2.70? That's huge)
# 0.49 * 1000 / 38 = 12.9, not 18.9
# 18.9 = X * 1000 / 38, X = 0.7182
# 44.9 = Y * 1000 / 16, Y = 0.7184
# So paper TLE and DE-LM-static IGD stats that give 18.9/44.9 are BOTH ≈ 0.72
# This could be overall mean (incl 3-obj with high values like DF10 40)
# TLE 14 mean = 185.0364 (way too high due to DF10 39.6)
# Hmm, that doesn't work either

# Let me look at 8-obj mean: only DF1-DF8
print('\n=== TEST 6: 8-obj mean (incl DF8) ===')
for algo in ALGOS:
    means = []
    inv_means = []
    for prob in PROBS_8:
        means.append(stats[(algo, prob)]['mean_filt'])
        inv_means.append(stats[(algo, prob)]['inv_mean'])
    m = np.mean(means)
    inv = np.mean(inv_means)
    print(f'  {algo:24s} 8mean_filt={m:.4f} inv={inv:.2f}')

# Maybe paper used 14-problem median
print('\n=== TEST 7: median across 7 problem means ===')
for algo in ALGOS:
    means = []
    for prob in PROBS:
        means.append(stats[(algo, prob)]['mean_filt'])
    m = np.median(means)
    print(f'  {algo:24s} median_of_7_means={m:.4f}')

# How about median across 14*30 sorted? That's the overall median above
# What if it's the median of the 14 problem-medians?
print('\n=== TEST 8: median of 14 problem medians (for 18.9 calc) ===')
for algo in ALGOS:
    meds = []
    for prob in PROBS_14:
        meds.append(stats[(algo, prob)]['median_filt'])
    m = np.median(meds)
    inv_means = [stats[(algo, p)]['inv_mean'] for p in PROBS_14]
    inv = np.mean(inv_means)
    igd_1000 = m * 1000 / max(inv, 1) if inv > 0 else m
    print(f'  {algo:24s} median_of_14_medians={m:.4f} inv={inv:.2f} IGD/1000={igd_1000:.2f}')
