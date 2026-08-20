#!/usr/bin/env python3
"""T70 round 3 second pass: cleanup remaining duplicates and old files in 论文/.

After first pass, 论文/ still has duplicate files that exist in _submission/ (newer).
Move old duplicates to _TO_DELETE/.

KEEP in 论文/:
- _submission/  (current)
- sections/     (source, just synced)
- _TO_DELETE/   (this cleanup)
- cas-*.sty/cls/bst  (LaTeX class files, needed for compilation)
- _merge_submission.py + _repack_overleaf.py  (build scripts)
"""
import shutil
import os
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r'D:\新论文')
PAPER = ROOT / '论文'
SUBMISSION = PAPER / '_submission'
TO_DELETE = PAPER / '_TO_DELETE'

moves = []

def move(src, label=None):
    src = Path(src)
    if not src.exists():
        return None
    dst = TO_DELETE / src.name
    i = 1
    while dst.exists():
        dst = TO_DELETE / f"{src.name}.{i}"
        i += 1
    try:
        shutil.move(str(src), str(dst))
        moves.append((label or src.name, src, dst))
        return dst
    except Exception as e:
        print(f"  ERROR moving {src}: {e}")
        return None

# Files in 论文/ that have newer equivalents in _submission/
# (Move old duplicates to _TO_DELETE)
print("=== Duplicates in 论文/ (older than _submission/) ===")
duplicates = [
    'ai_audit.txt',
    'cover_letter.pdf',
    'cover_letter.tex',
    'EM_UPLOAD_GUIDE.md',
    'highlights.txt',
    'main.pdf',           # 7/14
    'main_submission.pdf',  # 8/3
    'main_submission.tex',  # 8/3
    'references.bib',     # 7/14 (in 论文/) vs 8/17 (in _submission/)
    'supplementary_material.pdf',
    'supplementary_material.tex',
    'TLE_SWEVO_Overleaf.zip',  # 8/12 (in 论文/) vs 8/19 (in root)
    'TLE_SWEVO_PDFs_only.zip',  # 8/12 (in 论文/) vs 8/19 (in root)
    '_cross_llm_n30_stats.json',
    '_cross_llm_n30_summary.md',
    'README.md',
    'inspect_df4.py',     # debug script
]
for name in duplicates:
    f = PAPER / name
    if f.exists():
        move(f, "duplicate")
        print(f"  Moved {name}")
print(f"  Total: {len(duplicates)}")

# Also remove cas-dc.cls if cas-sc.cls is what we use
# Check which one is used
with open(PAPER / 'main_submission.tex', 'r', encoding='utf-8') as f:
    main_content = f.read()
if 'cas-dc' in main_content or 'cas-sc' in main_content:
    if 'cas-dc' in main_content:
        print(f"  cas-dc.cls is used - KEEP")
    else:
        move(PAPER / 'cas-dc.cls', "unused_class")

# Recompile to verify nothing broke
print("\n=== Verifying compilation after cleanup ===")
import subprocess
result = subprocess.run(['pdflatex', '--interaction=nonstopmode', 'main_submission.tex'],
                        cwd=str(SUBMISSION), capture_output=True)
print(f"  pdflatex main: exit code {result.returncode}")

# Summary
print(f"\n=== SUMMARY ===")
print(f"Total moved this pass: {len(moves)}")
print(f"_TO_DELETE total items: {len(list(TO_DELETE.iterdir()))}")
