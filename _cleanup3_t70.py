#!/usr/bin/env python3
"""T70 round 3 final cleanup: remove remaining temp/backups in _submission/ and sections/.

Items to clean:
- _submission/$tmpDir, _tmp, _trash_aux (empty leftovers)
- _submission/figures (empty? or has old files)
- _submission/TLE_SWEVO_Overleaf.zip (8/17 - older than 8/19 in root)
- sections/05_results.tex.bak (7/2)
- sections/05_results.tex.original (7/2)
- sections/*.tex.t68backup (my own backups)
- _FINAL_PDFs (root) - old final PDFs
"""
import shutil
import os
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r'D:\新论文')
PAPER = ROOT / '论文'
SUBMISSION = PAPER / '_submission'
SECTIONS = PAPER / 'sections'
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
        if src.is_dir():
            shutil.move(str(src), str(dst))
        else:
            shutil.move(str(src), str(dst))
        moves.append((label or src.name, src, dst))
        return dst
    except Exception as e:
        print(f"  ERROR moving {src}: {e}")
        return None

def remove_empty_dir(d):
    d = Path(d)
    if d.exists() and d.is_dir():
        try:
            # Check if empty (no files in dir)
            contents = list(d.iterdir())
            if len(contents) == 0:
                d.rmdir()
                print(f"  Removed empty dir: {d.name}")
                return True
            else:
                # If has content but is small/stale, also move
                move(d, "stale_dir")
                return True
        except Exception as e:
            print(f"  ERROR removing {d}: {e}")
    return False

# 1) _submission empty/stale dirs
print("=== _submission/ empty/stale dirs ===")
for d_name in ['$tmpDir', '_tmp', '_trash_aux']:
    d = SUBMISSION / d_name
    if d.exists():
        # Check if empty
        contents = list(d.iterdir())
        if not contents:
            d.rmdir()
            print(f"  Removed empty: {d_name}")
        else:
            print(f"  {d_name} has {len(contents)} items - moving to _TO_DELETE")
            move(d, "stale_tmp")

# figures/ inside _submission
fig_dir = SUBMISSION / 'figures'
if fig_dir.exists():
    contents = list(fig_dir.iterdir())
    if not contents:
        fig_dir.rmdir()
        print(f"  Removed empty: figures")
    else:
        # Check if any used in main_submission.tex
        with open(SUBMISSION / 'main_submission.tex', 'r', encoding='utf-8') as f:
            content = f.read()
        used = []
        for f in contents:
            if f.name in content:
                used.append(f)
        unused = [f for f in contents if f.name not in content]
        if unused:
            print(f"  figures/ has {len(used)} used, {len(unused)} unused - moving unused to _TO_DELETE")
            for f in unused:
                move(f, "fig_unused")
        else:
            print(f"  figures/ all used - KEEP")
        # Remove the dir if it's now empty
        remaining = list(fig_dir.iterdir())
        if not remaining:
            fig_dir.rmdir()
            print(f"  Removed empty figures/")

# 2) _submission/TLE_SWEVO_Overleaf.zip (8/17) - older than root's (8/19)
print("\n=== Old _submission/TLE_SWEVO_Overleaf.zip ===")
old_zip = SUBMISSION / 'TLE_SWEVO_Overleaf.zip'
if old_zip.exists():
    move(old_zip, "old_submission_zip")
    print(f"  Moved {old_zip.name}")

# 3) sections/ backups
print("\n=== sections/ backups ===")
for f in SECTIONS.glob('*.t68backup'):
    move(f, "section_backup")
    print(f"  Moved {f.name}")
for f in SECTIONS.glob('*.bak'):
    move(f, "section_bak")
    print(f"  Moved {f.name}")
for f in SECTIONS.glob('*.original'):
    move(f, "section_orig")
    print(f"  Moved {f.name}")

# 4) _FINAL_PDFs in root
print("\n=== Root _FINAL_PDFs ===")
fp = ROOT / '_FINAL_PDFs'
if fp.exists():
    contents = list(fp.iterdir())
    if not contents:
        fp.rmdir()
        print(f"  Removed empty: _FINAL_PDFs")
    else:
        move(fp, "old_final_pdfs")
        print(f"  Moved _FINAL_PDFs (had {len(contents)} items)")

# 5) _FINAL_PDFs/ in _submission if it exists
fp2 = SUBMISSION / '_FINAL_PDFs'
if fp2.exists():
    contents = list(fp2.iterdir())
    if not contents:
        fp2.rmdir()
        print(f"  Removed empty _FINAL_PDFs in _submission")
    else:
        move(fp2, "old_submission_final_pdfs")

# Summary
print(f"\n=== SUMMARY ===")
print(f"Total moved: {len(moves)}")
print(f"_TO_DELETE total items: {len(list(TO_DELETE.iterdir()))}")
