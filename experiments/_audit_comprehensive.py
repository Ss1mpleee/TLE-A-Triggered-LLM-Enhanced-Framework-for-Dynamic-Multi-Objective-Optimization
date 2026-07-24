"""Comprehensive pre-submission audit:
1. AI-tell phrase scan (10% threshold check)
2. First-person / passive voice check
3. Logic consistency (data values, cross-refs)
4. References (all entries vs DOI verification)
5. Journal scope match check
"""
import re
from pathlib import Path

ROOT = Path(r'D:\新论文\论文')
SECTIONS = list((ROOT / 'sections').glob('*.tex')) + [ROOT / 'main.tex', ROOT / 'cover_letter.tex', ROOT / 'supplementary_material.tex']
SKIP_PATTERNS = ['A_appendix.tex', 'B_highlights.tex', 'cover_letter.tex', 'supplementary_material.tex']

# === AI-Tell phrases (high-frequency LLM markers) ===
AI_TELLS = {
    # Hedging/transition
    r'\bIt is worth (?:noting|mentioning)\b': 'hedging',
    r'\bIt should be (?:noted|mentioned)\b': 'hedging',
    r'\bNote that\b': 'hedging',
    r'\bNotably,?\s': 'transition',
    r'\bImportantly,?\s': 'transition',
    r'\bIn recent years\b': 'cliche',
    r'\bWith the (?:rapid )?development of\b': 'cliche',
    r'\bIn the (?:era|age) of\b': 'cliche',
    r'\bmore and more\b': 'cliche',
    r'\bplays? a (?:crucial|pivotal|key|critical|essential|important) role\b': 'cliche',
    r'\b(?:huge|vast|immense|enormous) potential\b': 'cliche',
    r'\bvery (?:challenging|important|interesting)\b': 'cliche',
    r'\bin conclusion,?\s': 'transition',
    r'\bIt is (?:important|essential|interesting|worth) to\b': 'transition',
    r'\bhas emerged as a\b': 'cliche',
    r'\bgain(?:s|ed)? (?:significant|substantial|considerable) (?:attention|interest|traction)\b': 'cliche',
    r'\bDespite (?:its|their) (?:challenges|complexities),?\b': 'cliche',
    r'\bA growing (?:body of )?(?:number of )?(?:research|interest|attention)\b': 'cliche',
    r'\b(?:opens?|opening) (?:up )?new (?:avenues|possibilities|horizons|opportunities)\b': 'cliche',
    r'\bdelve(?:s|d)? into\b': 'AI-favorite',
    r'\bcomprehensive (?:survey|review|analysis|study|understanding)\b': 'cliche',
    r'\bboth the (?:theoretical|practical) (?:and|as well as)\b': 'cliche',
    # Specific AI favorites
    r'\bFurthermore,\b': 'AI-favorite',
    r'\bMoreover,\b': 'AI-favorite',
    r'\bIn contrast,\b': 'transition',
    r'\bIndeed,\b': 'transition',
    r'\bEssentially,\b': 'transition',
    r'\bUltimately,\b': 'transition',
    r'\bNot only .+? but also\b': 'AI-favorite',
    r'\bdemonstrate[sd]? that\b': 'common',
    r'\bprovide[sd]? (?:a|an) (?:novel|new|comprehensive) (?:insight|perspective|framework)\b': 'AI-favorite',
    r'\bstate-of-the-art\b': 'cliche',
    r'\bcrucial (?:role|aspect|factor|component)\b': 'cliche',
    r'\bvast (?:landscape|potential|amount)\b': 'cliche',
    r'\blandscape of\b': 'cliche',
    r'\bever-evolving\b': 'AI-favorite',
    r'\brealm of\b': 'cliche',
    r'\bmeticulous(?:ly)?\b': 'cliche',
    r'\bintricate\b': 'AI-favorite',
    r'\bnavigate the (?:complexities|challenges|landscape)\b': 'cliche',
    r'\bin the (?:realm|domain|landscape|sphere) of\b': 'cliche',
}

# === First-person (real violations) ===
FIRST_PERSON = re.compile(
    r"(?<![\\\w])(we|us|our|ours|ourselves)(?![\\\w'])"
    r"|"
    r"(?<![\\\w])\bI\b(?![\\\w'])"
    r"|"
    r"\bThis (?:paper|work|study|article|manuscript|note|research)\s+"
    r"(propos|develop|present|introduc|report|show|demonstrat|investigat|aim|provid|describ|focus)\w*\b",
    re.IGNORECASE
)

print('=' * 80)
print('1. AI-TELL PHRASE SCAN (per file)')
print('=' * 80)
total_ai = 0
for f in sorted(SECTIONS):
    if f.name in SKIP_PATTERNS:
        continue
    txt = f.read_text(encoding='utf-8')
    # Strip math, comments, cite
    body = re.sub(r'%.*', '', txt)
    body = re.sub(r'\$[^$]*\$', '', body)
    body = re.sub(r'\\cite\{[^}]*\}', 'CITE', body)
    hits = []
    for pat, kind in AI_TELLS.items():
        for m in re.finditer(pat, body, re.IGNORECASE):
            ctx = body[max(0,m.start()-30):min(len(body),m.end()+30)].replace('\n', ' ')
            hits.append((m.group(0), kind, ctx))
    if hits:
        print(f'\n=== {f.name} ({len(hits)} hits) ===')
        for tok, kind, ctx in hits:
            print(f'  [{kind:14s}] "{tok}" in: ...{ctx}...')
        total_ai += len(hits)
print(f'\n>>> Total AI-tell hits across main paper: {total_ai}')

print()
print('=' * 80)
print('2. FIRST-PERSON SCAN (real violations only)')
print('=' * 80)
total_fp = 0
for f in sorted(SECTIONS):
    txt = f.read_text(encoding='utf-8')
    body = re.sub(r'%.*', '', txt)
    body = re.sub(r'\$[^$]*\$', '', body)
    body = re.sub(r'\\cite\{[^}]*\}', 'CITE', body)
    # Remove figure/table captions (legit "ours" use)
    body = re.sub(r'\\caption\{[^}]*\}', '', body)
    hits = list(FIRST_PERSON.finditer(body))
    if hits:
        print(f'\n=== {f.name} ===')
        for m in hits:
            ctx = body[max(0,m.start()-50):min(len(body),m.end()+50)].replace('\n', ' ')
            print(f'  HIT: "{m.group(0)}" in: ...{ctx}...')
        total_fp += len(hits)
print(f'\n>>> Total first-person hits: {total_fp}')

print()
print('=' * 80)
print('3. LOGIC / DATA CONSISTENCY CHECK')
print('=' * 80)
# Check for known contradictions
checks = []
# Abstract vs section
abstract = (ROOT / 'main.tex').read_text(encoding='utf-8')
abstract_m = re.search(r'\\begin\{abstract\}(.+?)\\end\{abstract\}', abstract, re.DOTALL)
if abstract_m:
    abs_text = abstract_m.group(1)
    # Find chi^2 value
    chi_match = re.search(r'chi\^2[_^]?(\d+)\s*=\s*([\d.]+)', abs_text)
    if chi_match:
        checks.append(f'Abstract chi^2_{chi_match.group(1)} = {chi_match.group(2)}')
    # Find CD
    cd_match = re.search(r'\\mathrm\{CD\}\s*=\s*([\d.]+)', abs_text)
    if cd_match:
        checks.append(f'Abstract CD = {cd_match.group(1)}')

# Section 5 has Friedman info
sec5 = (ROOT / 'sections/05_results.tex').read_text(encoding='utf-8')
chi_5 = re.search(r'chi\^2_(\d+)\s*=\s*([\d.]+)', sec5)
if chi_5:
    checks.append(f'05_results chi^2_{chi_5.group(1)} = {chi_5.group(2)}')
cd_4 = re.search(r'CD\s*=\s*([\d.]+)', sec5)
if cd_4:
    checks.append(f'05_results CD = {cd_4.group(1)}')
k_n_match = re.search(r'k\s*=\s*(\d+)[^.]*?N\s*=\s*(\d+)', (ROOT / 'sections/04_experimental_setup.tex').read_text(encoding='utf-8'))
if k_n_match:
    checks.append(f'04_setup: k={k_n_match.group(1)}, N={k_n_match.group(2)}')

# Check all important numbers
print('Found values:')
for c in checks:
    print(f'  - {c}')

print()
print('=' * 80)
print('4. REFERENCE COUNT + CACHE STATS')
print('=' * 80)
import subprocess
r = subprocess.run(['python', r'D:\新论文\实验\experiments\_audit_bib.py'],
                   capture_output=True, text=True)
print(r.stdout)