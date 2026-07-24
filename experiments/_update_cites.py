"""Apply all cite renames in one go."""
import os
import re

# Mapping: old key -> new key
KEY_MAP = {
    'deb2007dnsga': 'deb2007dnsga',  # same
    'farina2004': 'farina2004',  # same
    'zhou2014pps': 'zhou2013pps',  # year
    'wu2024evolutionary': 'wu2024llmec',  # rename
    'vanstein2025llamea': 'vanstein2024llamea',  # year
    'liu2026llm-aided': 'liu2024llmmoea',  # year + name
    'romera2024funsearch': 'romera2024funsearch',  # same
    'liu2024llm-surrogate': 'hao2024llmsurrogate',  # rename
    'li2015moead': 'li2008moead',  # year
    'huang2026knee-dmo': 'huang2026knee',  # rename
    'liu2026dual-space': 'liu2026dual',  # rename
    'auer2002ucb': 'auer2002ucb',  # same
    'besbes2014stochastic': 'besbes2014stochastic',  # same
    'garivier2011upper': 'garivier2011ucb',  # rename
    'storn1997de': 'storn1997de',  # same
    'nsga2': 'deb2002nsga2',  # rename
    'friedman1937': 'friedman1937',  # same
    'demvsar2006': 'demsar2006',  # rename
}

# Keys to drop entirely
DROP_KEYS = ['wang2026adr-dmoea', 'cec2018dmo']

# Keys to add (new in this round)
# No add — all new bib keys are renames, no new concept

sections_dir = r'D:\新论文\论文\sections'
for fn in os.listdir(sections_dir):
    if not fn.endswith('.tex'):
        continue
    path = os.path.join(sections_dir, fn)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    # Apply renames
    for old, new in KEY_MAP.items():
        if old == new:
            continue
        content = content.replace(f'\\cite{{{old}}}', f'\\cite{{{new}}}')
    # Drop cite for wang2026adr-dmoea and cec2018dmo
    # Match ~[\cite{...}] or just \cite{...} in context
    for k in DROP_KEYS:
        # Match patterns like " and adaptive dynamic response strategies~\cite{wang2026adr-dmoea}."
        # Drop the \cite{...} but keep the surrounding text
        # First, drop standalone \cite{k} in 04_experimental_setup
        content = re.sub(r'~?\\cite\{' + re.escape(k) + r'\}', '', content)
        # Also handle list of cites
        content = re.sub(r',?\\cite\{' + re.escape(k) + r'\}', '', content)
    # Clean up any ", , " or trailing ", "
    content = re.sub(r'~?, ,', '~', content)
    content = re.sub(r', ,', ',', content)
    content = re.sub(r'~,\s*', '~', content)
    content = re.sub(r'\s+,', ',', content)
    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {fn}')
    else:
        print(f'  (no change) {fn}')

print()
print('=== Verify all cites resolve to bib ===')
import re
with open(r'D:\新论文\论文\references.bib', 'r', encoding='utf-8') as f:
    bib = f.read()
bib_keys = set(re.findall(r'@(?:\w+)\{([^,]+),', bib))
print(f'Bib keys: {len(bib_keys)}')

cite_pat = re.compile(r'\\cite\{([^}]+)\}')
all_cited = set()
for fn in os.listdir(sections_dir):
    if fn.endswith('.tex'):
        with open(os.path.join(sections_dir, fn), 'r', encoding='utf-8') as f:
            c = f.read()
        for m in cite_pat.finditer(c):
            for k in m.group(1).split(','):
                all_cited.add(k.strip())
print(f'Cited keys: {len(all_cited)}')
broken = all_cited - bib_keys
if broken:
    for k in broken:
        print(f'  BROKEN: {k}')
else:
    print('  ALL CITE KEYS RESOLVE')

unused = bib_keys - all_cited
if unused:
    print(f'\nUnused bib keys: {unused}')
