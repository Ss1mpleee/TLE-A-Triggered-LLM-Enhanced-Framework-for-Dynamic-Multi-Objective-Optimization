#!/usr/bin/env python
"""Force-repackage, with explicit deletion."""
import os
import shutil
import zipfile
import time
from pathlib import Path

SUB = Path(r'D:\新论文\论文\_submission')
ROOT = SUB.parent

# Update figures/ subfolder
fig_dir = SUB / 'figures'
for ext in ['png', 'pdf']:
    src = SUB / f'fig_budget_comparison.{ext}'
    dst = fig_dir / f'fig_budget_comparison.{ext}'
    if src.exists():
        shutil.copy(src, dst)

# Build Overleaf zip in submission/
overleaf_zip = SUB / 'TLE_SWEVO_Overleaf.zip'
if overleaf_zip.exists():
    overleaf_zip.unlink()

INCLUDE_EXTS = {'.tex', '.bib', '.cls', '.sty', '.bst', '.png', '.pdf',
                '.svg', '.txt', '.md'}
EXCLUDE_EXTS = {'.aux', '.log', '.out', '.blg', '.abs', '.bbl', '.toc',
                '.synctex.gz', '.fdb_latexmk', '.fls', '.flac', '.doc',
                '.docx', '.zip'}
EXCLUDE_NAMES = {'TLE_SWEVO_Overleaf.zip'}
EXCLUDE_SUBSTR = ('_preview', '_wide', '_original')

files_added = 0
with zipfile.ZipFile(overleaf_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
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
print(f"Overleaf: {overleaf_zip} -> {overleaf_zip.stat().st_size} bytes ({files_added} files)")

# Build PDFs-only zip in D:\新论文\
pdfs_zip = ROOT / 'TLE_SWEVO_PDFs_only.zip'
print(f"  current pdfs_zip: {pdfs_zip}, exists={pdfs_zip.exists()}, size={pdfs_zip.stat().st_size if pdfs_zip.exists() else 0}")
if pdfs_zip.exists():
    pdfs_zip.unlink()
    time.sleep(0.1)  # let FS settle
print(f"  after delete: exists={pdfs_zip.exists()}")

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
print(f"PDFs-only: {pdfs_zip} -> {pdfs_zip.stat().st_size} bytes")
