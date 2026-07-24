"""Comprehensive scan of all .tex for first-person + AI tells + logic + internal consistency."""
import re
import os
from pathlib import Path

ROOT = Path(r'D:\新论文\论文')
SECTIONS = [
    '01_introduction.tex', '02_related_work.tex', '03_method.tex',
    '03_theory.tex', '04_experimental_setup.tex', '05_results.tex',
    '06_discussion.tex', '07_conclusion.tex', 'A_appendix.tex',
    'B_highlights.tex',
]

# First-person triggers (case-insensitive, word boundary)
FIRST_PERSON = [
    r'\bI\b(?!\w)',                       # I (not followed by alnum)
    r'\bwe\b(?!\w)',                      # we
    r"\bour\b(?!')",                       # our (not followed by apostrophe)
    r"\bus\b(?!')",                        # us
    r'\bme\b(?!\w)',                       # me
    r'\bmy\b(?!\w)',                       # my
    r'\bmyself\b',
    r'\bourselves\b',
    r'\bthe\s+author(?:s)?\s+(?:propos|develop|present|introduc|conduct|investigat|examin|explor|design|implement|evaluat|report|show|demonstrat|argu|sugges|provid|analyz|us|aim|attempt|believ|claim|consider|discus|focu|hop|intend|not|observ|perform|plan|propos|refer|state|studi|think|us|work)\w*\b',
    r'\bIn\s+this\s+(?:paper|work|study|article|manuscript|note),\s+(?:we|I)\b',
    r'\bThis\s+(?:paper|work|study|article|manuscript)\s+(?:propos|develop|present|introduc|report|show|demonstrat|investigat|aim|provid|describ)\w*\b',
]

# AI-tell phrases (high-frequency LLM output)
AI_TELLS = [
    r'\bIt is worth (?:noting|mentioning)\b',
    r'\bIt should be (?:noted|mentioned)\b',
    r'\bNote that\b',
    r'\bNotably,?\s',
    r'\bImportantly,?\s',
    r'\bIn recent years\b',
    r'\bWith the (?:rapid )?development of\b',
    r'\bIn the (?:era|age) of\b',
    r'\bmore and more\b',
    r'\bplays? a (?:crucial|pivotal|key|critical|essential|important) role\b',
    r'\b(?:huge|vast|immense|enormous) potential\b',
    r'\bvery (?:challenging|important|interesting)\b',
    r'\bin conclusion,?\s',
    r'\bto the best of (?:our|my|the author) knowledge\b',  # may be acceptable, just note
    r'\bfuture work\b',
    r'\bIt is (?:important|essential|interesting|worth) to\b',
    r'\bhas emerged as a\b',
    r'\bgain(?:s|ed)? (?:significant|substantial|considerable) (?:attention|interest|traction)\b',
    r'\bDespite (?:its|their) (?:challenges|complexities),?\b',
    r'\bA growing (?:body of )?(?:number of )?(?:research|interest|attention)\b',
    r'\b(?:opens?|opening) (?:up )?new (?:avenues|possibilities|horizons|opportunities)\b',
    r'\bdelve(?:s|d)? into\b',
    r'\bcomprehensive (?:survey|review|analysis|study|understanding)\b',
    r'\bboth the (?:theoretical|practical) (?:and|as well as)\b',
]

# Logic/consistency check: known data facts
DATA_FACTS = {
    'TLE_8UAV_f1_vs_DE_p': 0.4856,
    'TLE_8UAV_vs_DNSGA_p': 0.0000,
    'TLE_16UAV_vs_DNSGA_p': 0.0312,
    'TLE_32UAV_vs_DNSGA_p': 0.0312,
    'TLE_vs_DNSGA_8UAV_pct': -21.2,
    'TLE_vs_DNSGA_16UAV_pct': -20.4,
    'TLE_vs_DNSGA_32UAV_pct': -19.0,
}

print('=' * 80)
print('FIRST-PERSON + AI-TELL SCAN')
print('=' * 80)

for fn in SECTIONS:
    p = ROOT / 'sections' / fn
    if not p.exists():
        continue
    text = p.read_text(encoding='utf-8')
    print(f'\n=== {fn} (length: {len(text)}) ===')

    # Strip TeX commands/comments for cleaner scan? No, keep them.
    # Strip comments
    body = re.sub(r'%.*', '', text)

    fp_found = []
    for pat in FIRST_PERSON:
        matches = list(re.finditer(pat, body, re.IGNORECASE))
        for m in matches:
            # Get surrounding context (40 chars)
            start = max(0, m.start() - 30)
            end = min(len(body), m.end() + 30)
            ctx = body[start:end].replace('\n', ' ')
            fp_found.append((m.group(0), ctx))

    if fp_found:
        print(f'  FIRST-PERSON ({len(fp_found)} hits):')
        for tok, ctx in fp_found:
            print(f'    >>> "{tok}" in: ...{ctx}...')
    else:
        print('  [OK] No first-person')

    ai_found = []
    for pat in AI_TELLS:
        matches = list(re.finditer(pat, body, re.IGNORECASE))
        for m in matches:
            start = max(0, m.start() - 25)
            end = min(len(body), m.end() + 25)
            ctx = body[start:end].replace('\n', ' ')
            ai_found.append((m.group(0), ctx))

    if ai_found:
        print(f'  AI-TELL ({len(ai_found)} hits):')
        for tok, ctx in ai_found[:8]:  # limit to 8
            print(f'    >>> "{tok}" in: ...{ctx}...')
        if len(ai_found) > 8:
            print(f'    ... ({len(ai_found)-8} more)')

# Main abstract scan
print('\n' + '=' * 80)
print('MAIN.TEX / COVER_LETTER SCAN')
print('=' * 80)
for fn in ['main.tex', 'cover_letter.tex']:
    p = ROOT / fn
    if not p.exists():
        continue
    text = p.read_text(encoding='utf-8')
    body = re.sub(r'%.*', '', text)
    print(f'\n=== {fn} ===')

    fp_found = []
    for pat in FIRST_PERSON:
        matches = list(re.finditer(pat, body, re.IGNORECASE))
        for m in matches:
            start = max(0, m.start() - 30)
            end = min(len(body), m.end() + 30)
            ctx = body[start:end].replace('\n', ' ')
            fp_found.append((m.group(0), ctx))
    if fp_found:
        print(f'  FIRST-PERSON ({len(fp_found)} hits):')
        for tok, ctx in fp_found[:5]:
            print(f'    >>> "{tok}" in: ...{ctx}...')
        if len(fp_found) > 5:
            print(f'    ... ({len(fp_found)-5} more)')

    ai_found = []
    for pat in AI_TELLS:
        matches = list(re.finditer(pat, body, re.IGNORECASE))
        for m in matches:
            start = max(0, m.start() - 25)
            end = min(len(body), m.end() + 25)
            ctx = body[start:end].replace('\n', ' ')
            ai_found.append((m.group(0), ctx))
    if ai_found:
        print(f'  AI-TELL ({len(ai_found)} hits):')
        for tok, ctx in ai_found[:5]:
            print(f'    >>> "{tok}" in: ...{ctx}...')
        if len(ai_found) > 5:
            print(f'    ... ({len(ai_found)-5} more)')