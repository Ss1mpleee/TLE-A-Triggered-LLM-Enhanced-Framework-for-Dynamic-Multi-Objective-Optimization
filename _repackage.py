#!/usr/bin/env python
"""Re-package submission folder into two zips (v2 — exclude preview/wide figures).

1. TLE_SWEVO_Overleaf.zip  — full Overleaf source
2. TLE_SWEVO_PDFs_only.zip  — just the 3 main PDFs + EM upload guide + AI audit
"""
import shutil
import zipfile
from pathlib import Path

SUB = Path(r'D:\新论文\论文\_submission')
ROOT = SUB.parent

# Sync regenerated figure into figures/ subfolder
fig_dir = SUB / 'figures'
for ext in ['png', 'pdf']:
    src = SUB / f'fig_budget_comparison.{ext}'
    dst = fig_dir / f'fig_budget_comparison.{ext}'
    if src.exists():
        shutil.copy(src, dst)

# Build TLE_SWEVO_Overleaf.zip
overleaf_zip = SUB / 'TLE_SWEVO_Overleaf.zip'
if overleaf_zip.exists():
    overleaf_zip.unlink()
print(f"Building {overleaf_zip.name}...")

INCLUDE_EXTS = {'.tex', '.bib', '.cls', '.sty', '.bst', '.png', '.pdf',
                '.svg', '.txt', '.md'}
EXCLUDE_EXTS = {'.aux', '.log', '.out', '.blg', '.abs', '.bbl', '.toc',
                '.synctex.gz', '.fdb_latexmk', '.fls', '.flac', '.doc',
                '.docx', '.zip'}
EXCLUDE_NAMES = {'TLE_SWEVO_Overleaf.zip'}
# Exclude preview/wide images that are not used by the .tex
EXCLUDE_SUBSTR = ('_preview', '_wide', '_original')

files_added = 0
with zipfile.ZipFile(overleaf_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    # Top-level submission files
    for f in sorted(SUB.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() not in INCLUDE_EXTS:
            continue
        if f.suffix.lower() in EXCLUDE_EXTS:
            continue
        if f.name in EXCLUDE_NAMES:
            continue
        if any(s in f.name for s in EXCLUDE_SUBSTR):
            continue
        zf.write(f, arcname=f.name)
        files_added += 1
    # figures/ subfolder (only include the .png/.pdf of figures referenced)
    if fig_dir.is_dir():
        for f in sorted(fig_dir.iterdir()):
            if not f.is_file():
                continue
            if f.suffix.lower() not in INCLUDE_EXTS:
                continue
            if f.suffix.lower() in EXCLUDE_EXTS:
                continue
            if any(s in f.name for s in EXCLUDE_SUBSTR):
                continue
            zf.write(f, arcname=f'figures/{f.name}')
            files_added += 1
print(f"  added {files_added} files")
print(f"  size: {overleaf_zip.stat().st_size / 1024 / 1024:.2f} MB")

# Build TLE_SWEVO_PDFs_only.zip
pdfs_zip = ROOT / 'TLE_SWEVO_PDFs_only.zip'
if pdfs_zip.exists():
    pdfs_zip.unlink()
print(f"Building {pdfs_zip.name}...")
with zipfile.ZipFile(pdfs_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for name in ['main_submission.pdf', 'cover_letter.pdf',
                 'supplementary_material.pdf']:
        src = SUB / name
        if src.exists():
            zf.write(src, arcname=name)
    for name in ['EM_UPLOAD_GUIDE.md', 'ai_audit.txt']:
        src = SUB / name
        if src.exists():
            zf.write(src, arcname=name)
print(f"  size: {pdfs_zip.stat().st_size / 1024 / 1024:.2f} MB")
print()
print("Done.")
