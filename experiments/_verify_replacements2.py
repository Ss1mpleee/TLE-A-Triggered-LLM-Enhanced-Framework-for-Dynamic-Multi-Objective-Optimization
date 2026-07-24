"""Verify EvoPrompt 2024."""
import urllib.request, json

# Try arxiv
try:
    req = urllib.request.Request('http://export.arxiv.org/api/query?id_list=2309.08532', headers={'User-Agent': 'TLE-audit/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read().decode('utf-8')
    # Parse for title
    import re
    title_m = re.search(r'<title>(.*?)</title>', data)
    authors_m = re.findall(r'<name>(.*?)</name>', data)
    print('=== arXiv 2309.08532 ===')
    print(f'Title: {title_m.group(1) if title_m else "?"}')
    print(f'Authors: {authors_m[:5] if authors_m else "?"}')
except Exception as e:
    print(f'arXiv error: {e}')

# Verify PlatEMO via crossref
print('\n=== PlatEMO via crossref ===')
try:
    req = urllib.request.Request('https://api.crossref.org/works/10.1109/MCI.2017.2742868', headers={'User-Agent': 'TLE-audit/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        msg = data.get('message', {})
        t = msg.get('title', [''])[0] if msg.get('title') else ''
        a = msg.get('author', [])
        af = ', '.join(x.get('family', '') for x in a[:5]) if a else ''
        y = msg.get('issued', {}).get('date-parts', [[0]])[0][0]
        j = msg.get('container-title', [''])[0]
        v = msg.get('volume', '')
        n = msg.get('number', '')
        p = msg.get('page', '')
        print(f'  {af} ({y}) {j} {v}({n}):{p}')
        print(f'  "{t}"')
except Exception as e:
    print(f'Crossref error: {e}')
