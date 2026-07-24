"""Compile in a temp directory to avoid file lock, then copy PDFs back."""
import shutil
import subprocess
from pathlib import Path

SRC = Path(r'D:\新论文\论文')
TMP = Path(r'D:\新论文\_build_tmp')
PDF_BACK = SRC

# Reset tmp
if TMP.exists():
    shutil.rmtree(TMP)
TMP.mkdir(parents=True)

# Copy source tree (no .aux/.log/.pdf needed, those are generated)
EXCLUDE = {'.aux', '.log', '.bbl', '.blg', '.out', '.spl', '.pdf'}
for p in SRC.rglob('*'):
    if p.is_file():
        if p.suffix in EXCLUDE:
            continue
        rel = p.relative_to(SRC)
        dst = TMP / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)

# Compile main
for cmd in [
    ['pdflatex', '-interaction=nonstopmode', 'main.tex'],
    ['bibtex', 'main'],
    ['pdflatex', '-interaction=nonstopmode', 'main.tex'],
    ['pdflatex', '-interaction=nonstopmode', 'main.tex'],
]:
    print(f'>>> {cmd}')
    r = subprocess.run(cmd, cwd=str(TMP), capture_output=True, text=True, shell=True)
    print(r.stdout[-500:] if r.stdout else '')
    if r.returncode != 0:
        print(f'STDERR: {r.stderr[-500:]}')

# Compile cover and supp
for f in ['cover_letter.tex', 'supplementary_material.tex']:
    subprocess.run(['pdflatex', '-interaction=nonstopmode', f], cwd=str(TMP), capture_output=True, text=True, shell=True)

# Copy PDFs back
print('\n=== Compiled PDFs ===')
for pdf in TMP.glob('*.pdf'):
    print(f'  {pdf.name}: {pdf.stat().st_size} bytes')
    target = PDF_BACK / pdf.name
    # Try copying - if locked, just note it
    try:
        shutil.copy2(pdf, target)
        print(f'    -> copied to {target}')
    except PermissionError:
        print(f'    -> BLOCKED (file in use, leaving {pdf} as build artifact)')

# Cleanup tmp
shutil.rmtree(TMP)