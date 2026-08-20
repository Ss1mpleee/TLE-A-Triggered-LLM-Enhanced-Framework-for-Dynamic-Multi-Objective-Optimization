import re
DOLLAR = chr(36)
with open(r'D:\新论文\论文\_submission\main_submission.tex', 'r', encoding='utf-8') as f:
    raw = f.read()

# Test the pattern on a known line 846
lines = raw.split('\n')
line846 = lines[845]
pat = re.compile(r"V" + DOLLAR + r"([0-3])" + DOLLAR)
matches = pat.findall(line846)
print("V$x$ matches in line 846:", matches)
new_line, count = pat.subn("T" + DOLLAR + r"\1" + DOLLAR, line846)
print("replaced count:", count)
print("old line V1..V3 area:")
print(line846[410:500])
print("new line V1..V3 area:")
print(new_line[410:500])
