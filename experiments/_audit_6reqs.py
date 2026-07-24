"""Comprehensive audit: AI-tell, first-person, refs, format."""
import os
import re
import urllib.request
import json
import time

# Get all .tex content
PAPER_DIR = r'D:\新论文\论文'
sections = {}
for fn in os.listdir(os.path.join(PAPER_DIR, 'sections')):
    if fn.endswith('.tex'):
        with open(os.path.join(PAPER_DIR, 'sections', fn), 'r', encoding='utf-8') as f:
            sections[fn] = f.read()

main_tex = ''
with open(os.path.join(PAPER_DIR, 'main.tex'), 'r', encoding='utf-8') as f:
    main_tex = f.read()
supp_tex = ''
with open(os.path.join(PAPER_DIR, 'supplementary_material.tex'), 'r', encoding='utf-8') as f:
    supp_tex = f.read()

all_tex = '\n'.join([main_tex, supp_tex] + list(sections.values()))

def strip_latex_commands(s):
    # Remove \cite{}, \ref{}, \label{}, \textbf{} etc - keep content
    s = re.sub(r'\\[a-zA-Z]+\*?\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\[a-zA-Z]+\*?', '', s)
    s = re.sub(r'\{([^}]*)\}', r'\1', s)
    s = re.sub(r'%[^\n]*', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s

plain = strip_latex_commands(all_tex)

print('='*80)
print('[1] AI-TELL PHRASES SCAN')
print('='*80)
ai_tells = [
    'demonstrated that',
    'it is shown that',
    'has been shown to',
    'it can be seen',
    'it is worth noting',
    'it is important to note',
    'importantly,',
    'in conclusion,',
    'in summary,',
    'notably,',
    'interestingly,',
    'remarkably,',
    'comprehensive review',
    'leverages',
    'harness',
    'encompasses',
    'facilitates',
    'delve into',
    'in the realm of',
    'in the field of',
    'landscape of',
    'plethora of',
    'myriad of',
    'navigating the',
    'powerful tool',
    'game-changer',
    'revolutionize',
    'cutting-edge',
    'state-of-the-art',
    'paradigm shift',
    'pivotal role',
    'crucial role',
    'plays a key role',
    'has emerged as',
    'has become increasingly',
    'in recent years',
    'in recent times',
    'a wide range of',
    'a variety of',
    'on the other hand',
    'in addition,',
    'moreover,',
    'furthermore,',
    'additionally,',
    'consequently,',
    'therefore,',
    'thus,',
    'hence,',
    'not only ... but also',
    'it should be noted',
    'as mentioned earlier',
    'as previously stated',
    'as discussed above',
    'it is well known',
    'it is well-established',
    'it is widely recognized',
    'has gained significant',
    'has attracted significant',
    'growing interest in',
    'increasingly popular',
    'widespread attention',
    'novel framework',
    'novel approach',
    'novel method',
    'propose a novel',
    'in this paper, we',
    'in this work, we',
    'we present',
    'we propose',
    'we introduce',
    'we develop',
    'we design',
    'we evaluate',
    'we conduct',
    'we investigate',
    'we explore',
    'we examine',
    'we analyze',
    'we study',
    'we compare',
    'we test',
    'we believe',
    'we argue',
    'we claim',
    'we contend',
    'we note',
    'we observe',
    'we find',
    'we show',
    'our approach',
    'our method',
    'our framework',
    'our results',
    'our experiments',
    'our findings',
    'our analysis',
    'our contribution',
    'our work',
]
found = 0
for phrase in ai_tells:
    count = plain.lower().count(phrase.lower())
    if count > 0:
        # Find context
        idx = plain.lower().find(phrase.lower())
        context = plain[max(0, idx-40):idx+len(phrase)+40]
        print(f'  HIT: "{phrase}" x{count}: ...{context}...')
        found += count
print(f'\nTotal AI-tell hits: {found}')

print()
print('='*80)
print('[4] FIRST-PERSON SCAN (case-insensitive, excluding math/code)')
print('='*80)
# Look for \bI\b, \bwe\b, \bour\b, \bus\b
# But NOT: UCB1, IGD, HV, CEC, UCB, MOEA, DMO, EA, RSM, et al. acronyms
# NOT: items (i), (ii), (iii), sub indices
first_person_patterns = [
    (r'\bI\s+', 'I (capital) followed by space'),
    (r" I'", "I' contraction"),
    (r'\bme\b', 'me'),
    (r'\bmy\b', 'my'),
    (r'\bmine\b', 'mine'),
    (r'\bmyself\b', 'myself'),
    # we — careful, lots of false positives like "we" in citations, "we" in compounds
    (r'\bwe\s+', 'we '),
    (r"\bwe'", "we'"),
    (r'\bus\s+', 'us '),
    (r'\bours\b', 'ours'),
    (r'\bourselves\b', 'ourselves'),
    (r'\bour\s+', 'our '),
]
found_fp = 0
for pat, label in first_person_patterns:
    matches = list(re.finditer(pat, plain, re.IGNORECASE))
    if matches:
        for m in matches[:3]:
            idx = m.start()
            ctx = plain[max(0, idx-50):idx+50]
            print(f'  HIT: {label}: ...{ctx}...')
        found_fp += len(matches)
print(f'\nTotal first-person hits: {found_fp}')

print()
print('='*80)
print('[3] SWEVO SCOPE CHECK')
print('='*80)
print('Paper topic: TLE (Triggered LLM-Enhanced Evolutionary Algorithm) for DMO')
print('Key components:')
print('  - Dynamic multi-objective optimization (DMO) ✓ in SWEVO scope')
print('  - LLM-enhanced evolutionary algorithm (LLM-EC) ✓ emerging SWEVO topic')
print('  - UCB bandit budget scheduling ✓ in scope (related to MO algorithm tuning)')
print('  - UAV task allocation as testbed ✓ typical SWEVO application')

# Also fetch SWEVO aims/scope from web
print()
print('Fetching SWEVO Aims & Scope from web...')
try:
    req = urllib.request.Request('https://www.sciencedirect.com/journal/swarm-and-evolutionary-computation/about/aims-and-scope',
                                 headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode('utf-8', errors='ignore')[:5000]
    # Find relevant text
    idx = content.lower().find('swarm')
    if idx > 0:
        print(content[idx:idx+1500])
except Exception as e:
    print(f'Web fetch failed: {e}')

print()
print('='*80)
print('[5] FORMAT CHECK')
print('='*80)

# Abstract length
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', all_tex, re.DOTALL)
if m:
    abs_text = re.sub(r'\\[a-zA-Z]+\*?\{([^}]*)\}', r'\1', m.group(1))
    abs_text = re.sub(r'\\[a-zA-Z]+\*?', '', abs_text)
    abs_text = re.sub(r'\s+', ' ', abs_text).strip()
    words = len(abs_text.split())
    print(f'Abstract word count: {words} (SWEVO typical: 200-300, max 350)')

# Highlights
hl = re.findall(r'\\hl\{([^}]+)\}', main_tex + supp_tex)
print(f'\nHighlights count: {len(hl)}')
for i, h in enumerate(hl, 1):
    h_clean = h.strip()
    print(f'  {i}. ({len(h_clean)} chars) {h_clean[:80]}...')

# Document class
m = re.search(r'\\documentclass\[([^\]]+)\]', main_tex)
if m:
    print(f'\nDocument class options: {m.group(1)}')

# Page count
import subprocess
print('\nPDFs:')
for pdf in ['main.pdf', 'cover_letter.pdf', 'supplementary_material.pdf']:
    p = os.path.join(PAPER_DIR, pdf)
    if os.path.exists(p):
        sz = os.path.getsize(p)
        print(f'  {pdf}: {sz/1024:.0f} KB')

print()
print('='*80)
print('[6] REFERENCES REALNESS')
print('='*80)
with open(os.path.join(PAPER_DIR, 'references.bib'), 'r', encoding='utf-8') as f:
    bib = f.read()
entries = []
for m in re.finditer(r'@(?P<type>\w+)\{(?P<key>[^,]+),', bib):
    key = m.group('key')
    start = m.end()
    next_m = re.search(r'\n@', bib[start:])
    end = start + next_m.start() if next_m else len(bib)
    entry = bib[start:end]
    doi_m = re.search(r'doi\s*=\s*\{([^}]+)\}', entry)
    year_m = re.search(r'year\s*=\s*\{(\d{4})\}', entry)
    title_m = re.search(r'title\s*=\s*\{([^}]+)\}', entry)
    entries.append({
        'key': key,
        'doi': doi_m.group(1) if doi_m else None,
        'year': int(year_m.group(1)) if year_m else None,
        'title': title_m.group(1)[:60] if title_m else None,
    })

print(f'Total entries: {len(entries)}')
print(f'With DOI: {sum(1 for e in entries if e["doi"])}')
print(f'Without DOI: {sum(1 for e in entries if not e["doi"])}')
print(f'2025-2026: {sum(1 for e in entries if e["year"] and e["year"] >= 2025)}')

# Verify each DOI
real = 0
fake = 0
errors = 0
for e in entries:
    if not e['doi']:
        continue
    try:
        req = urllib.request.Request(f'https://api.crossref.org/works/{e["doi"]}', headers={'User-Agent': 'TLE-audit/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            msg = data.get('message', {})
            t = msg.get('title', [''])[0] if msg.get('title') else ''
            # Check title similarity
            if e['title']:
                # Strip LaTeX
                bib_title = re.sub(r'\{([^}]*)\}', r'\1', e['title']).lower()
                crossref_title = t.lower()
                # Take first 30 chars
                if bib_title[:30] in crossref_title or crossref_title[:30] in bib_title:
                    real += 1
                else:
                    fake += 1
                    print(f'  TITLE MISMATCH: {e["key"]}')
                    print(f'    bib:     {e["title"]}')
                    print(f'    crossref: {t[:80]}')
            else:
                real += 1
    except urllib.error.HTTPError as ex:
        fake += 1
        print(f'  FABRICATED: {e["key"]} ({ex.code})')
    except Exception as ex:
        errors += 1
        print(f'  ERROR: {e["key"]} - {ex}')
    time.sleep(0.3)

print(f'\nDOI verification: {real} REAL, {fake} FAKE, {errors} errors')
