"""Verify 4 replacement DOIs."""
import urllib.request
import json

DOIS = [
    '10.1145/3787965',  # Liu 2026 ACM LLM-aided MOEA
    '10.1016/j.swevo.2020.100668',  # Wan 2020 SWEVO
    '10.1162/evco.a.393',  # Liu 2026 ECJ dual-space
    '10.1016/j.asoc.2024.111756',  # Li 2024 ASOC
]
for doi in DOIS:
    try:
        req = urllib.request.Request(f'https://api.crossref.org/works/{doi}', headers={'User-Agent': 'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            msg = data.get('message', {})
            t = msg.get('title', [''])[0] if msg.get('title') else ''
            a = msg.get('author', [{}])[0].get('family', '') if msg.get('author') else ''
            y = msg.get('issued', {}).get('date-parts', [[0]])[0][0] if msg.get('issued') else 0
            j = msg.get('container-title', [''])[0] if msg.get('container-title') else ''
            print(f'  {doi}: REAL')
            print(f'    {a} ({y}) | {j}')
            print(f'    "{t[:90]}"')
    except urllib.error.HTTPError as e:
        print(f'  {doi}: {e.code} FABRICATED')
    except Exception as e:
        print(f'  {doi}: ERROR {e}')
