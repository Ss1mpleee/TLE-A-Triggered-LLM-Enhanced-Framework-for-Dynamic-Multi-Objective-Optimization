with open(r'D:\新论文\论文\_submission\main_submission.tex', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')
line846 = lines[845]
D = chr(36)
print('has V' + D + '1' + D + ':', ('V' + D + '1' + D) in line846)
print('has V1:', 'V1' in line846)
idx = line846.find('V1')
print('byte content around V1:')
print(repr(line846[idx-5:idx+15]))
# Also count T$x$ and V$x$ (with $) using raw bytes
import re
# Use raw string for the dollar
raw_dollar = '\\$'
pat = 'V' + raw_dollar + r'([0-3])' + raw_dollar
ms = re.findall(pat, line846)
print('V$x$ count:', len(ms), 'matches:', ms)
pat_t = 'T' + raw_dollar + r'([0-3])' + raw_dollar
ms_t = re.findall(pat_t, line846)
print('T$x$ count:', len(ms_t), 'matches:', ms_t)
