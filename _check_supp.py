import re
with open(r'D:\新论文\论文\_submission\supplementary_material.tex', 'r', encoding='utf-8') as f:
    content = f.read()
# Try with raw string
matches = re.findall(r'V\$([0-3])\$', content)
print('V$x$ count:', len(matches), matches)
matches2 = re.findall(r'T\$([0-3])\$', content)
print('T$x$ count:', len(matches2), matches2)
