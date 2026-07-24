"""Manually verify 6 DOIs return correct titles matching bib entries."""
import urllib.request
import json

DOIS = {
    'huang2026knee-dmo': '10.1016/j.swevo.2026.102358',
    'cao2026effective': '10.1016/j.swevo.2026.102364',
    'zhang2026ga-gnn': '10.1016/j.swevo.2026.102366',
    'ding2026sparse-bo': '10.1016/j.swevo.2026.102360',
    'deb2007dnsga': '10.1007/978-3-540-70928-2_60',
    'zhou2014pps': '10.1109/TCYB.2013.2245892',
}

for key, doi in DOIS.items():
    try:
        req = urllib.request.Request(f'https://api.crossref.org/works/{doi}', headers={'User-Agent': 'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            msg = data.get('message', {})
            t = msg.get('title', [''])[0] if msg.get('title') else ''
            a = msg.get('author', [{}])
            af = ', '.join(x.get('family', '') for x in a[:3]) if a else ''
            y = msg.get('issued', {}).get('date-parts', [[0]])[0][0]
            j = msg.get('container-title', [''])[0]
            print(f'\n[{key}]')
            print(f'  Bib claim: see references.bib')
            print(f'  Crossref: {af} ({y}) {j}')
            print(f'  Title: "{t}"')
    except Exception as e:
        print(f'[{key}] ERROR: {e}')

# Also dump bib entries for visual compare
print('\n\n=== Bib content for these 6 ===')
import re
with open(r'D:\新论文\论文\references.bib', 'r', encoding='utf-8') as f:
    bib = f.read()
for key in DOIS.keys():
    m = re.search(r'@(?:\w+)\{' + re.escape(key) + r',.*?\n\}', bib, re.DOTALL)
    if m:
        print(f'\n[{key}]')
        print(m.group(0))
