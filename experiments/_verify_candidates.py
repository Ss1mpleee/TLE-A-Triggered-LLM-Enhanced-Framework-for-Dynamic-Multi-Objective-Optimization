"""Verify 7 additional ref candidates via crossref/arXiv."""
import urllib.request, json

CANDIDATES = [
    ('zhang2007moead', '10.1109/TEVC.2007.892759', 'MOEA/D original'),
    ('zhang2014knee', '10.1109/TEVC.2014.2378512', 'Knee point MOEA'),
    ('li2009moead-d', '10.1109/TEVC.2008.925798', 'MOEA/D vs NSGA-II (the original MOEA/D ref)'),
    ('auer2010log', '10.1007/s10994-009-5082-2', 'Auer UCB1 logarithmic regret extension'),
    ('trovo2020swts', 'arXiv:2005.11960', 'Sliding window Thompson sampling'),
    ('jintian2018platemo-knn', '10.1109/TEVC.2018.2869400', 'Tian many-objective knn'),
    ('zhang2015cea', '10.1109/TEVC.2015.2470118', 'CEC competition'),
]

for key, doi, desc in CANDIDATES:
    if doi.startswith('arXiv'):
        # arXiv
        arxiv_id = doi.replace('arXiv:', '')
        try:
            req = urllib.request.Request(f'http://export.arxiv.org/api/query?id_list={arxiv_id}', headers={'User-Agent': 'TLE-audit/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read().decode('utf-8')
            import re
            titles = re.findall(r'<title>(.*?)</title>', data, re.DOTALL)
            t = titles[1] if len(titles) > 1 else titles[0]
            authors = re.findall(r'<author>\s*<name>(.*?)</name>', data, re.DOTALL)
            print(f'[{key}] {desc}')
            print(f'  arXiv {arxiv_id}: {t[:80]}')
            print(f'  Authors: {", ".join(authors[:3])}')
        except Exception as e:
            print(f'[{key}] ERROR: {e}')
    else:
        try:
            req = urllib.request.Request(f'https://api.crossref.org/works/{doi}', headers={'User-Agent': 'TLE-audit/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                msg = data.get('message', {})
                t = msg.get('title', [''])[0] if msg.get('title') else ''
                a = msg.get('author', [])
                af = ', '.join(x.get('family', '') for x in a[:3]) if a else ''
                y = msg.get('issued', {}).get('date-parts', [[0]])[0][0]
                j = msg.get('container-title', [''])[0]
                v = msg.get('volume', '')
                n = msg.get('number', '')
                p = msg.get('page', '')
                print(f'[{key}] {desc}')
                print(f'  {af} ({y}) {j} {v}({n}):{p}')
                print(f'  "{t[:80]}"')
        except urllib.error.HTTPError as e:
            print(f'[{key}] {doi}: {e.code} FABRICATED')
        except Exception as e:
            print(f'[{key}] {doi}: ERROR {e}')
    print()
