"""Find more 2024-2025 LLM-EC and bandit papers."""
import urllib.parse, urllib.request, json

queries = [
    # LLM-EC 2024-2025 in journals
    ('xie2025llm-surrogate', 'Xie Large Language Model-Driven Surrogate-Assisted Evolutionary Algorithm 2025 arXiv'),
    ('chen2025llm-cea', 'Chen Large Language Model-assisted Evolutionary Algorithm Expensive Constrained GECCO 2025'),
    ('llm2024knee', 'LLM knee point multi-objective evolutionary 2024'),
    ('llm2024psomop', 'LLM PSO multi-objective parameter 2024'),
    ('llm2024metaheuristic', 'LLM metaheuristic design automated 2024'),
    # Bandit 2024-2025
    ('bandit2024budget', 'multi-armed bandit budget allocation evolutionary optimization 2024'),
    ('lattimore2020bandit', 'Lattimore Bandit Algorithms textbook 2020'),
    # ECJ 2024
    ('ecj2024dmo', 'Evolutionary Computation 2024 dynamic multi-objective'),
    # IEEE TEVC 2024-2025 DMO specific
    ('tevc2024dmo', 'IEEE TEVC 2024 dynamic multi-objective evolutionary algorithm'),
    # ASOC 2024-2025 DMO
    ('asoc2024dmo', 'Applied Soft Computing 2024 dynamic multi-objective evolutionary'),
    # Information Sciences 2024 DMO
    ('is2024dmo', 'Information Sciences 2024 dynamic multi-objective prediction'),
    # KBS 2024 DMO
    ('kbs2024dmo', 'Knowledge-Based Systems 2024 dynamic multi-objective'),
]

def crossref_search(q, n=3):
    try:
        url = f'https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(q)}&rows={n}'
        req = urllib.request.Request(url, headers={'User-Agent':'TLE-audit/1.0 (mailto:test@test.com)'})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode('utf-8'))
            return d.get('message',{}).get('items',[])
    except: return []

def arxiv_check(aid):
    try:
        req = urllib.request.Request(f'http://export.arxiv.org/api/query?id_list={aid}', headers={'User-Agent':'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read().decode('utf-8')
            tm = re.search(r'<title>(.*?)</title>', data, re.DOTALL)
            am = re.findall(r'<author>\s*<name>(.*?)</name>', data)
            cm = re.search(r'<published>(.*?)</published>', data)
            return tm.group(1)[:60] if tm else '?', am[:3], cm.group(1)[:10] if cm else '?'
    except: return None, None, None

import re

for key, q in queries:
    print(f'=== {key} ===')
    if 'arxiv' in q.lower():
        m = re.search(r'arxiv[:\s]*(\d{4}\.\d{4,5})', q, re.I)
        if m:
            t, au, d = arxiv_check(m.group(1))
            print(f'  arXiv {m.group(1)}: {t}')
            print(f'  Authors: {au} | Date: {d}')
    else:
        items = crossref_search(q, 2)
        if not items: print('  NO RESULTS'); continue
        for it in items:
            t = it.get('title',[''])[0][:65]
            y = (it.get('issued',{}).get('date-parts',[[0]])[0][0]
                 or it.get('published-print',{}).get('date-parts',[[0]])[0][0])
            doi = it.get('DOI','')
            j = (it.get('container-title',[''])[0] if it.get('container-title') else '')[:35]
            au = ', '.join(f"{a.get('family','')}" for a in it.get('author',[])[:2])
            # Filter: must be relevant
            tk = (t+au+j).lower()
            relevant = False
            if any(k in tk for k in ['dynamic','multi-objectiv','multiobjective','moea','evolution','pareto','genetic','differential','llm','large language','bandit','surrogate','knee','memetic']):
                if y >= 2023:
                    relevant = True
            mark = '✓' if relevant else ' '
            print(f'  [{mark} {y}] {au} | DOI: {doi}')
            print(f'        {j}')
            print(f'        {t}')
    print()
