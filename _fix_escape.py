#!/usr/bin/env python3
"""Fix the \\nSWEVO escape error in main_submission.tex Appendix A.3."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = r'D:\新论文\论文\_submission\main_submission.tex'
with open(f, 'r', encoding='utf-8') as fh:
    content = fh.read()

# The file currently has: 7950X \\\nSWEVO  (3 backslashes + n)
# We want:                 7950X \\\nSWEVO  (2 backslashes + real newline + nSWEVO...)
# In Python literal: "\\\\\\n" = 5 chars: \ \ \ \ n   (no, that's 4 backslashes + n)
# The actual content has the bytes: 5c5c5c 6e = \\\n (3 backslashes + n char)
# We need to replace this with: 5c5c 0a (\\) + real newline

# Find the bad sequence and replace
# Bad: 7950X \\\nSWEVO
# Good: 7950X \\\nSWEVO (where the \n is a real newline char, not a backslash + n)

bad = '7950X \\\\\nSWEVO'  # 3 backslashes + n + SWEVO
print('bad in content:', bad in content)

good = '7950X \\\\\nSWEVO'  # 2 backslashes + real newline + SWEVO (Python interprets \n as newline)
print('good target length:', len(good), 'bad length:', len(bad))

# In Python, the bad string is 14 chars: 7 9 5 0 X space \ \ \ n S W E V O
# We want to replace the 3 backslashes + n with 2 backslashes + newline

# Let's use a more direct approach: read raw bytes
with open(f, 'rb') as fh:
    raw = fh.read()
bad_bytes = b'7950X \\\\\\nSWEVO'  # 3 backslashes + n + SWEVO
print('bad_bytes in raw:', bad_bytes in raw)
good_bytes = b'7950X \\\\\nSWEVO'  # 2 backslashes + real newline + SWEVO
print('good_bytes length:', len(good_bytes))

# The bad bytes 5c5c5c 6e should be in the file
bad_pattern = b'\\\\\\n'  # 3 backslashes + n
print('bad_pattern 5c5c5c6e in raw:', bad_pattern in raw)

# Replace the bad pattern with 2 backslashes + newline
new_raw = raw.replace(b'\\\\\\n', b'\\\\\n')
# Wait, in Python b'\\\\\\n' = 4 bytes: \ \ \ \ \ n (5 backslashes) + ... hmm
# Let me think. b'\\\\' = 2 bytes \\, b'\\n' = 2 bytes \n
# So b'\\\\\\n' = 4 bytes: \ \ \ n (3 backslashes + n)
# That matches the bad pattern 5c5c5c6e

new_raw = raw.replace(b'\\\\\\n', b'\\\\\n')
# new_raw's pattern b'\\\\\n' = 3 bytes: \ \ \n (2 backslashes + newline) - wait, \n in Python bytes is 0x0a (newline) not 5c6e
# So b'\\\\\n' = 5 bytes: 5c 5c 0a (\\ followed by newline)

# Verify
print('new pattern in new_raw:', b'\\\\\n' in new_raw)
print('Remaining bad pattern:', b'\\\\\\n' in new_raw)

with open(f, 'wb') as fh:
    fh.write(new_raw)
print('Saved.')

# Verify
with open(f, 'rb') as fh:
    check = fh.read()
idx = check.find(b'SWEVO scope fit')
print('Context:')
print(repr(check[idx-30:idx+50]))
