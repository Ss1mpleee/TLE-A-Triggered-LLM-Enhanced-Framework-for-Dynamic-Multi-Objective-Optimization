#!/usr/bin/env python3
"""T70 round 3: cleanup outdated materials.

Move (not delete) clearly outdated files/directories to a `_TO_DELETE/` folder
in the workspace. This is reversible - the user can manually verify and then
truly delete the `_TO_DELETE/` folder.

Categories of cleanup:
1. Old Overleaf extracted directories (TLE_SWEVO_Overleaf__old_*): 22 dirs
2. Old Overleaf packages (TLE_SWEVO_Overleaf, Overleaf_package): outdated
3. Old build stages (_stage_used_*, _stage2_used_*): outdated
4. Duplicate templates (els-cas-templates (2), els-cas-templates (2).zip)
5. Old Python cache (__pycache__)
6. Old thumbnails (only if not used by cas-sc.cls)
7. Old submission/tables/figures (now in _submission/)
8. Old .aux/.log/.out/.bbl/.blg/.abs build artifacts
9. Old draft files (_*.txt, highlights_new.txt, cover_letter_new_para.txt, etc.)
10. Old docx files (cover_letter.docx is from 7/29, we have current .tex)
11. Old one-off _*.py scripts (keep only _merge_submission.py and _repack_overleaf.py)
12. Old PNGs in root (paper_v2*, paper_v3*, paper_v3final*, paper_view.html, etc.)
13. Old zip files in root (TLE_SWEVO_Overleaf_OLD*.zip, BAD*.zip, etc.)
14. Old PDF (TLE_paper_SWEVO_2026-07-01_FINAL.pdf, main.pdf)
15. Old build artifacts in root (main.aux, main.log, main.out, main.spl)
16. Old root directories (figures/, 文档/)
"""
import shutil
import os
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Workspace paths
ROOT = Path(r'D:\新论文')
PAPER = ROOT / '论文'
TO_DELETE = PAPER / '_TO_DELETE'

# Create _TO_DELETE folder
TO_DELETE.mkdir(parents=True, exist_ok=True)
print(f"Created {TO_DELETE}")

# Track moves
moves = []

def move(src, label=None):
    """Move src into _TO_DELETE/<basename>. Returns (src, dst, success)."""
    src = Path(src)
    if not src.exists():
        return None
    dst = TO_DELETE / src.name
    # If dst exists, add a suffix
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


# === Category 1: Old Overleaf extracted directories ===
print("\n=== 1. Old Overleaf __old_* directories ===")
old_dirs = sorted(PAPER.glob('TLE_SWEVO_Overleaf__old_*'))
print(f"  Found {len(old_dirs)} directories")
for d in old_dirs:
    move(d, "old_overleaf_dir")
print(f"  Moved {len(old_dirs)} directories")

# === Category 2: Old Overleaf packages ===
print("\n=== 2. Old Overleaf packages ===")
for d in [PAPER / 'TLE_SWEVO_Overleaf', PAPER / 'Overleaf_package']:
    if d.exists():
        move(d, "old_overleaf_pkg")
        print(f"  Moved {d.name}")

# === Category 3: Old build stages ===
print("\n=== 3. Old build stages ===")
for d in PAPER.glob('_stage*_used_*'):
    move(d, "old_stage")
    print(f"  Moved {d.name}")
for d in PAPER.glob('_stage2*_used_*'):
    move(d, "old_stage2")
    print(f"  Moved {d.name}")

# === Category 4: Duplicate templates ===
print("\n=== 4. Duplicate templates ===")
for f in [PAPER / 'els-cas-templates (2).zip', PAPER / 'els-cas-templates (2)']:
    if f.exists():
        move(f, "dup_template")
        print(f"  Moved {f.name}")

# === Category 5: Python cache ===
print("\n=== 5. Python cache ===")
for d in PAPER.glob('__pycache__'):
    move(d, "pycache")
    print(f"  Moved {d.name}")

# === Category 6: Thumbnails (cas-common icons) ===
# Check if cas-sc.cls uses these
print("\n=== 6. Thumbnails (check if used by cas-sc.cls) ===")
cas_sc = PAPER / 'cas-sc.cls'
uses_thumbs = False
if cas_sc.exists():
    with open(cas_sc, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'thumbnail' in content.lower() or '.jpeg' in content:
        uses_thumbs = True
if uses_thumbs:
    print(f"  cas-sc.cls uses thumbnails - KEEP {PAPER/'thumbnails'}")
else:
    move(PAPER / 'thumbnails', "thumbnails")
    print(f"  Moved thumbnails (not used)")

# === Category 7: Old submission/tables/figures ===
print("\n=== 7. Old submission/tables/figures ===")
for d in [PAPER / '提交', PAPER / '_tables', PAPER / '_FINAL_PDFs', PAPER / 'figures']:
    if d.exists():
        move(d, "old_subdir")
        print(f"  Moved {d.name}")

# === Category 8: Old build artifacts in 论文/ ===
print("\n=== 8. Old build artifacts in 论文/ ===")
artifacts = []
for ext in ['.aux', '.log', '.out', '.bbl', '.blg', '.abs', '.spl', '.synctex.gz']:
    for f in PAPER.glob(f'*{ext}'):
        # Skip the current submission's .aux files - they're needed for cross-refs
        # Actually _submission has its own .aux files
        artifacts.append(f)
# Don't move the .bak files in sections (those are our backups)
for f in artifacts:
    if f.exists():
        move(f, "artifact")
print(f"  Moved {len(artifacts)} artifacts")

# === Category 9: Old draft files ===
print("\n=== 9. Old draft files ===")
draft_files = [
    'cover_letter_new_para.txt',
    'highlights_new.txt',
    'Highlights.doc',
    '_abs_line.txt',
    '_abs_orig.txt',
    '_new_abstract.txt',
    '_pdf_p1-3.txt',
    '_review.txt',
    'cover_letter.docx',  # old Word version, we have .tex
]
for name in draft_files:
    f = PAPER / name
    if f.exists():
        move(f, "draft")
        print(f"  Moved {f.name}")

# === Category 11: Old one-off _*.py scripts ===
# KEEP: _merge_submission.py, _repack_overleaf.py
# These are essential for the workflow
print("\n=== 11. Old _*.py scripts (keep _merge_submission.py + _repack_overleaf.py) ===")
keep_scripts = {'_merge_submission.py', '_repack_overleaf.py'}
removed_count = 0
for f in sorted(PAPER.glob('_*.py')):
    if f.name in keep_scripts:
        print(f"  KEEP: {f.name}")
        continue
    move(f, "old_script")
    removed_count += 1
print(f"  Moved {removed_count} old scripts")

# === Category 12: Old PNGs in root ===
print("\n=== 12. Old PNGs in root ===")
old_pngs = []
for pattern in ['paper_v2b_p-*.png', 'paper_v2c-*.png', 'paper_v2_p-*.png',
                'paper_v3-*.png', 'paper_v3final-*.png']:
    old_pngs.extend(ROOT.glob(pattern))
old_pngs.append(ROOT / 'graphical_abstract_v3.png')
old_pngs.append(ROOT / 'paper_view.html')
old_pngs.append(ROOT / 'paper_mcp_nav.json')
old_pngs.append(ROOT / 'paper_mcp_nav.py')
old_pngs.append(ROOT / 'verify_refs.py')
old_pngs.append(ROOT / 'verification_report.txt')
old_pngs.append(ROOT / '选题分析.html')
old_pngs.append(ROOT / 'figures')  # old figures dir
old_pngs.append(ROOT / '文档')  # old docs dir
for f in old_pngs:
    if f.exists():
        move(f, "old_root")
        print(f"  Moved {f.name}")
print(f"  Total moved: {len([m for m in moves if m[0] == 'old_root'])}")

# === Category 13: Old zip files in root ===
print("\n=== 13. Old zip files in root ===")
old_zips = list(ROOT.glob('TLE_SWEVO_Overleaf_OLD*.zip'))
old_zips.extend(ROOT.glob('TLE_SWEVO_Overleaf_BAD*.zip'))
old_zips.extend(ROOT.glob('TLE_SWEVO_PDFs_only_OLD*.zip'))
for z in old_zips:
    if z.exists():
        move(z, "old_zip")
        print(f"  Moved {z.name}")
print(f"  Total old zips: {len(old_zips)}")

# === Category 14: Old PDFs ===
print("\n=== 14. Old PDFs in root ===")
old_pdfs = [
    ROOT / 'TLE_paper_SWEVO_2026-07-01_FINAL.pdf',
    ROOT / 'main.pdf',
]
for f in old_pdfs:
    if f.exists():
        move(f, "old_pdf")
        print(f"  Moved {f.name}")

# === Category 15: Old build artifacts in root ===
print("\n=== 15. Old build artifacts in root ===")
for ext in ['.aux', '.log', '.out', '.spl', '.bbl', '.blg']:
    for f in ROOT.glob(f'main{ext}'):
        if f.exists():
            move(f, "root_artifact")
            print(f"  Moved {f.name}")

# === Category 16: Old main.tex in 论文/ ===
print("\n=== 16. Old main.tex in 论文/ ===")
old_main = PAPER / 'main.tex'
if old_main.exists():
    # Check if it's the current one or old
    # The current one is in _submission/main_submission.tex
    # main.tex in 论文/ is the legacy single-file version
    move(old_main, "old_main_tex")
    print(f"  Moved {old_main.name}")

# Summary
print(f"\n=== SUMMARY ===")
print(f"Total items moved: {len(moves)}")
print(f"_TO_DELETE folder: {TO_DELETE}")
print(f"Contents: {len(list(TO_DELETE.iterdir()))} items")
