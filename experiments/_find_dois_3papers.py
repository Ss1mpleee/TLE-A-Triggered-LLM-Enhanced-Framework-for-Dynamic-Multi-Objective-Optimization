"""Find actual DOIs for the 3 papers I incorrectly verified."""
import urllib.parse, urllib.request, json

queries = [
    ('zhang2007moead', 'MOEA/D multiobjective evolutionary algorithm based on decomposition'),
    ('zhang2015knee', 'knee point driven evolutionary algorithm many-objective Zhang'),
    ('wei2020mrkp', 'Wei prediction strategy special points multiregion knee points dynamic multiobjective Applied Intelligence'),
]
for key, q in queries:
    try:
        url = f'https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(q)}&rows=3'
        req = urllib.request.Request(url, headers={'User-Agent':'TLE-audit/1.0 (mailto:test@test.com)'})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode('utf-8'))
            items = d.get('message',{}).get('items',[])[:2]
            print(f'=== {key} ===')
            for it in items:
                t = it.get('title',[''])[0][:70]
                y = (it.get('issued',{}).get('date-parts',[[0]])[0][0]
                     or it.get('published-print',{}).get('date-parts',[[0]])[0][0])
                doi = it.get('DOI','')
                au = ', '.join(f"{a.get('family','')}" for a in it.get('author',[])[:3])
                print(f'  {y} | {au} | DOI: {doi}')
                print(f'    {t}')
            print()
    except Exception as e:
        print(f'{key}: ERR {e}')
