"""Strict first-person + 'this paper presents' scan."""
import re
from pathlib import Path

ROOT = Path(r'D:\新论文\论文')
files = sorted(list((ROOT / 'sections').glob('*.tex'))) + [ROOT / 'main.tex', ROOT / 'cover_letter.tex', ROOT / 'supplementary_material.tex']

# Strict: real pronouns only. Skip LaTeX subscripts (\mu_a etc) and math ($, etc).
# Pattern: word boundary, not preceded by backslash or alnum
pronoun_pat = re.compile(
    r"(?<![\\\w])"           # not preceded by \ or word char
    r"(we|us|our|ours|ourselves)"
    r"(?![\\\w'])",           # not followed by \ or word char or apostrophe
    re.IGNORECASE
)
i_pat = re.compile(
    r"(?<![\\\w])"            # not preceded by \ or word char
    r"\bI\b"                  # standalone I
    r"(?![\\\w'])"            # not followed by \ or word char
)

# "This paper/work/study + verb" — borderline active-voice, soft-target
this_paper_pat = re.compile(
    r"\b(this|the present|the current)\s+"
    r"(paper|work|study|article|manuscript|note|research)\s+"
    r"(propos|develop|present|introduc|report|show|demonstrat|investigat|aim|provid|describ|focus|focuses|examines)\w*\b",
    re.IGNORECASE
)

# "we ran / we performed" — hard violation
we_verb_pat = re.compile(
    r"(?<![\\\w])(we|We|WE)\s+(propos|develop|present|introduc|conduct|investigat|examin|explor|design|implement|evaluat|report|show|demonstrat|argu|sugges|provid|analyz|aim|attempt|believ|claim|consider|discus|focu|hop|intend|observ|perform|plan|refer|state|studi|think|work|ran|find|present|utiliz|employ|adopt|use|show|observe|conducted|carried|did)\w*\b",
)

print('=' * 80)
print('STRICT FIRST-PERSON + THIS-PAPER SCAN')
print('=' * 80)

for fp in files:
    if not fp.exists(): continue
    txt = fp.read_text(encoding='utf-8')
    body = re.sub(r'%.*', '', txt)

    # Strip math mode content
    body_no_math = re.sub(r'\$[^$]*\$', '', body)
    # Strip \cite{...} content
    body_no_math = re.sub(r'\\cite\{[^}]*\}', 'CITE', body_no_math)

    we_hits = [(m.start(), m.group(0)) for m in pronoun_pat.finditer(body_no_math)]
    i_hits = [(m.start(), m.group(0)) for m in i_pat.finditer(body_no_math)]
    we_verb = [(m.start(), m.group(0)) for m in we_verb_pat.finditer(body_no_math)]
    this_p = [(m.start(), m.group(0)) for m in this_paper_pat.finditer(body_no_math)]

    if we_hits or i_hits or we_verb or this_p:
        print(f'\n=== {fp.name} ===')
        for start, tok in we_hits:
            ctx = body_no_math[max(0,start-50):min(len(body_no_math),start+80)].replace('\n', ' ')
            print(f'  WE/OUR \"{tok}\" in: ...{ctx}...')
        for start, tok in i_hits:
            ctx = body_no_math[max(0,start-50):min(len(body_no_math),start+80)].replace('\n', ' ')
            print(f'  I \"{tok}\" in: ...{ctx}...')
        for start, tok in we_verb:
            ctx = body_no_math[max(0,start-50):min(len(body_no_math),start+80)].replace('\n', ' ')
            print(f'  WE+VERB \"{tok}\" in: ...{ctx}...')
        for start, tok in this_p:
            ctx = body_no_math[max(0,start-50):min(len(body_no_math),start+80)].replace('\n', ' ')
            print(f'  THIS-PAPER \"{tok}\" in: ...{ctx}...')

print('\nDONE.')