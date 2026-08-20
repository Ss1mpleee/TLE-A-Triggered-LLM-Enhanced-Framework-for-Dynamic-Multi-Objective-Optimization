#!/usr/bin/env python3
"""T70 round 3: sync D:\\新论文\\论文\\sections/*.tex from the latest flat
D:\\新论文\\论文\\_submission\\main_submission.tex.

The flat file has the form:
  ...frontmatter...
  % >>> INLINED FROM: sections/01_introduction.tex >>>
  ...01_introduction body...
  % <<< END INLINED FROM: sections/01_introduction.tex <<<
  % >>> INLINED FROM: sections/02_related_work.tex >>>
  ...02_related_work body...
  ...

We extract each body and write to the corresponding section file.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

flat_path = Path(r'D:\新论文\论文\_submission\main_submission.tex')
sections_dir = Path(r'D:\新论文\论文\sections')

# Section mapping
section_map = {
    '01_introduction.tex': ('01_introduction',),
    '02_related_work.tex': ('02_related_work',),
    '03_method.tex': ('03_method',),
    '03_theory.tex': ('03_theory',),
    '04_experimental_setup.tex': ('04_experimental_setup',),
    '05_results.tex': ('05_results',),
    '06_discussion.tex': ('06_discussion',),
    '07_conclusion.tex': ('07_conclusion',),
    'A_appendix.tex': ('A_appendix',),
}

# Read flat file
with open(flat_path, 'r', encoding='utf-8') as f:
    flat = f.read()

# For each section, find the INLINED FROM marker and extract content
# Strategy: find all "INLINED FROM: sections/X.tex" markers, then for each,
# extract content from after the marker up to the next "INLINED FROM" or "END INLINED" marker
import re
all_starts = list(re.finditer(r'% >>> INLINED FROM: sections/(\w+\.tex) >>>', flat))

# Map name -> (start_idx, end_idx)
section_bounds = {}
for i, m in enumerate(all_starts):
    name = m.group(1)
    start = m.end() + 1  # after the marker line
    if i + 1 < len(all_starts):
        end = all_starts[i+1].start()
    else:
        # Find END INLINED or end of file
        end_marker = re.search(r'% <<< END INLINED FROM: sections/' + re.escape(name) + r' <<<', flat[start:])
        if end_marker:
            end = start + end_marker.start()
        else:
            end = len(flat)
    section_bounds[name] = (start, end)

# Extract content for our target sections
extracted = {}
for sec_file, (sec_name,) in section_map.items():
    if sec_name + '.tex' not in section_bounds:
        print(f"  WARNING: {sec_name}.tex not found in flat file - SKIP")
        continue
    start, end = section_bounds[sec_name + '.tex']
    body = flat[start:end]
    # Remove trailing newlines
    body = body.rstrip('\n')
    extracted[sec_file] = body
    print(f"  Extracted {sec_name}: {len(body)} chars, {body.count(chr(10))} lines")

# Write to section files
for sec_file, body in extracted.items():
    sec_path = sections_dir / sec_file
    # Backup existing file
    if sec_path.exists():
        backup = sec_path.with_suffix(sec_path.suffix + '.t68backup')
        with open(sec_path, 'r', encoding='utf-8') as f:
            old = f.read()
        with open(backup, 'w', encoding='utf-8') as f:
            f.write(old)
        print(f"  Backed up {sec_file} -> {backup.name}")
    # Write new content
    with open(sec_path, 'w', encoding='utf-8') as f:
        f.write(body)
    print(f"  Wrote {sec_file} ({len(body)} chars)")

print(f"\n=== Sync complete: {len(extracted)} sections updated ===")
