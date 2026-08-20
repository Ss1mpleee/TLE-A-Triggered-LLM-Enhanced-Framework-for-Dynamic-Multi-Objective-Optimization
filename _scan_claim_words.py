#!/usr/bin/env python3
"""T70: find all new/novel/first/proposed/innovative/pioneer/newly/fresh/propose
instances in the 3 tex files, with surrounding context for the user to review.
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

files = {
    'main': r'D:\新论文\论文\_submission\main_submission.tex',
    'supp': r'D:\新论文\论文\_submission\supplementary_material.tex',
    'cover': r'D:\新论文\论文\_submission\cover_letter.tex',
}

# Words that may overclaim
patterns = [
    (r'\bnew\b', 'new'),
    (r'\bnovel\b', 'novel'),
    (r'\bfirst\b', 'first'),
    (r'\bnewly\b', 'newly'),
    (r'\binnovative\b', 'innovative'),
    (r'\bpioneer(?:ing|s)?\b', 'pioneer'),
    (r'\bpropose[ds]?\b', 'propose'),
    (r'\bintroduce[ds]?\b', 'introduce'),  # often paired with "novel"
    (r'\bfresh\b', 'fresh'),
    (r'\bcutting-edge\b', 'cutting-edge'),
    (r'\bstate-of-the-art\b', 'state-of-the-art'),
    (r'\bgroundbreaking\b', 'groundbreaking'),
]

for label, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    print(f"\n=== {label} ({path}) ===")
    for pat, name in patterns:
        for i, line in enumerate(lines, 1):
            for m in re.finditer(pat, line, re.IGNORECASE):
                # Show 50 chars before, the match, 80 chars after
                start = max(0, m.start() - 50)
                end = min(len(line), m.end() + 80)
                context = line[start:end]
                # Replace the matched word with [TAG]
                tag_start = m.start() - start
                tag = '[[' + name + ']]'
                # Just print
                print(f"  L{i}: ...{context[:tag_start]}{tag}{context[tag_start+len(m.group()):]}")
