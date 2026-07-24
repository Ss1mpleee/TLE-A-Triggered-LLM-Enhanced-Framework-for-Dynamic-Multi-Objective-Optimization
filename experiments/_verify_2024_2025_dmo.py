"""Verify real DOI for known 2024-2025 DMO papers found via web search."""
import urllib.request, json

def check(doi):
    try:
        req = urllib.request.Request(f'https://api.crossref.org/works/{doi}',
                                     headers={'User-Agent': 'TLE-audit/1.0 (mailto:test@test.com)'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            d = json.loads(resp.read().decode('utf-8'))['message']
            t = d.get('title',[''])[0]
            y = (d.get('issued',{}).get('date-parts',[[0]])[0][0]
                 or d.get('published-print',{}).get('date-parts',[[0]])[0][0]
                 or d.get('published-online',{}).get('date-parts',[[0]])[0][0])
            j = d.get('container-title',[''])[0] if d.get('container-title') else ''
            au = ', '.join(f"{a.get('family','')}" for a in d.get('author',[])[:3])
            return f'REAL | {y} | {j[:30]} | {au} | {t[:80]}'
    except urllib.error.HTTPError as e:
        return f'{e.code}'
    except Exception as e:
        return f'ERR: {str(e)[:60]}'

candidates = [
    # Hu Peng 2024 SWEVO 89 101621 - AB-DMOEA
    '10.1016/j.swevo.2024.101621',
    # Qiuzhen Lin 2024 IEEE TSMC 54(2) 936 - knowledge transfer DMO
    '10.1109/TSMC.2023.3292712',  # try this
    # Songbai Liu 2024 SWEVO 91 101727 - coevolutionary multitasking constrained
    '10.1016/j.swevo.2024.101727',
    # Wu Yating 2025 ECJ evco_a_00373
    '10.1162/evco_a_00373',
    # Fangzhen Ge 2025 J Supercomput
    '10.1007/s11227-024-06600-0',  # placeholder
    # Ming 2022 TriP
    '10.1016/j.swevo.2022.101166',
    # Ge 2024 Mahalanobis dynamic MOEA
    '10.1109/TEVC.2024.3376543',  # placeholder
    # Hu Peng SWEVO 2024
    '10.1016/j.swevo.2024.101625',
    # Wang 2020 ensemble learning dynamic MO
    '10.1016/j.asoc.2020.106592',
    # Liu 2024 SWEVO (the dual-space one we already have)
    '10.1016/j.swevo.2025.101892',  # placeholder
    # Liu Tianyu 2026 ECJ dual-space
    # already in bib
    # Recent SWEVO DMO 2024-2025 generic
    '10.1016/j.swevo.2024.101620',
    '10.1016/j.swevo.2024.101630',
    '10.1016/j.swevo.2024.101650',
    '10.1016/j.swevo.2024.101700',
    '10.1016/j.swevo.2025.101800',
    '10.1016/j.swevo.2025.101850',
    # Information Sciences 2024 DMO
    '10.1016/j.ins.2024.120001',  # placeholder
    # Knowledge-based Systems 2024
    '10.1016/j.knosys.2024.111500',  # placeholder
    # ICJ 2024 LLM-EC
    '10.1007/s10462-024-10710-9',  # placeholder
    # IEEE Trans on Cybernetics
    '10.1109/TCYB.2024.3367891',  # placeholder
]

for doi in candidates:
    r = check(doi)
    print(f'{doi:<40} -> {r}')
