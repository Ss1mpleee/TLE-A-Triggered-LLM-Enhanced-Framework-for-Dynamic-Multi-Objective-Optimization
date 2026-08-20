#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\新论文\论文\_submission\supplementary_material.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Test simple substring
test1 = 'sec\\_main'
print('test1 in content:', test1 in content)
# That's the python escape form
test2 = 'sec\\_main\\_v3'
print('test2 in content:', test2 in content)
# Test what we actually have
test3 = r'sec\_main\_v3'
print('test3 (raw string) in content:', test3 in content)
# Look at the actual bytes around
idx = content.find('main_v3')
print('idx of main_v3:', idx)
if idx > 0:
    print('Context:')
    print(repr(content[idx-15:idx+30]))
