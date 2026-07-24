"""Verify 4 more DMO candidates."""
import urllib.request, json

DOIS = [
    ('wei2020mrkp', '10.1007/s10489-020-01772-7', 'Wei 2020 knee points DMO'),
    ('cao2020svr', '10.1109/TEVC.2019.2924952', 'Cao 2020 SVR DMO'),
    ('xu2022incr', '10.1109/TEVC.2021.3066433', 'Xu 2022 incremental SVM DMO'),
    ('jiang2021knee', '10.1109/TEVC.2020.3005313', 'Jiang 2021 knee transfer DMO'),
    ('zou2020knee', '10.1016/j.ins.2020.09.038', 'Zou 2020 knee-guided prediction DMO'),
]
for key, doi, desc in DOIS:
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
            print(f'  "{t[:90]}"')
    except urllib.error.HTTPError as e:
        print(f'[{key}] {doi}: {e.code} FABRICATED')
    except Exception as e:
        print(f'[{key}] {doi}: ERROR {e}')
    print()
