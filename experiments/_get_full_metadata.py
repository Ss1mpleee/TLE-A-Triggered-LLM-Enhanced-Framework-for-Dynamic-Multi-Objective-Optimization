"""Get full metadata for 4 replacement papers."""
import urllib.request
import json

DOIS = {
    'liu2024llm-pred': '10.1145/3787965',  # ACM LLM-aided MOEA
    'wang2017drl-moead': '10.1016/j.swevo.2020.100668',  # Wan 2020 SWEVO
    'li2025dual-pred': '10.1162/evco.a.393',  # Liu 2026 ECJ dual-space
    'liu2017bandit-ea': '10.1016/j.asoc.2024.111756',  # Li 2024 ASOC
}

for key, doi in DOIS.items():
    req = urllib.request.Request(f'https://api.crossref.org/works/{doi}', headers={'User-Agent': 'TLE-audit/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        msg = data.get('message', {})
        print(f'=== {key} ===')
        print(f'  DOI: {doi}')
        # Authors
        authors = msg.get('author', [])
        print(f'  Authors ({len(authors)}):')
        for a in authors[:5]:
            fam = a.get('family', '')
            giv = a.get('given', '')
            print(f'    {fam}, {giv}')
        if len(authors) > 5:
            print(f'    ... +{len(authors)-5} more')
        # Title
        t = msg.get('title', [''])[0]
        print(f'  Title: {t}')
        # Journal
        j = msg.get('container-title', [''])[0]
        print(f'  Journal: {j}')
        # Year
        y = msg.get('issued', {}).get('date-parts', [[0]])[0][0]
        print(f'  Year: {y}')
        # Vol/pages
        v = msg.get('volume', '')
        n = msg.get('number', '')
        p = msg.get('page', '')
        print(f'  Volume: {v}  Number: {n}  Pages: {p}')
        print()
