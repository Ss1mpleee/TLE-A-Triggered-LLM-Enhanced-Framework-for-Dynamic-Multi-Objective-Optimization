"""Verify OPRO paper via arXiv."""
import urllib.request, re
req = urllib.request.Request('http://export.arxiv.org/api/query?id_list=2309.03409', headers={'User-Agent': 'TLE-audit/1.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = resp.read().decode('utf-8')
titles = re.findall(r'<title>(.*?)</title>', data, re.DOTALL)
authors = re.findall(r'<author>\s*<name>(.*?)</name>', data, re.DOTALL)
c = re.search(r'<arxiv:comment>(.*?)</arxiv:comment>', data, re.DOTALL)
print(f'Title: {titles[1] if len(titles) > 1 else "?"}')
print(f'Authors: {", ".join(authors[:5])}')
print(f'Comment: {c.group(1) if c else "?"}')

# Also try crossref for journal version
import urllib.request, json
doi = '10.1145/3639049.3640123'  # ICLR 2024 might not have DOI
# Actually, check ICLR proceedings
print('\n=== Try as conference paper ===')
