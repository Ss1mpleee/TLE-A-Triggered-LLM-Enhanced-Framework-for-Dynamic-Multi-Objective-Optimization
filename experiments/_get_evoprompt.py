"""Get EvoPrompt arxiv abstract."""
import urllib.request, re
req = urllib.request.Request('http://export.arxiv.org/api/query?id_list=2309.08532', headers={'User-Agent': 'TLE-audit/1.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = resp.read().decode('utf-8')
# Title is the second <title> in entry
titles = re.findall(r'<title>(.*?)</title>', data, re.DOTALL)
print('Titles found:', len(titles))
for i, t in enumerate(titles):
    t = t.replace('\n', ' ').strip()
    print(f'  [{i}] {t[:120]}')

# Authors
authors = re.findall(r'<author>\s*<name>(.*?)</name>', data, re.DOTALL)
print(f'\nAuthors: {authors}')

# Year
y_m = re.search(r'<published>(\d{4})', data)
print(f'Year: {y_m.group(1) if y_m else "?"}')

# Comment for ICLR
c_m = re.search(r'<arxiv:comment>(.*?)</arxiv:comment>', data, re.DOTALL)
print(f'Comment: {c_m.group(1) if c_m else "?"}')
