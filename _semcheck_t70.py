#!/usr/bin/env python3
"""T70 final semantic check: verify all 4 review aspects are addressed."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

files = {
    'main': r'D:\新论文\论文\_submission\main_submission.tex',
    'supp': r'D:\新论文\论文\_submission\supplementary_material.tex',
    'cover': r'D:\新论文\论文\_submission\cover_letter.tex',
}

# Aspect 1: First-person pronouns
print("=" * 70)
print("ASPECT 1: First-person pronouns (we/I/our/us) - should be 0")
print("=" * 70)
for label, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    we = len(re.findall(r'\bwe\b', content, re.IGNORECASE))
    our = len(re.findall(r'\bour\b', content, re.IGNORECASE))
    us = len(re.findall(r'\bus\b', content, re.IGNORECASE))
    print(f"  {label:6s}: we={we}, our={our}, us={us}")

# Aspect 2: AI-tell phrases
print()
print("=" * 70)
print("ASPECT 2: AI-tell phrases (count occurrences)")
print("=" * 70)
ai_phrases = ['delve', 'leverage', 'leverages', 'leveraging', 'leverage',
              'robust', 'comprehensive', 'facilitate', 'facilitates',
              'harness', 'harnesses', 'elucidate', 'elucidates',
              'in conclusion', 'it is worth noting', 'to summarize',
              'orchestrate', 'orchestrated', 'orchestration',
              'in the realm of', 'navigate the complexities',
              'plethora', 'intricate', 'pivotal', 'paramount',
              'transformative', 'game-changer', 'game-changing',
              'revolutionary', 'paradigm shift',
              'moreover', 'furthermore', 'indeed,', 'crucially,',
              'importantly,', 'remarkably,', 'notably,',
              'tapestry', 'symphony', 'this paper', 'this manuscript',
              'this study', 'this work']
for label, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"  {label}:")
    for p in ai_phrases:
        n = len(re.findall(re.escape(p), content, re.IGNORECASE))
        if n > 0:
            print(f"    '{p}' = {n}")

# Aspect 3: Scope alignment mentions
print()
print("=" * 70)
print("ASPECT 3: Scope-alignment keywords (SWEVO scope, DE, memetic, hybrid, DMO)")
print("=" * 70)
scope_kw = ['SWEVO', 'scope', 'Differential Evolution', 'memetic',
            'hybrid', 'metaheuristic', 'swarm', 'evolutionary computation',
            'algorithm hybrid', 'hybridization', 'Pareto', 'DMO',
            'dynamic multi-objective', 'engineering application',
            'real-world', 'multi-UAV', 'UAV', 'unmanned aerial vehicle']
for label, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"  {label}:")
    for kw in scope_kw:
        n = len(re.findall(re.escape(kw), content, re.IGNORECASE))
        if n > 0:
            print(f"    '{kw}' = {n}")

# Aspect 4: Abbreviation first-occurrence full-name coverage
print()
print("=" * 70)
print("ASPECT 4: Abbreviation first-occurrence coverage in main")
print("=" * 70)
abbrevs = {
    'LLM': 'large language model',
    'LLM-EC': 'large-language-model evolutionary computation',
    'LLM-EA': 'LLM-enhanced evolutionary algorithm',
    'DMO': 'dynamic multi-objective optimization',
    'CEC': 'Congress on Evolutionary Computation',
    'IGD': 'inverted generational distance',
    'HV': 'hypervolume',
    'UCB1': 'Upper Confidence Bound 1',
    'UAV': 'unmanned aerial vehicle',
    'JSON': 'JavaScript object notation',
    'DE': 'differential evolution',
    'NSGA-II': 'Non-dominated Sorting Genetic Algorithm II',
    'DNSGA-II-A': 'Dynamic NSGA-II with random immigrants',
    'PPS': 'Population Prediction Strategy',
    'MOEA/DD': 'Multi-Objective Evolutionary Algorithm based on Dominance and Decomposition',
    'PlatEMO': '',  # No full name
    'DTLZ': '',  # No full name, well-known
    'DMOEA': 'dynamic multi-objective evolutionary algorithm',
    'Pareto': 'Pareto',
    'CoT': 'chain-of-thought',
    'RLHF': 'reinforcement learning from human feedback',
    'TLE': 'Triggered LLM-Enhanced Evolutionary Algorithm',
    'Qwen': '',
    'Ollama': '',
}
for label, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"  {label}:")
    for abbr, full in abbrevs.items():
        if not full:
            continue
        # Find first occurrence position
        m = re.search(r'\b' + re.escape(abbr) + r'\b', content)
        if not m:
            continue
        # Check if full name appears within 200 chars BEFORE
        window = content[max(0, m.start() - 200):m.start()]
        # Also check if the full name appears anywhere before
        first_full = content.find(full)
        if first_full == -1:
            print(f"    '{abbr}' ({full}): NOT DEFINED ANYWHERE")
        elif first_full > m.start():
            print(f"    '{abbr}' ({full}): defined AFTER first use (at offset {first_full} vs use at {m.start()})")
        else:
            # Check if it's within 200 chars
            if m.start() - first_full < 200:
                pass  # Good
            else:
                # Far away but defined before - still acceptable for big papers
                pass

# Final check: stale numbers in main
print()
print("=" * 70)
print("STALE-NUMBER CHECK in main_submission.tex")
print("=" * 70)
stale = [
    ('5,156 entries', 'should be 17,226'),
    ('215-run', 'should be 2,520-run'),
    ('5,156', 'should be 17,226'),
    ('n=8 seeds', 'should be n=30'),
    ('RTX 5070', 'should be RTX 4090'),
    ('8 seeds all produce', 'should be 30 seeds all produce'),
    ('all 215 runs', 'should be all 2,520 runs'),
]
with open(files['main'], 'r', encoding='utf-8') as f:
    content = f.read()
for pat, expected in stale:
    if pat in content:
        print(f"  STILL STALE: '{pat}' ({expected})")
    else:
        print(f"  OK: '{pat}' removed")

# And in supp
print()
print("=" * 70)
print("STALE-NUMBER CHECK in supplementary_material.tex")
print("=" * 70)
with open(files['supp'], 'r', encoding='utf-8') as f:
    content = f.read()
stale_supp = [
    ('5,156', 'should be 17,226'),
    ('all 215 runs', 'should be all 2,520 runs'),
    ('eight seeds', 'should be 30 seeds'),
    ('B_max = 60', 'should be 50'),
    ('37 GPU-h', 'should be 22-24 h'),
    ('n = 5 seeds', 'should be n = 30 (for ablation)'),  # might appear legitimately for sensitivity
]
for pat, expected in stale_supp:
    if pat in content:
        # Check context
        idx = content.find(pat)
        ctx = content[max(0, idx-50):idx+50]
        print(f"  STILL PRESENT: '{pat}' ({expected})")
        print(f"    Context: ...{ctx}...")
    else:
        print(f"  OK: '{pat}' removed")
