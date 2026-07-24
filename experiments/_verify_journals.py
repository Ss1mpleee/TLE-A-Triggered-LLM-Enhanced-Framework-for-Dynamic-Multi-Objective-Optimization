"""Verify additional DMO papers from other journals."""
import urllib.request, json

# Known real DMO papers from reference lists
DOIS = {
    'jiang2019tl-dmo': '10.1109/TEVC.2017.2777782',  # Transfer learning DMO TEVC 22(4):501-514
    'jiang2021knee-tl': '10.1109/TEVC.2020.3003966',  # Knee point transfer DMO TEVC 25(1):117-129
    'cao2020svr-dmo': '10.1109/TEVC.2019.2925770',  # SVR DMO TEVC 24(2):305-319
    'yang2018steady': '10.1109/TEVC.2016.2554635',  # steady-state DMO TEVC 21(1):65-82
    'zhang2019novel-pred': '10.1109/TEVC.2018.2867098',  # Novel prediction strategies DMO TEVC
    'muruganantham2016kalman': '10.1109/TCYB.2015.2463093',  # Kalman filter DMO TCYB
    'ruan2017dm-div': '10.1016/j.asoc.2017.04.037',  # diversity maintenance prediction ASOC
    'azzouz2017change': '10.1007/s00500-015-1985-1',  # change severity population management Soft Computing
}

for key, doi in DOIS.items():
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
            print(f'[{key}] REAL')
            print(f'  {af} ({y}) {j} {v}({n}):{p}')
            print(f'  "{t[:80]}"')
    except urllib.error.HTTPError as e:
        print(f'[{key}] {doi}: {e.code} FABRICATED')
    except Exception as e:
        print(f'[{key}] {doi}: ERROR {e}')
    print()
