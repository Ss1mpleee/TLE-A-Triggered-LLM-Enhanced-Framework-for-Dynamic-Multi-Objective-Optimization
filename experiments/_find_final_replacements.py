"""Verify the 4 corrected SWEVO 2026 DOIs and find 13 remaining issues."""
import urllib.request
import json
import re
import time

# Verify 4 SWEVO 2026 DOIs (corrected)
VERIFY = [
    ('10.1016/j.swevo.2026.102358', 'huang2026knee-dmo'),
    ('10.1016/j.swevo.2026.102364', 'cao2026effective'),
    ('10.1016/j.swevo.2026.102366', 'zhang2026ga-gnn'),
    ('10.1016/j.swevo.2026.102360', 'ding2026sparse-bo'),
    ('10.1007/978-3-540-70928-2_60', 'deb2007dnsga'),
    ('10.1109/tcyb.2013.2245892', 'zhou2014pps'),
    ('10.1016/j.asoc.2024.111756', 'liu2017bandit-ea'),
]

print('=== Verify corrected DOIs ===')
for doi, key in VERIFY:
    try:
        req = urllib.request.Request(f'https://api.crossref.org/works/{doi}', headers={'User-Agent': 'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            msg = data.get('message', {})
            t = msg.get('title', [''])[0] if msg.get('title') else ''
            a = msg.get('author', [{}])[0].get('family', '') if msg.get('author') else ''
            y = msg.get('issued', {}).get('date-parts', [[0]])[0][0] if msg.get('issued') else 0
            j = msg.get('container-title', [''])[0] if msg.get('container-title') else ''
            print(f'  {key}: REAL')
            print(f'    {a} ({y}) | {j}')
            print(f'    "{t[:80]}"')
    except urllib.error.HTTPError as e:
        print(f'  {key}: {e.code} FABRICATED')
    except Exception as e:
        print(f'  {key}: ERROR {e}')
    time.sleep(0.3)
print()

# Now find replacements for the 13 unresolved
UNRESOLVED = [
    # (key, claimed_title, first_author, search_keywords)
    ('xu2026runtime', 'Runtime analysis of evolutionary algorithms for multiparty multiobjective optimization', 'Sun', 'multiparty multiobjective runtime'),
    ('tian2024predict-dmo', 'Transfer learning based dynamic multi-objective optimization: a survey', 'Tian', 'transfer learning dynamic multi-objective survey'),
    ('li2024knee-pareto', 'A knee-point based prediction strategy for dynamic multi-objective optimization', 'Li', 'knee point prediction dynamic multi-objective'),
    ('zhou2024survey', 'A survey on large language model-empowered evolutionary computation', 'Zhou', 'large language model evolutionary computation survey'),
    ('wang2023dmo', 'A unified framework for dynamic multi-objective optimization based on dynamic decomposition', 'Wang', 'dynamic decomposition multiobjective framework'),
    ('azevedo2023dmo', 'A survey on dynamic multi-objective optimization problems', 'Azevedo', 'dynamic multiobjective optimization problems survey'),
    ('azevedo2016dmo', 'Evolutionary computation for dynamic optimization problems: a survey', 'Azevedo', 'evolutionary computation dynamic optimization survey'),
    ('helbig2016dmo', 'Dynamic multi-objective optimization: a survey', 'Helbig', 'dynamic multiobjective optimization survey'),
    ('liu2024llm-pred', 'Large language model-empowered predictive evolutionary optimization for dynamic constrained optimization', 'Liu', 'large language model predictive evolutionary optimization'),
    ('tian2023transfer', 'A knee point-based evolutionary algorithm for multi-objective DEA cross-efficiency evaluation', 'Tian', 'knee point multiobjective DEA cross-efficiency'),
    ('li2023drl-dmo', 'A reinforcement learning-based adaptive operator selection for dynamic multi-objective optimization', 'Li', 'reinforcement learning adaptive operator dynamic multiobjective'),
    ('wang2017drl-moead', 'Decomposition-based evolutionary dynamic multiobjective optimization using a difference-based predictor', 'Wang', 'decomposition evolutionary dynamic multiobjective difference predictor'),
    ('sierra2014ucb', 'An evolutionary algorithm for multi-label classification using UCB-based operator selection', 'Da Silva', 'evolutionary multi-label classification UCB'),
    ('li2025dual-pred', 'An adaptive dual-domain prediction strategy based on second-order derivatives for dynamic multi-objective optimization', 'Li', 'adaptive dual-domain prediction dynamic multiobjective'),
]

print('=== Find replacements for 13 unresolved ===')
replacements = {}
for key, title, first_author, kw in UNRESOLVED:
    print(f'\n>>> {key} (search: "{kw}")')
    # Try multiple queries
    for query in [title, kw, f'{first_author} {kw}']:
        url = f'https://api.crossref.org/works?query.bibliographic={urllib.request.quote(query)}&rows=5'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'TLE-audit/1.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                items = data.get('message', {}).get('items', [])

                # Filter and score
                candidates = []
                for c in items[:5]:
                    if c.get('type') not in ('journal-article',):
                        continue
                    ctitle = c.get('title', [''])[0] if c.get('title') else ''
                    cauthor = c.get('author', [{}])[0].get('family', '') if c.get('author') else ''
                    cy = c.get('issued', {}).get('date-parts', [[0]])[0][0] if c.get('issued') else 0
                    cdoi = c.get('DOI', '')

                    if first_author.lower() not in cauthor.lower() and cauthor.lower() not in first_author.lower():
                        continue
                    # Title similarity
                    title_words = set(re.findall(r'\w+', title.lower()))
                    ctitle_words = set(re.findall(r'\w+', ctitle.lower()))
                    overlap = len(title_words & ctitle_words)
                    if overlap < 3:
                        continue
                    candidates.append({
                        'doi': cdoi,
                        'title': ctitle,
                        'author': cauthor,
                        'year': cy,
                        'journal': c.get('container-title', [''])[0] if c.get('container-title') else '',
                        'overlap': overlap,
                    })
                if candidates:
                    candidates.sort(key=lambda m: m['overlap'], reverse=True)
                    best = candidates[0]
                    print(f'    BEST: {best["author"]} ({best["year"]}) DOI={best["doi"]} overlap={best["overlap"]}')
                    print(f'    "{best["title"][:80]}"')
                    replacements[key] = best
                    break
        except Exception as e:
            pass
        time.sleep(0.3)
    else:
        print(f'    NO MATCH')
        replacements[key] = None

# Save
import json
with open(r'D:\新论文\实验\experiments\_final_replacements.json', 'w', encoding='utf-8') as f:
    json.dump({
        'verified_correct_doi': {k: doi for doi, k in VERIFY},
        'final_replacements': {k: v for k, v in replacements.items() if v},
        'still_no_replacement': [k for k in UNRESOLVED if not replacements.get(k)],
    }, f, indent=2, ensure_ascii=False)
print(f'\nSaved to _final_replacements.json')