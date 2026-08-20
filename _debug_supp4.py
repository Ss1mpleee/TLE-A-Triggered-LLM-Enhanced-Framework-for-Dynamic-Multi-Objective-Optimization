#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\新论文\论文\_submission\supplementary_material.tex', 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('ablation')
print('idx:', idx)
if idx > 0:
    print('Context:')
    print(repr(content[idx-50:idx+400]))
