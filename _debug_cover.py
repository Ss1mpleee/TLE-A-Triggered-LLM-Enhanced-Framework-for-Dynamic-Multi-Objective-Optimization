#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\新论文\论文\_submission\cover_letter.tex', 'r', encoding='utf-8') as f:
    content = f.read()
# Try different strings
test1 = r"fleet sizes 8/16/32 (Wilcoxon $\\mathbf{p} \\leq 0.0312$)"
print('test1 in content:', test1 in content)
test2 = r"fleet sizes 8/16/32 (Wilcoxon $\mathbf{p} \leq 0.0312$)"
print('test2 in content:', test2 in content)
# Show actual
idx = content.find('fleet sizes 8/16/32')
print('Context:')
print(repr(content[idx:idx+100]))
