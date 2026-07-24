"""Build a clean Overleaf-ready ZIP for the TLE paper project."""
import os
import zipfile
import shutil
from pathlib import Path

ROOT = Path(r'D:\新论文\论文')
OUT = Path(r'D:\新论文\论文_Overleaf.zip')
TEMP = Path(r'D:\新论文\_overleaf_staging')

# Clean staging dir
if TEMP.exists():
    shutil.rmtree(TEMP)
TEMP.mkdir(parents=True)

# Copy needed files into staging with proper structure
INCLUDE_DIRS = ['sections', 'figures']
EXCLUDE_NAMES = ['_finalck-18.png', '_finalck-19.png', '_finalck']  # random screenshot files
EXCLUDE_SUFFIX = {'.aux', '.log', '.bbl', '.blg', '.out', '.spl', '.pdf', '.original', '.bak'}

# Copy root files
for f in ROOT.iterdir():
    if f.is_file():
        if f.suffix in EXCLUDE_SUFFIX:
            continue
        if any(f.name.startswith(x) for x in ['_finalck']):
            continue
        if f.name in ['README.md']:
            continue  # skip README, not needed for compilation
        shutil.copy2(f, TEMP / f.name)

# Copy sections dir (all .tex files, no backups)
sections_src = ROOT / 'sections'
sections_dst = TEMP / 'sections'
sections_dst.mkdir()
for f in sections_src.iterdir():
    if f.is_file() and f.suffix == '.tex' and not any(f.name.endswith(s) for s in ['.original', '.bak']):
        shutil.copy2(f, sections_dst / f.name)

# Copy figures dir (all PNG, exclude _deprecated, exclude backups)
figures_src = ROOT / 'figures'
figures_dst = TEMP / 'figures'
figures_dst.mkdir()
for f in figures_src.iterdir():
    if f.is_dir():
        if f.name == '_deprecated':
            continue
    elif f.is_file():
        if f.suffix in EXCLUDE_SUFFIX:
            continue
        if f.name.endswith('.original') or f.name.endswith('.bak'):
            continue
        if f.suffix in {'.png', '.pdf', '.svg'}:
            shutil.copy2(f, figures_dst / f.name)

# Build ZIP
if OUT.exists():
    OUT.unlink()

print('=== Staging dir contents ===')
for p in sorted(TEMP.rglob('*')):
    if p.is_file():
        rel = p.relative_to(TEMP)
        print(f'  {rel}  ({p.stat().st_size} bytes)')

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for p in sorted(TEMP.rglob('*')):
        if p.is_file():
            arcname = p.relative_to(TEMP).as_posix()
            zf.write(p, arcname)

print(f'\n=== ZIP created ===')
print(f'  Path: {OUT}')
print(f'  Size: {OUT.stat().st_size:,} bytes ({OUT.stat().st_size/1024/1024:.1f} MB)')

# Cleanup staging
shutil.rmtree(TEMP)