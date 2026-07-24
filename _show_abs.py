import re
with open(r'D:\新论文\论文\main.tex', 'r', encoding='utf-8') as f:
    text = f.read()
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', text, re.DOTALL)
if m:
    abs_text = m.group(1)
    print('Abstract length:', len(abs_text))
    print(abs_text)
    print()
    print('=== Duplicates check ===')
    print(f'Friedman test count: {abs_text.count("Friedman test reveals")}')
    print(f'CD = 3.408 count: {abs_text.count("CD = 3.408")}')
    print(f'8-UAV scenario count: {abs_text.count("8-UAV scenario")}')