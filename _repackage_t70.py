#!/usr/bin/env python3
"""T70: repackage the submission zip files with updated PDFs and tex."""
import zipfile
import os
from pathlib import Path

src_dir = Path(r'D:\新论文\论文\_submission')
out_dir = Path(r'D:\新论文')

# Files to include in the Overleaf zip (exclude aux/bbl/blg/log/out/toc/.bak)
include_patterns = [
    '*.tex', '*.bib', '*.bst', '*.cls', '*.sty',
    '*.pdf', '*.png', '*.svg', '*.jpg',
    '*.md', '*.doc', '*.txt',  # supporting docs
]
exclude_patterns = [
    '.aux', '.bbl', '.blg', '.log', '.out', '.toc', '.synctex.gz',
    '.bak', '$tmpDir', '_tmp', '_trash_aux', 'figures', 'ai_audit.txt',
]

# Get all files in src_dir
files = []
for item in src_dir.iterdir():
    if item.is_file():
        # Check if should be excluded
        name = item.name
        if any(name.endswith(p) for p in exclude_patterns):
            continue
        if any(name.startswith(p) for p in ['_', '$']):
            continue
        if name == 'ai_audit.txt':
            continue
        if name == 'TLE_SWEVO_Overleaf.zip':
            continue
        if name.endswith('.abs'):
            continue
        files.append(item)

# Sort
files.sort(key=lambda x: x.name)

# Create Overleaf zip
overleaf_zip = out_dir / 'TLE_SWEVO_Overleaf.zip'
with zipfile.ZipFile(overleaf_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in files:
        zf.write(f, arcname=f.name)

print(f"Overleaf zip: {overleaf_zip} ({overleaf_zip.stat().st_size:,} bytes, {len(files)} files)")

# Create PDFs-only zip
pdfs_only_zip = out_dir / 'TLE_SWEVO_PDFs_only.zip'
pdfs = [f for f in files if f.suffix == '.pdf']
with zipfile.ZipFile(pdfs_only_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in pdfs:
        zf.write(f, arcname=f.name)

print(f"PDFs-only zip: {pdfs_only_zip} ({pdfs_only_zip.stat().st_size:,} bytes, {len(pdfs)} files)")

# List included files
print("\n=== Overleaf zip contents ===")
with zipfile.ZipFile(overleaf_zip, 'r') as zf:
    for info in sorted(zf.infolist(), key=lambda x: x.filename):
        print(f"  {info.filename} ({info.file_size:,} bytes)")
