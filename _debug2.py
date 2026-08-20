import re
DOLLAR = chr(36)
with open(r'D:\新论文\论文\_submission\main_submission.tex', 'r', encoding='utf-8') as f:
    raw = f.read()
lines = raw.split('\n')
line846 = lines[845]

# Try multiple patterns
pat1 = re.compile(r"V" + DOLLAR + r"([0-3])" + DOLLAR)
pat2 = re.compile(r"V\$([0-3])\$")
pat3 = re.compile(r"V\$([0-3])\$", re.UNICODE)
pat4 = re.compile(r"V" + DOLLAR + r"([0-3])" + DOLLAR, re.UNICODE)

print("pat1 (concat chr36):", pat1.findall(line846))
print("pat2 (raw $):", pat2.findall(line846))
print("pat3 (raw $ + UNICODE):", pat3.findall(line846))
print("pat4 (concat chr36 + UNICODE):", pat4.findall(line846))

# Try a simpler test
test = "V" + DOLLAR + "1" + DOLLAR + " (2.143) < V" + DOLLAR + "0" + DOLLAR
print("test string:", repr(test))
print("pat1 on test:", pat1.findall(test))
print("pat2 on test:", pat2.findall(test))
