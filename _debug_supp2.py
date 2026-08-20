#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\新论文\论文\_submission\supplementary_material.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Find context
target = r'\texttt{results/raw/sec\_main\_v3.json}'
idx = content.find(target)
print('idx:', idx)
if idx > 0:
    print('Context:')
    print(repr(content[idx:idx+400]))
