#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\新论文\论文\_submission\supplementary_material.tex', 'r', encoding='utf-8') as f:
    content = f.read()
# Use raw string regex
import re
for m in re.finditer(r'sec_\w+', content):
    print('Found:', repr(m.group()), 'at', m.start())
