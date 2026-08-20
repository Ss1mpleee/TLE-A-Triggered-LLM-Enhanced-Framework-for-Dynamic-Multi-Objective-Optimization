"""semcheck9: Comprehensive paper claim validation for SWEVO review."""
import json
from collections import defaultdict

# Cache hits analysis
print('='*60)
print('CACHE HITS ANALYSIS')
print('='*60)
total_cache_hits = 0
for f, label in [
    ('results/raw/sec_main_v3.json', 'main'),
    ('results/raw/exp6_cross_llm_n14.json', 'cross-LLM'),
    ('results/raw/exp7_ablation_combined.json', 'ablation'),
]:
    with open(f, encoding='utf-8') as fp:
        d = json.load(fp)
    n = len(d)
    n_cache = sum(1 for r in d if r.get('cache_hits', 0) > 0)
    cache_total = sum(r.get('cache_hits', 0) for r in d)
    total_cache_hits += cache_total
    print(f'  {label:12s}: {n} runs, {n_cache} use cache, {cache_total} total cache_hits')
print(f'  TOTAL cache_hits: {total_cache_hits}')

# Fresh LLM calls
print()
print('FRESH LLM CALLS (cache_hits=0):')
for f, label in [
    ('results/raw/sec_main_v3.json', 'main'),
    ('results/raw/exp6_cross_llm_n14.json', 'cross-LLM'),
    ('results/raw/exp7_ablation_combined.json', 'ablation'),
]:
    with open(f, encoding='utf-8') as fp:
        d = json.load(fp)
    fresh_total = sum(r['invocations'] - r.get('cache_hits', 0) for r in d)
    print(f'  {label}: {fresh_total} fresh LLM calls')

# LLM cache files
import os
cache_dir = 'results/llm_cache'
n_files = len([f for f in os.listdir(cache_dir) if f.endswith('.json')])
print(f'\nCache files in {cache_dir}: {n_files}')

# Main table data
print()
print('='*60)
print('MAIN TABLE (14 problems, 6 algos, n=30)')
print('='*60)
with open('results/raw/sec_main_v3.json', encoding='utf-8') as f:
    main = json.load(f)
for algo in ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']:
    n = sum(1 for r in main if r['algo'] == algo)
    print(f'  {algo:24s} {n} runs')
print(f'  TOTAL: {len(main)} runs')
