#!/usr/bin/env python3
"""T70 detailed first-occurrence check: 50-char window for full-name presence."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

def find_first_with_definition(content, abbr, full_pattern):
    """Find the first occurrence of abbreviation and check if full name appears in 100 chars before or 30 chars after."""
    for m in re.finditer(r'\b' + re.escape(abbr) + r'\b', content):
        pos = m.start()
        # Check 100 chars before
        before = content[max(0, pos-150):pos]
        after = content[pos:pos+50]
        if re.search(full_pattern, before, re.IGNORECASE) or re.search(full_pattern, after, re.IGNORECASE):
            return (pos, 'OK', f"defined nearby")
        # Also check "common abbreviations" paragraph
        if 'abbreviations are summarised' in before.lower() or 'abbreviations used' in before.lower():
            return (pos, 'OK (abbrev block)', f"in common-abbreviations block")
    return None

files = {
    'main': r'D:\新论文\论文\_submission\main_submission.tex',
    'supp': r'D:\新论文\论文\_submission\supplementary_material.tex',
    'cover': r'D:\新论文\论文\_submission\cover_letter.tex',
}

# For main: skip the title block (first 200 lines are title/authors/abstract/intro)
# We need to find the FIRST IN-TEXT occurrence (not title)

# Just check each abbreviation manually with proper context check
checks = {
    'IGD': [r'inverted generational distance'],
    'HV': [r'hypervolume'],
    'UCB1': [r'upper confidence bound 1', r'upper confidence bound'],
    'DMO': [r'dynamic multi-objective optimization', r'dynamic multi-objective optimisation'],
    'CEC': [r'congress on evolutionary computation'],
    'LLM-EC': [r'large-language-model evolutionary computation', r'large language model evolutionary computation'],
    'LLM-EA': [r'LLM-enhanced evolutionary algorithm'],
    'DNSGA-II-A': [r'Dynamic NSGA-II with random immigrants', r'Dynamic NSGA-II'],
    'PPS-DMOEA': [r'Population Prediction Strategy', r'PPS-DMOEA'],  # PPS is defined; -DMOEA is appended
    'MOEA/DD': [r'Multi-Objective Evolutionary Algorithm based on Dominance and Decomposition', r'multi-objective evolutionary algorithm'],
    'JSON': [r'JavaScript object notation'],
    'UAV': [r'unmanned aerial vehicle', r'Unmanned Aerial Vehicle'],
    'DE': [r'differential evolution', r'Differential Evolution'],
    'NSGA-II': [r'non-dominated sorting genetic algorithm ii', r'Non-dominated Sorting Genetic Algorithm II'],
    'PPS': [r'Population Prediction Strategy'],
    'DMOEA': [r'dynamic multi-objective evolutionary algorithm'],
    'RLHF': [r'reinforcement learning from human feedback'],
    'CoT': [r'chain-of-thought', r'chain of thought'],
    'DTLZ': [],  # well-known
    'PlatEMO': [],
    'TLE': [r'Triggered LLM-Enhanced Evolutionary Algorithm', r'triggered llm-enhanced evolutionary algorithm'],
    'CD': [r'critical difference', r'critical-difference'],
    'DTLZ-variant': [],
}

print("=" * 70)
print("DETAILED first-occurrence check (150-char window before)")
print("=" * 70)

for label, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"\n  === {label} ===")
    for abbr, patterns in checks.items():
        if not patterns:
            print(f"  {abbr:15s}: (well-known, no definition required)")
            continue
        for m in re.finditer(r'\b' + re.escape(abbr) + r'\b', content):
            pos = m.start()
            # Get 200 chars before and 50 after
            before = content[max(0, pos-200):pos]
            after = content[pos:pos+50]
            # Check if any full pattern is in the before/after window
            found = False
            for p in patterns:
                if re.search(p, before, re.IGNORECASE) or re.search(p, after, re.IGNORECASE):
                    found = True
                    break
            if found:
                # OK - defined in window
                break
            # If not found, check if there's a "common abbreviations" block in the before
            if 'abbreviations' in before.lower() and ('summari' in before.lower() or 'expanded' in before.lower() or 'defined' in before.lower()):
                break
            # If this is the first occurrence and not defined, report it
            print(f"  {abbr:15s}: NOT DEFINED at first use (offset {pos})")
            print(f"      Before: ...{content[max(0,pos-80):pos]}")
            print(f"      After:  {content[pos:pos+80]}...")
            break
