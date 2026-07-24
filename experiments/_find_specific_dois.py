"""Find actual DOIs for Lin 2024 and Ge 2024/2025 DMO papers."""
import urllib.parse, urllib.request, json

queries = [
    ('lin2024kt-dmo', 'Dynamic Multiobjective Evolutionary Optimization via Knowledge Transfer Maintenance Qiuzhen Lin IEEE Transactions Systems Man Cybernetics 2024'),
    ('ge2025prob', 'Ge dynamic multi-objective optimization algorithm probability-driven prediction correlation-guided individual transfer Journal Supercomputing 2025'),
    ('ge2024maha', 'Ge dynamic multi-objective evolutionary algorithm Mahalanobis distance correlation guided'),
    ('peng2024ab', 'Hu Peng adaptive boosting dynamic multi-objective SWEVO 2024'),
    ('hu2024change', 'new framework change response dynamic multi-objective optimization Zheng 2024'),
    ('liu2024dual', 'Liu Tianyu dual-space prediction dynamic multiobjective Evolutionary Computation 2026'),
    ('yan2025dms', 'Yan indicator multi-objective evolutionary algorithm improved gaussian SWEVO 2025'),
    ('zhang2024trans', 'transfer learning dynamic multi-objective evolutionary 2024'),
    ('azevedo2023dmo', 'Azevedo dynamic multi-objective 2023'),
    ('helbig2022dmo', 'Helbig challenges dynamic multi-objective real-world 2022'),
]

def crossref_search(q, n=2):
    try:
        url = f'https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(q)}&rows={n}'
        req = urllib.request.Request(url, headers={'User-Agent':'TLE-audit/1.0 (mailto:test@test.com)'})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode('utf-8'))
            items = d.get('message',{}).get('items',[])
            return items
    except: return []

for key, q in queries:
    items = crossref_search(q, 2)
    print(f'=== {key} ===')
    if not items:
        print('  NO RESULTS')
    for it in items:
        t = it.get('title',[''])[0][:65]
        y = (it.get('issued',{}).get('date-parts',[[0]])[0][0]
             or it.get('published-print',{}).get('date-parts',[[0]])[0][0])
        doi = it.get('DOI','')
        j = (it.get('container-title',[''])[0] if it.get('container-title') else '')[:35]
        au = ', '.join(f"{a.get('family','')}" for a in it.get('author',[])[:2])
        # Filter: must be DMO / MOEA / EC related (not unrelated biomedical etc)
        score = 0
        tk = (t+au).lower()
        for kw in ['dynamic', 'multi-objectiv', 'multiobjective', 'moea', 'evolutionary', 'optimization', 'pareto', 'genetic', 'differential']:
            if kw in tk: score += 1
        marker = '✓' if score >= 2 and y >= 2023 else '✗'
        print(f'  [{marker} {y}] {au} | DOI: {doi}')
        print(f'        {j}')
        print(f'        {t}')
    print()
