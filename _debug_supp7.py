#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\新论文\论文\_submission\supplementary_material.tex', 'r', encoding='utf-8') as f:
    content = f.read()
# Find 'sec' literal
idx = 0
for i in range(5):
    idx = content.find('sec', idx+1)
    if idx == -1: break
    print(f'Found sec at {idx}:', repr(content[idx:idx+30]))
