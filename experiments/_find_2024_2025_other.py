"""Search for 2024-2025 DMO/LLM-EC papers from other journals.
Direct DOI checks via crossref, no URL pattern guessing.
"""
import urllib.request, json, sys

def crossref_check(doi, expected_title_part=''):
    try:
        url = f'https://api.crossref.org/works/{doi}'
        req = urllib.request.Request(url, headers={'User-Agent': 'TLE-audit/1.0 (mailto:test@test.com)'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            msg = data.get('message', {})
            title = msg.get('title', [''])[0]
            year = (msg.get('issued', {}).get('date-parts', [[0]])[0][0]
                    or msg.get('published-print', {}).get('date-parts', [[0]])[0][0])
            journal = msg.get('container-title', [''])[0] if msg.get('container-title') else ''
            authors = ', '.join(f"{a.get('family','')} {a.get('given','')[:1]}." for a in msg.get('author', [])[:3])
            match = expected_title_part.lower() in title.lower() if expected_title_part else True
            return {'status': 'REAL', 'doi': doi, 'title': title[:80], 'year': year, 'journal': journal[:40], 'authors': authors, 'match': match}
    except urllib.error.HTTPError as e:
        return {'status': f'HTTP_{e.code}', 'doi': doi}
    except Exception as e:
        return {'status': f'ERR_{type(e).__name__}', 'doi': doi, 'err': str(e)[:50]}

# Try known journals for 2024-2025 DMO/LLM-EC papers
candidates = [
    # LLM-EC: ECJ 2024
    ('10.1162/evco.a.393', 'liu', 'Liu Tianyu ECJ 2026 dual-space prediction'),  # already in bib as liu2026dual
    # Try other ECJ 2024-2025 DMO papers
    ('10.1162/evco.a.38', '', 'ECJ 2024 vol 32 issue 1'),
    ('10.1162/evco.a.39', '', 'ECJ 2024 vol 32 issue 2'),
    # TEVC 2024 DMO
    ('10.1109/TEVC.2024.3401234', '', 'TEVC 2024 DMO test'),
    # Information Sciences 2024-2025 DMO
    ('10.1016/j.ins.2024.121234', '', 'IS 2024 DMO'),
    # ASOC 2024-2025 LLM-EC
    ('10.1016/j.asoc.2024.111999', '', 'ASOC 2024 LLM'),
    # Liu Wanyi 2024 (already in bib as liu2024llmmoea)
    # Try some real DMO 2024-2025 papers I might know
    ('10.1109/TEVC.2023.3295432', '', 'TEVC 2023 DMO predict'),
    ('10.1109/TEVC.2024.3356789', '', 'TEVC 2024 LLM-EC'),
    # Cao 2020 SVR for DMO (not 2024-2025 but for completeness)
    # Other known 2024 DMO papers
    ('10.1109/CYB.2023.3345678', '', 'IEEE CYB 2024 DMO'),
]

print('=== Direct crossref check for 2024-2025 DMO/LLM-EC papers ===\n')
for doi, _, desc in candidates:
    r = crossref_check(doi, '')
    print(f'[{r["status"]:<10}] {doi:<35} {desc}')
    if r['status'] == 'REAL':
        print(f'  Title: {r["title"]}')
        print(f'  Year: {r["year"]} | Journal: {r["journal"]}')
        print(f'  Authors: {r["authors"]}')
        print()
