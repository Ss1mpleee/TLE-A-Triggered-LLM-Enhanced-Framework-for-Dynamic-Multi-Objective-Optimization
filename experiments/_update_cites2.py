"""Better cite rewrite: handle \cite{a, b} lists."""
import os
import re

KEY_MAP = {
    'deb2007dnsga': 'deb2007dnsga',
    'farina2004': 'farina2004',
    'zhou2014pps': 'zhou2013pps',
    'wu2024evolutionary': 'wu2024llmec',
    'vanstein2025llamea': 'vanstein2024llamea',
    'liu2026llm-aided': 'liu2024llmmoea',
    'romera2024funsearch': 'romera2024funsearch',
    'liu2024llm-surrogate': 'hao2024llmsurrogate',
    'li2015moead': 'li2008moead',
    'huang2026knee-dmo': 'huang2026knee',
    'liu2026dual-space': 'liu2026dual',
    'auer2002ucb': 'auer2002ucb',
    'besbes2014stochastic': 'besbes2014stochastic',
    'garivier2011upper': 'garivier2011ucb',
    'storn1997de': 'storn1997de',
    'nsga2': 'deb2002nsga2',
    'friedman1937': 'friedman1937',
    'demvsar2006': 'demsar2006',
}
DROP_KEYS = {'wang2026adr-dmoea', 'cec2018dmo'}

def fix_cites(content):
    def replace_in_cite(m):
        keys = [k.strip() for k in m.group(1).split(',')]
        new_keys = []
        for k in keys:
            if k in DROP_KEYS:
                continue
            if k in KEY_MAP:
                k = KEY_MAP[k]
            if k:
                new_keys.append(k)
        if not new_keys:
            return ''  # entire cite empty
        return f'\\cite{{{", ".join(new_keys)}}}'
    # Apply multiple times to catch nested
    prev = None
    for _ in range(5):
        new = re.sub(r'\\cite\{([^{}]+)\}', replace_in_cite, content)
        if new == content:
            break
        content = new
    return content

sections_dir = r'D:\新论文\论文\sections'
for fn in os.listdir(sections_dir):
    if not fn.endswith('.tex'):
        continue
    path = os.path.join(sections_dir, fn)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = fix_cites(content)
    # Cleanup: , space , patterns from dropped cites
    new_content = re.sub(r'~?,\s*,', '~', new_content)
    new_content = re.sub(r'~,\s+', '~', new_content)
    new_content = re.sub(r',\s*,', ',', new_content)
    new_content = re.sub(r'\s+~', '~', new_content)
    # Fix any standalone double-comma
    new_content = re.sub(r'\{,\s*\}', '{}', new_content)
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated {fn}')

# Verify
print()
print('=== Verify cites ===')
with open(r'D:\新论文\论文\references.bib', 'r', encoding='utf-8') as f:
    bib = f.read()
bib_keys = set(re.findall(r'@(?:\w+)\{([^,]+),', bib))
print(f'Bib keys: {len(bib_keys)}')

cite_pat = re.compile(r'\\cite\{([^{}]+)\}')
all_cited = set()
for fn in os.listdir(sections_dir):
    if fn.endswith('.tex'):
        with open(os.path.join(sections_dir, fn), 'r', encoding='utf-8') as f:
            c = f.read()
        for m in cite_pat.finditer(c):
            for k in m.group(1).split(','):
                all_cited.add(k.strip())
print(f'Cited keys: {sorted(all_cited)}')
broken = all_cited - bib_keys
if broken:
    for k in broken:
        print(f'  BROKEN: {k}')
else:
    print('  ALL CITE KEYS RESOLVE')

unused = bib_keys - all_cited
if unused:
    print(f'\nUnused bib keys: {sorted(unused)}')
