"""Verify specific 2024-2025 DOIs found in web search."""
import urllib.request, json

def check(doi):
    try:
        req = urllib.request.Request(f'https://api.crossref.org/works/{doi}', headers={'User-Agent': 'TLE-audit/1.0 (mailto:test@test.com)'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            d = json.loads(resp.read().decode('utf-8'))['message']
            t = d.get('title',[''])[0]
            y = (d.get('issued',{}).get('date-parts',[[0]])[0][0]
                 or d.get('published-print',{}).get('date-parts',[[0]])[0][0]
                 or d.get('published-online',{}).get('date-parts',[[0]])[0][0])
            j = d.get('container-title',[''])[0] if d.get('container-title') else ''
            au = ', '.join(f"{a.get('family','')}" for a in d.get('author',[])[:3])
            return f'REAL | {y} | {j[:30]} | {au} | {t[:90]}'
    except urllib.error.HTTPError as e:
        return f'{e.code} (not found)'
    except Exception as e:
        return f'ERR: {str(e)[:60]}'

# From LetPub TEVC 2024-2025 list + other 2024 papers
candidates = [
    # TEVC 2024-2025 (from LetPub)
    '10.1109/TEVC.2024.3359120',  # Zhang 2024 fuzzy jobshop
    '10.1109/TEVC.2025.3544287',  # 2026 large-scale constrained
    '10.1109/TEVC.2025.3550742',  # 2026 fragment reconstruction
    '10.1109/TEVC.2025.3551728',  # 2026 evolutionary multitask
    # Mind Evolution arXiv (Google DeepMind)
    # arXiv 2403.02108 - Mind Evolution: Evolving Deeper LLM Thinking
    # AAAI 2025 DMO papers - try common DOIs
    '10.1109/TEVC.2023.3329945',  # 2023 DMO test
    '10.1109/TEVC.2024.3425678',  # 2024 DMO placeholder
    '10.1016/j.swevo.2024.101555',  # 2024 SWEVO placeholder (would be same journal)
    # ASOC 2024-2025 DMO
    '10.1016/j.asoc.2024.112345',
    '10.1016/j.asoc.2024.111234',
    # ECJ 2024 real papers (try known issue numbers)
    '10.1162/evco.a.36',  # ECJ 2023
    '10.1162/evco.a.37',  # ECJ 2023
]

print('=== Verify 2024-2025 candidates from web search ===\n')
for doi in candidates:
    print(f'{doi:<35} -> {check(doi)}')
    print()
