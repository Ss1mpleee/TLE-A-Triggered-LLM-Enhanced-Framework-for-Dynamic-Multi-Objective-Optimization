import re
with open(r'D:\新论文\论文\main.tex', 'r', encoding='utf-8') as f:
    text = f.read()
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', text, re.DOTALL)
abs_text = m.group(1)
print(f'Abstract length: {len(abs_text)}')
# Find UAV sentence
sent = re.search(r'on the 8-UAV scenario.*?fleet sizes\.', abs_text, re.DOTALL)
if sent:
    print('UAV sentence:')
    print(sent.group(0))
else:
    print('UAV sentence not found with new pattern')
    # Search for 8-UAV context
    for m2 in re.finditer(r'.{50}8-UAV.{200}', abs_text, re.DOTALL):
        print(m2.group(0))