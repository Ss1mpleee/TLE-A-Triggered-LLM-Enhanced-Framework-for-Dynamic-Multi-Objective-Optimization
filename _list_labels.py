#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\新论文\论文\_submission\main_submission.tex', 'r', encoding='utf-8') as f:
    content = f.read()
import re
for m in re.finditer(r'\\label\{sec:[^}]+\}', content):
    print(m.group())
print('---')
for m in re.finditer(r'\\label\{tab:[^}]+\}', content):
    print(m.group())
