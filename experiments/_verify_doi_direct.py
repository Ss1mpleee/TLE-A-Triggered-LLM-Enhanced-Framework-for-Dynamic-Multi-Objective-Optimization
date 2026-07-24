"""Thorough DOI verification via direct crossref API."""
import re
import json
import urllib.request
import urllib.error
import time

BIB = r'D:\新论文\论文\references.bib'
with open(BIB, 'r', encoding='utf-8') as f:
    text = f.read()

entries = re.findall(r'@(\w+)\{([^,]+),(.*?)\n\}', text, re.DOTALL)

print(f'Total entries: {len(entries)}\n')
print(f'{"KEY":40s} {"STATUS":10s} {"DOI":40s} TITLE_MATCH')
print('=' * 130)

results = []
for etype, key, body in entries:
    dois = re.findall(r'doi\s*=\s*\{([^}]+)\}', body)
    titles = re.findall(r'title\s*=\s*\{([^}]+)\}', body)
    authors_raw = re.findall(r'author\s*=\s*\{([^}]+)\}', body)
    if not dois:
        results.append((key, 'NO_DOI', '-', '-', 'no DOI provided'))
        print(f'{key:40s} {"NO_DOI":10s} {"-":40s} (no DOI)')
        continue
    doi = dois[0]
    bib_title = titles[0] if titles else ''
    bib_first_author = ''
    if authors_raw:
        a = authors_raw[0]
        # First author surname
        bib_first_author = a.split(' and ')[0].split(',')[0].strip()

    url = f'https://api.crossref.org/works/{doi}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TLE-audit/1.0 (mailto:user@example.com)'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            msg = data.get('message', {})
            actual_title = msg.get('title', [''])[0] if msg.get('title') else ''
            actual_author_list = msg.get('author', [])
            actual_first = actual_author_list[0].get('family', '') if actual_author_list else ''

            # Compare
            bib_t = re.sub(r'[\{\}\\]', '', bib_title).lower()[:40]
            actual_t = re.sub(r'[\{\}\\]', '', actual_title).lower()[:40]
            t_match = bib_t[:30] in actual_t or actual_t[:30] in bib_t
            a_match = bib_first_author.lower()[:15] in actual_first.lower() or actual_first.lower()[:15] in bib_first_author.lower()

            if t_match and a_match:
                status = 'REAL'
            elif t_match and not a_match:
                status = 'AUTHOR_MISMATCH'
            elif not t_match and a_match:
                status = 'TITLE_MISMATCH'
            else:
                status = 'WRONG_PAPER'
            print(f'{key:40s} {status:10s} {doi:40s} bib="{bib_t[:30]}" actual="{actual_t[:30]}"')
            results.append((key, status, doi, bib_title[:60], actual_title[:60]))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f'{key:40s} {"FABRICATED":10s} {doi:40s} (404 not found)')
            results.append((key, 'FABRICATED', doi, bib_title[:60], '-'))
        else:
            print(f'{key:40s} {"ERROR":10s} {doi:40s} ({e.code})')
            results.append((key, 'ERROR', doi, bib_title[:60], '-'))
    except Exception as e:
        print(f'{key:40s} {"ERROR":10s} {doi:40s} ({e})')
        results.append((key, 'ERROR', doi, bib_title[:60], '-'))
    time.sleep(0.3)  # rate limit

# Summary
print()
print('=' * 130)
print('SUMMARY')
print('=' * 130)
real = [r for r in results if r[1] == 'REAL']
no_doi = [r for r in results if r[1] == 'NO_DOI']
issues = [r for r in results if r[1] not in ('REAL', 'NO_DOI')]
print(f'Total: {len(results)}')
print(f'REAL (verified): {len(real)}')
print(f'NO_DOI (skipped): {len(no_doi)}')
print(f'ISSUES (need fix): {len(issues)}')

if issues:
    print('\n=== ISSUES ===')
    for key, status, doi, bib_t, actual_t in issues:
        print(f'  {key}: {status} | DOI={doi}')
        print(f'    bib:  {bib_t}')
        print(f'    actual: {actual_t}')

if no_doi:
    print('\n=== NO DOI (well-known classics, no fix needed) ===')
    for key, status, doi, bib_t, actual_t in no_doi:
        print(f'  {key}')