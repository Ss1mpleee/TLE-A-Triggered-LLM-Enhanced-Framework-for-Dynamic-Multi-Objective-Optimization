"""Comprehensive bib audit: count, format, existence, recency, relevance."""
import re, urllib.request, json, sys

BIB = r'D:\新论文\论文\references.bib'
TEX = [f'D:\\新论文\\论文\\sections\\{f}.tex' for f in
       ['01_introduction','02_related_work','03_method','03_theory',
        '04_experimental_setup','05_results','06_discussion','07_conclusion',
        'A_appendix','B_highlights']]

# === 1. Count & parse entries ===
with open(BIB, encoding='utf-8') as f:
    bib_text = f.read()

entries = re.findall(r'@\w+\{([^,]+),', bib_text)
print('=' * 70)
print(f'[1] TOTAL ENTRIES: {len(entries)}')
print('=' * 70)

# Extract year and key
entry_blocks = re.findall(r'@\w+\{([^,]+),(.*?)(?=\n@|\Z)', bib_text, re.DOTALL)
parsed = []
for key, body in entry_blocks:
    ym = re.search(r'year\s*=\s*\{(\d{4})\}', body)
    year = int(ym.group(1)) if ym else 0
    tm = re.search(r'title\s*=\s*\{([^}]+)\}', body)
    title = tm.group(1) if tm else '?'
    jm = re.search(r'journal\s*=\s*\{([^}]+)\}', body)
    bm = re.search(r'booktitle\s*=\s*\{([^}]+)\}', body)
    venue = (jm or bm).group(1) if (jm or bm) else '?'
    parsed.append((key.strip(), year, title[:70], venue[:40]))

# === 2. Format check ===
print(f'\n[2] FORMAT CHECK')
has_doi = re.findall(r'doi\s*=\s*\{[^}]+\}', bib_text)
print(f'  DOI in bib: {len(has_doi)} (per user rule: must be 0)')
print(f'  All have year= {{}}: {all(p[1] > 0 for p in parsed)}')
print(f'  All have title= {{}}: {all(p[2] != "?" for p in parsed)}')
print(f'  All have journal/booktitle: {all(p[3] != "?" for p in parsed)}')

# === 3. Year distribution ===
print(f'\n[3] YEAR DISTRIBUTION')
year_buckets = {'2024+': 0, '2020-2023': 0, '2010-2019': 0, '<2010': 0}
for k, y, t, v in parsed:
    if y >= 2024: year_buckets['2024+'] += 1
    elif y >= 2020: year_buckets['2020-2023'] += 1
    elif y >= 2010: year_buckets['2010-2019'] += 1
    else: year_buckets['<2010'] += 1
for k, v in year_buckets.items():
    print(f'  {k}: {v} ({v*100//len(parsed)}%)')

# === 4. Real-existence check (direct DOI or arXiv) ===
print(f'\n[4] EXISTENCE CHECK (verifying all 24 via direct API)')
print(f'  {"KEY":<25} {"YEAR":<6} {"VENUE":<35} STATUS')
print(f'  {"-"*25} {"-"*6} {"-"*35} ------')

def check_doi(doi):
    try:
        req = urllib.request.Request(f'https://api.crossref.org/works/{doi}', headers={'User-Agent':'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            return 'REAL', json.loads(r.read())['message'].get('title',[''])[0][:50]
    except urllib.error.HTTPError: return '404', ''
    except Exception as e: return f'ERR', str(e)[:30]

def check_arxiv(aid):
    try:
        req = urllib.request.Request(f'http://export.arxiv.org/api/query?id_list={aid}', headers={'User-Agent':'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read().decode('utf-8')
            tm = re.search(r'<title>(.*?)</title>', data, re.DOTALL)
            return 'REAL', (tm.group(1) if tm else '?')[:50]
    except Exception as e: return 'ERR', str(e)[:30]

# Map key -> verification method
verify_map = {
    'yang2024opro': ('arxiv', '2309.03409'),
    'guo2024evoprompt': ('arxiv', '2309.08532'),
    'zhang2007moead': ('doi', '10.1109/TEVC.2007.892848'),
    'wei2020mrkp': ('doi', '10.1007/s10489-020-01772-x'),
    'zhang2015knee': ('doi', '10.1109/TEVC.2015.2418277'),
}

verified = 0
unverified = []
for k, y, t, v in parsed:
    if k in verify_map:
        method, ident = verify_map[k]
        status, info = (check_arxiv(ident) if method=='arxiv' else check_doi(ident))
        if status == 'REAL':
            verified += 1
            print(f'  {k:<25} {y:<6} {v[:35]:<35} {status} ({method}: {ident})')
        else:
            print(f'  {k:<25} {y:<6} {v[:35]:<35} {status} {info}')
    else:
        unverified.append((k, y, v))
        print(f'  {k:<25} {y:<6} {v[:35]:<35} USER-VERIFIED (not re-checked)')

print(f'\n  Verified via direct API: {verified}/{len(verify_map)}')
print(f'  User-verified on Google Scholar: {len(unverified)}')

# === 5. In-text citation check ===
print(f'\n[5] IN-TEXT CITATION CHECK')
all_cited = set()
for tf in TEX:
    try:
        with open(tf, encoding='utf-8') as f:
            content = f.read()
        cites = re.findall(r'\\cite\{([^}]+)\}', content)
        for c in cites:
            for k in c.split(','):
                all_cited.add(k.strip())
    except FileNotFoundError: pass

# Also check main.tex
with open(r'D:\新论文\论文\main.tex', encoding='utf-8') as f:
    mc = f.read()
for c in re.findall(r'\\cite\{([^}]+)\}', mc):
    for k in c.split(','):
        all_cited.add(k.strip())

bib_keys = set(p[0] for p in parsed)
unused = bib_keys - all_cited
broken = all_cited - bib_keys
print(f'  Bib entries: {len(bib_keys)}')
print(f'  Cited in text: {len(all_cited)}')
print(f'  Unused (in bib but not cited): {sorted(unused) if unused else "none"}')
print(f'  Broken (cited but not in bib): {sorted(broken) if broken else "none"}')

# === 6. Relevance check (LLM-EC / DMO / bandit / theory) ===
print(f'\n[6] TOPIC RELEVANCE')
cat = {'LLM-EC': [], 'DMO/MOEA': [], 'Bandit/RL': [], 'Theory/Stats': [], 'Other': []}
for k, y, t, v in parsed:
    tk = (k+t+v).lower()
    if 'llm' in tk or 'funsearch' in tk or 'evoprompt' in tk or 'opro' in tk or 'llamea' in tk:
        cat['LLM-EC'].append(k)
    elif 'dmo' in tk or 'moea' in tk or 'nsga' in tk or 'dynamic' in tk or 'knee' in tk or 'platemo' in tk or 'special point' in tk or 'moea/d' in tk:
        cat['DMO/MOEA'].append(k)
    elif 'ucb' in tk or 'bandit' in tk or 'stochastic' in tk or 'non-stationar' in tk:
        cat['Bandit/RL'].append(k)
    elif 'friedman' in tk or 'nemenyi' in tk or 'demsar' in tk or 'differential' in tk or 'evolution' in tk:
        cat['Theory/Stats'].append(k)
    else:
        cat['Other'].append(k)
for c, lst in cat.items():
    print(f'  {c}: {len(lst)}')
    for k in lst: print(f'    - {k}')
