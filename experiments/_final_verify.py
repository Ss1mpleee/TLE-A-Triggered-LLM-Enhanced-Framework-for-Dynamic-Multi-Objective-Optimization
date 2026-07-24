"""Verify all 33 remaining entries are real DOIs."""
import urllib.request
import json
import re
import time

# Parse bib entries
with open(r'D:\新论文\论文\references.bib', 'r', encoding='utf-8') as f:
    bib = f.read()

# Get all keys
keys = re.findall(r'@(?:\w+)\{([^,]+),', bib)
dois = re.findall(r'doi\s*=\s*\{([^}]+)\}', bib)

# Pair them
entries = []
for m in re.finditer(r'@(?P<type>\w+)\{(?P<key>[^,]+),', bib):
    key = m.group('key')
    start = m.end()
    # Find next @ or end
    next_m = re.search(r'\n@|\Z', bib[start:])
    end = start + next_m.start() if next_m else len(bib)
    entry = bib[start:end]
    doi_m = re.search(r'doi\s*=\s*\{([^}]+)\}', entry)
    doi = doi_m.group(1) if doi_m else None
    year_m = re.search(r'year\s*=\s*\{(\d{4})\}', entry)
    year = int(year_m.group(1)) if year_m else None
    entries.append({'key': key, 'doi': doi, 'year': year, 'has_doi': doi is not None})

print(f'Total entries: {len(entries)}')
print(f'Entries with DOI: {sum(1 for e in entries if e["has_doi"])}')
print(f'Entries without DOI: {sum(1 for e in entries if not e["has_doi"])}')
print()

# Verify each DOI
real_count = 0
fake_count = 0
no_doi_count = 0
recent_count = 0
for e in entries:
    if not e['doi']:
        no_doi_count += 1
        print(f'  {e["key"]} (year={e["year"]}): NO DOI')
        continue
    if e['year'] and e['year'] >= 2025:
        recent_count += 1
    try:
        req = urllib.request.Request(f'https://api.crossref.org/works/{e["doi"]}', headers={'User-Agent': 'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            msg = data.get('message', {})
            t = msg.get('title', [''])[0] if msg.get('title') else ''
            real_count += 1
            print(f'  {e["key"]} ({e["year"]}) DOI={e["doi"]}: REAL "{t[:60]}"')
    except urllib.error.HTTPError as ex:
        fake_count += 1
        print(f'  {e["key"]} ({e["year"]}) DOI={e["doi"]}: FABRICATED {ex.code}')
    except Exception as ex:
        print(f'  {e["key"]} ({e["year"]}) DOI={e["doi"]}: ERROR {ex}')
    time.sleep(0.3)

print()
print(f'Real: {real_count}  Fake: {fake_count}  No DOI: {no_doi_count}  Total: {len(entries)}')
print(f'2025-2026: {recent_count} / {len(entries)} = {100*recent_count/len(entries):.1f}%')
