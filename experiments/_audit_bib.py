"""Audit references.bib for duplicates, fake DOIs, arXiv."""
import re
from collections import defaultdict

BIB = r'D:\新论文\论文\references.bib'
with open(BIB, 'r', encoding='utf-8') as f:
    text = f.read()

entries = re.findall(r'@(\w+)\{([^,]+),(.*?)\n\}', text, re.DOTALL)
print(f'Total entries: {len(entries)}\n')

doi_pattern = re.compile(r'doi\s*=\s*\{([^}]+)\}')
title_pattern = re.compile(r'title\s*=\s*\{([^}]+)\}')
year_pattern = re.compile(r'year\s*=\s*\{([^}]+)\}')

doi_to_keys = defaultdict(list)
title_to_keys = defaultdict(list)
no_doi = []
arxiv = []
fake_doi = []
year_dist = defaultdict(int)

for etype, key, body in entries:
    dois = doi_pattern.findall(body)
    titles = title_pattern.findall(body)
    years = year_pattern.findall(body)
    if years:
        year_dist[years[0]] += 1
    if not dois:
        no_doi.append((etype, key, titles[0] if titles else '?'))
    for d in dois:
        doi_to_keys[d].append(key)
        if 'arxiv' in d.lower():
            arxiv.append((key, d))
        # Suspect placeholder pattern
        if re.search(r'\.9999|placeholder|TBD|TODO|XXX|tmp|nnnnnnn', d, re.IGNORECASE):
            fake_doi.append((key, d))
        elif '3456789' in d:
            fake_doi.append((key, d))
    if titles:
        t_norm = re.sub(r'[\{\}\\"\'`´]', '', titles[0]).strip().lower()[:80]
        title_to_keys[t_norm].append(key)

print('=== YEAR DISTRIBUTION ===')
for y in sorted(year_dist.keys()):
    print(f'  {y}: {year_dist[y]}')

print('\n=== DUPLICATE DOIs ===')
dup_doi_count = 0
for d, ks in doi_to_keys.items():
    if len(ks) > 1:
        dup_doi_count += 1
        print(f'  {d}')
        for k in ks: print(f'    -> {k}')
if not dup_doi_count: print('  (none)')

print('\n=== DUPLICATE TITLES (first 80 chars) ===')
dup_title_count = 0
for t, ks in title_to_keys.items():
    if len(ks) > 1:
        dup_title_count += 1
        print(f'  "{t}"')
        for k in ks: print(f'    -> {k}')
if not dup_title_count: print('  (none)')

print(f'\n=== NO DOI ({len(no_doi)} entries) ===')
for et, k, t in no_doi:
    print(f'  [{et}] {k}: {t[:80]}')

print(f'\n=== ARXIV ({len(arxiv)} entries) ===')
for k, d in arxiv: print(f'  {k}: {d}')

print(f'\n=== SUSPECTED FAKE DOI ({len(fake_doi)} entries) ===')
for k, d in fake_doi: print(f'  {k}: {d}')

# Print sample entries that share page numbers within same volume (highly suspicious)
print('\n=== SAME JOURNAL+VOLUME+PAGES (impossible duplicates) ===')
vols = re.findall(r'journal\s*=\s*\{([^}]+)\}[^}]*volume\s*=\s*\{([^}]+)\}[^}]*pages\s*=\s*\{([^}]+)\}', text, re.DOTALL)
from collections import Counter
vols_counter = Counter(vols)
for v, c in vols_counter.items():
    if c > 1:
        print(f'  {v}: {c} entries with same journal+volume+pages')