#!/usr/bin/env python3
"""Final scan: any remaining 'new' or 'novel' that describes the method."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

files = {
    'main': r'D:\新论文\论文\_submission\main_submission.tex',
    'supp': r'D:\新论文\论文\_submission\supplementary_material.tex',
    'cover': r'D:\新论文\论文\_submission\cover_letter.tex',
}

# Find any "novel" - should be 0
# Find any "new" that describes the method (TLE, framework, approach, method, algorithm)
# vs "new" that describes findings/data (new failure modes, new data, new ablations)

for label, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    print(f"\n=== {label} ===")

    # 1) Any "novel" - should be 0
    novel_lines = [(i, l) for i, l in enumerate(lines, 1) if re.search(r'\bnovel\b', l, re.IGNORECASE)]
    if novel_lines:
        print(f"  [novel] found {len(novel_lines)}x:")
        for i, l in novel_lines:
            print(f"    L{i}: {l[:150]}")
    else:
        print(f"  [novel] 0x ✓")

    # 2) "new" near TLE/method/framework
    method_words = ['TLE', 'framework', 'approach', 'method', 'algorithm', 'mechanism',
                    'architecture', 'strategy', 'paradigm', 'pipeline', 'module',
                    'scheduler', 'trigger', 'mapping', 'design']
    new_method_lines = []
    for i, line in enumerate(lines, 1):
        for m in re.finditer(r'\bnew\b', line, re.IGNORECASE):
            # Check 100 chars before
            before = line[max(0, m.start()-100):m.start()]
            after = line[m.end():m.end()+50]
            for w in method_words:
                if w.lower() in before.lower() or w.lower() in after.lower():
                    new_method_lines.append((i, m.start(), line))
                    break

    if new_method_lines:
        print(f"  [new near method word] found {len(new_method_lines)}x:")
        for i, pos, l in new_method_lines:
            print(f"    L{i} pos={pos}: {l[max(0,pos-30):pos+80]}")
    else:
        print(f"  [new near method word] 0x ✓")

    # 3) "new" near data/finding/result
    finding_words = ['data', 'failure', 'finding', 'result', 'run', 'ablation',
                     'extension', 'study', 'analysis', 'configuration']
    new_finding_lines = []
    for i, line in enumerate(lines, 1):
        for m in re.finditer(r'\bnew\b', line, re.IGNORECASE):
            before = line[max(0, m.start()-100):m.start()]
            after = line[m.end():m.end()+50]
            for w in finding_words:
                if w.lower() in before.lower() or w.lower() in after.lower():
                    new_finding_lines.append((i, pos, line))
                    break

    if new_finding_lines:
        print(f"  [new near finding word] (legitimate uses, kept): {len(new_finding_lines)}x")

    # 4) "innovative"
    innovative_lines = [(i, l) for i, l in enumerate(lines, 1) if re.search(r'\binnovative\b', l, re.IGNORECASE)]
    if innovative_lines:
        print(f"  [innovative] found {len(innovative_lines)}x:")
        for i, l in innovative_lines:
            print(f"    L{i}: {l[:150]}")
    else:
        print(f"  [innovative] 0x ✓")

    # 5) "pioneer"
    pioneer_lines = [(i, l) for i, l in enumerate(lines, 1) if re.search(r'\bpioneer', l, re.IGNORECASE)]
    if pioneer_lines:
        print(f"  [pioneer] found {len(pioneer_lines)}x:")
        for i, l in pioneer_lines:
            print(f"    L{i}: {l[:150]}")
    else:
        print(f"  [pioneer] 0x ✓")
