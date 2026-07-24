"""Search Semantic Scholar for recent DMO/LLM-EC papers by known authors."""
import urllib.parse, urllib.request, json, time

def s2_search(query, year_from='2023-01', limit=15):
    """Search Semantic Scholar for papers with year filter."""
    try:
        url = (f'https://api.semanticscholar.org/graph/v1/paper/search'
               f'?query={urllib.parse.quote(query)}'
               f'&year={year_from}-'
               f'&limit={limit}'
               f'&fields=title,year,authors,venue,externalIds,abstract')
        req = urllib.request.Request(url, headers={'User-Agent': 'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'error': str(e)[:100]}

def crossref_lookup(title):
    """Find real DOI by title search on crossref."""
    try:
        url = f'https://api.crossref.org/works?query.title={urllib.parse.quote(title)}&rows=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'TLE-audit/1.0 (mailto:test@test.com)'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode('utf-8'))
            items = data.get('message',{}).get('items',[])
            if items:
                it = items[0]
                return {
                    'doi': it.get('DOI',''),
                    'year': (it.get('issued',{}).get('date-parts',[[0]])[0][0]
                             or it.get('published-print',{}).get('date-parts',[[0]])[0][0]),
                    'journal': (it.get('container-title',[''])[0] if it.get('container-title') else ''),
                    'authors': [f"{a.get('family','')}" for a in it.get('author',[])[:5]],
                }
    except: pass
    return None

# === Query 1: Recent DMO by known authors ===
queries = [
    'dynamic multi-objective optimization 2024',
    'dynamic multiobjective evolutionary algorithm change detection',
    'LLM evolutionary algorithm in-loop controller 2024',
    'predictive dynamic multi-objective optimization',
    'transfer learning dynamic multi-objective',
    'surrogate assisted evolutionary algorithm LLM',
    'multi-objective optimization transformer',
    'large language model prompt optimization evolutionary',
    'MOEA D knee point dynamic',
    'constrained multi-objective evolutionary 2025',
    'NSGA dynamic environment change',
    'coevolutionary multi-objective dynamic',
    'bandit evolutionary algorithm budget allocation',
    'population prediction dynamic optimization',
    'Pareto front prediction DMO',
]

found = []
print('=== Searching Semantic Scholar ===\n')
for q in queries:
    r = s2_search(q, year_from='2023-01', limit=10)
    papers = r.get('data', [])
    if papers:
        print(f'--- "{q}" ({len(papers)} hits) ---')
        for p in papers[:3]:
            yr = p.get('year', 0)
            if yr < 2023: continue
            ttl = p.get('title','')[:75]
            au = ', '.join(f"{a.get('name','?')}" for a in p.get('authors',[])[:3])
            ven = p.get('venue','')[:30]
            ext = p.get('externalIds',{})
            arxiv = ext.get('ArXiv','')
            doi = ext.get('DOI','')
            print(f'  [{yr}] {au}')
            print(f'      {ttl}')
            print(f'      Venue: {ven} | DOI: {doi or arxiv}')
            # Track candidate
            if ttl and au:
                found.append({'title': ttl, 'year': yr, 'venue': ven,
                              'doi': doi, 'arxiv': arxiv, 'authors': au})
        print()
    time.sleep(0.5)  # rate limit

print(f'\n=== Total candidates: {len(found)} ===')
