"""Find real replacements for 22 problematic bib entries."""
import urllib.request
import json
import re
import time

# Each problematic entry: (bib_key, bib_title, bib_first_author, mode)
# mode = 'fabricated' = DOI 404
# mode = 'wrong_paper' = DOI resolves to different paper
# mode = 'author_mismatch' = title ok, authors off
# mode = 'title_mismatch' = encoding issue
ISSUES = [
    # FABRICATED (404)
    ('huang2026knee-dmo', 'A knee-guided prediction model oriented to population composition structures for dynamic multi-objective evolutionary optimization', 'Huang', 'fabricated'),
    ('cao2026effective', 'An effective auxiliary task for volumetric modulated arc therapy planning', 'Cao', 'fabricated'),
    ('zhang2026ga-gnn', 'Genetic algorithm-based robust graph convolutional network design leveraging node splitting and fusion', 'Zhang', 'fabricated'),
    ('ding2026sparse-bo', 'Sparse Bayesian optimization with a sequential coordinate search for structural finite element model updating using uncertain modal data', 'Ding', 'fabricated'),
    ('xu2026runtime', 'Runtime analysis of evolutionary algorithms for multiparty multiobjective optimization', 'Sun', 'fabricated'),
    ('tian2024predict-dmo', 'Transfer learning based dynamic multi-objective optimization: a survey', 'Tian', 'fabricated'),
    ('li2024knee-pareto', 'A knee-point based prediction strategy for dynamic multi-objective optimization', 'Li', 'fabricated'),
    ('zhou2024survey', 'A survey on large language model-empowered evolutionary computation', 'Zhou', 'fabricated'),
    ('wang2023dmo', 'A unified framework for dynamic multi-objective optimization based on dynamic decomposition', 'Wang', 'fabricated'),
    ('azevedo2023dmo', 'A survey on dynamic multi-objective optimization problems', 'Azevedo', 'fabricated'),
    ('azevedo2016dmo', 'Evolutionary computation for dynamic optimization problems: a survey', 'Azevedo', 'fabricated'),
    ('helbig2016dmo', 'Dynamic multi-objective optimization: a survey', 'Helbig', 'fabricated'),
    ('deb2007dnsga', 'Dynamic multi-objective optimization and decision-making using modified NSGA-II: a case study on hydro-thermal power scheduling', 'Deb', 'fabricated'),
    ('zhou2014pps', 'A population prediction strategy for evolutionary dynamic multiobjective optimization', 'Zhou', 'fabricated'),
    # WRONG_PAPER
    ('liu2024llm-pred', 'Large language model-empowered predictive evolutionary optimization for dynamic constrained optimization', 'Liu', 'wrong_paper'),
    ('tian2023transfer', 'A knee point-based evolutionary algorithm for multi-objective DEA cross-efficiency evaluation', 'Tian', 'wrong_paper'),
    ('li2023drl-dmo', 'A reinforcement learning-based adaptive operator selection for dynamic multi-objective optimization', 'Li', 'wrong_paper'),
    ('wang2017drl-moead', 'Decomposition-based evolutionary dynamic multiobjective optimization using a difference-based predictor', 'Wang', 'wrong_paper'),
    ('sierra2014ucb', 'An evolutionary algorithm for multi-label classification using UCB-based operator selection', 'Da Silva', 'wrong_paper'),
    ('liu2017bandit-ea', 'An adaptive UCB-based selection for evolutionary multi-objective optimization', 'Liu', 'wrong_paper'),
    # AUTHOR_MISMATCH
    ('li2025dual-pred', 'An adaptive dual-domain prediction strategy based on second-order derivatives for dynamic multi-objective optimization', 'Li', 'author_mismatch'),
    # TITLE_MISMATCH (encoding)
    ('storn1997de', 'Differential evolution—a simple and efficient heuristic for global optimization over continuous spaces', 'Storn', 'title_mismatch'),
]

# Use crossref search to find real candidates
def search_crossref(query, rows=5):
    url = f'https://api.crossref.org/works?query.bibliographic={urllib.request.quote(query)}&rows={rows}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get('message', {}).get('items', [])
    except Exception as e:
        return []

# Verify a DOI directly
def verify_doi(doi):
    url = f'https://api.crossref.org/works/{doi}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get('message', {})
    except:
        return None

print('=' * 100)
print('SEARCHING FOR REAL REPLACEMENTS')
print('=' * 100)

replacements = {}
for key, title, first_author, mode in ISSUES:
    print(f'\n>>> Searching for: {key}')
    print(f'    Claimed title: {title}')
    print(f'    Mode: {mode}')

    # Try multiple search queries
    candidates = []
    for q in [title, f'{title} {first_author}', f'{first_author} {title.split()[0]} dynamic multi-objective']:
        cands = search_crossref(q, rows=5)
        candidates.extend(cands)
        if len(candidates) >= 5:
            break

    # Deduplicate
    seen = set()
    unique_cands = []
    for c in candidates:
        doi = c.get('DOI', '')
        if doi and doi not in seen:
            seen.add(doi)
            unique_cands.append(c)

    # Filter to journal-article type and title-similar
    title_words = set(re.findall(r'\w+', title.lower()))
    matches = []
    for c in unique_cands[:10]:
        ctype = c.get('type', '')
        if ctype not in ('journal-article', 'book-chapter', 'proceedings-article'):
            continue
        ctitle = c.get('title', [''])[0] if c.get('title') else ''
        ctitle_words = set(re.findall(r'\w+', ctitle.lower()))
        # Word overlap
        overlap = len(title_words & ctitle_words)
        if overlap < 4:  # too few common words
            continue
        # First author
        cauthor = c.get('author', [{}])[0].get('family', '') if c.get('author') else ''
        if first_author.lower() not in cauthor.lower() and cauthor.lower() not in first_author.lower():
            continue
        matches.append({
            'doi': c.get('DOI', ''),
            'title': ctitle,
            'author': cauthor,
            'year': c.get('issued', {}).get('date-parts', [[0]])[0][0] if c.get('issued') else 0,
            'journal': c.get('container-title', [''])[0] if c.get('container-title') else '',
            'volume': c.get('volume', ''),
            'pages': c.get('page', ''),
        })

    if matches:
        # Sort by year desc and overlap
        matches.sort(key=lambda m: (m.get('year', 0), len(set(re.findall(r'\w+', m['title'].lower())) & title_words)), reverse=True)
        best = matches[0]
        print(f'    BEST MATCH: {best["author"]} ({best["year"]})')
        print(f'    Title: {best["title"][:80]}')
        print(f'    DOI: {best["doi"]}')
        replacements[key] = best
    else:
        print(f'    NO MATCH FOUND')
        replacements[key] = None

    time.sleep(0.4)

print()
print('=' * 100)
print('SUMMARY OF REPLACEMENTS')
print('=' * 100)
for key, _, _, mode in ISSUES:
    r = replacements.get(key)
    if r:
        print(f'  {key}: FOUND {r["author"]} ({r["year"]}) DOI={r["doi"]}')
    else:
        print(f'  {key}: NO REPLACEMENT - need to REMOVE')

# Save results
import json
with open(r'D:\新论文\实验\experiments\_replacement_candidates.json', 'w', encoding='utf-8') as f:
    json.dump({
        'issues': [{'key': k, 'title': t, 'author': a, 'mode': m} for k, t, a, m in ISSUES],
        'replacements': {k: v for k, v in replacements.items() if v},
        'no_replacement': [k for k in ISSUES if not replacements.get(k)],
    }, f, indent=2, ensure_ascii=False)
print(f'\nSaved to _replacement_candidates.json')