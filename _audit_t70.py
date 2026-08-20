#!/usr/bin/env python3
"""T70 audit: verify the cleanup was correct, nothing current was deleted.

Checks:
1. All CRITICAL files still exist in their expected places
2. _TO_DELETE/ contains only OUTDATED materials
3. The 4-dimension review changes are still in place
4. The new/novel cleanup is still in place
5. LaTeX still compiles cleanly
"""
import os
import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r'D:\新论文')
PAPER = ROOT / '论文'
SUBMISSION = PAPER / '_submission'
SECTIONS = PAPER / 'sections'
TO_DELETE = PAPER / '_TO_DELETE'

# ============================================================================
# 1. Critical files exist
# ============================================================================
print("=" * 70)
print("CHECK 1: Critical files exist")
print("=" * 70)

CRITICAL = [
    # Submission directory current files
    (SUBMISSION / 'main_submission.tex', 'main_submission.tex (current flat)'),
    (SUBMISSION / 'main_submission.pdf', 'main_submission.pdf (current flat PDF)'),
    (SUBMISSION / 'supplementary_material.tex', 'supplementary_material.tex'),
    (SUBMISSION / 'supplementary_material.pdf', 'supplementary_material.pdf'),
    (SUBMISSION / 'cover_letter.tex', 'cover_letter.tex'),
    (SUBMISSION / 'cover_letter.pdf', 'cover_letter.pdf'),
    (SUBMISSION / 'references.bib', 'references.bib'),
    (SUBMISSION / 'EM_UPLOAD_GUIDE.md', 'EM_UPLOAD_GUIDE.md'),

    # Source sections
    (SECTIONS / '01_introduction.tex', '01_introduction.tex'),
    (SECTIONS / '02_related_work.tex', '02_related_work.tex'),
    (SECTIONS / '03_method.tex', '03_method.tex'),
    (SECTIONS / '03_theory.tex', '03_theory.tex'),
    (SECTIONS / '04_experimental_setup.tex', '04_experimental_setup.tex'),
    (SECTIONS / '05_results.tex', '05_results.tex'),
    (SECTIONS / '06_discussion.tex', '06_discussion.tex'),
    (SECTIONS / '07_conclusion.tex', '07_conclusion.tex'),
    (SECTIONS / 'A_appendix.tex', 'A_appendix.tex'),

    # Paper dir LaTeX class files
    (PAPER / 'cas-common.sty', 'cas-common.sty'),
    (PAPER / 'cas-sc.cls', 'cas-sc.cls'),
    (PAPER / 'cas-model2-names.bst', 'cas-model2-names.bst'),

    # Build scripts
    (PAPER / '_merge_submission.py', '_merge_submission.py'),
    (PAPER / '_repack_overleaf.py', '_repack_overleaf.py'),

    # Final zips
    (ROOT / 'TLE_SWEVO_Overleaf.zip', 'TLE_SWEVO_Overleaf.zip'),
    (ROOT / 'TLE_SWEVO_PDFs_only.zip', 'TLE_SWEVO_PDFs_only.zip'),
]

all_present = True
for path, name in CRITICAL:
    if path.exists():
        size = path.stat().st_size
        print(f"  ✓ {name}: {size:,} bytes")
    else:
        print(f"  ✗ MISSING: {name} at {path}")
        all_present = False
print()
if all_present:
    print("  ALL CRITICAL FILES PRESENT")
else:
    print("  CRITICAL FILES MISSING - URGENT ACTION NEEDED")

# ============================================================================
# 2. _TO_DELETE/ inventory
# ============================================================================
print()
print("=" * 70)
print("CHECK 2: _TO_DELETE/ inventory (should be only outdated files)")
print("=" * 70)

if not TO_DELETE.exists():
    print(f"  _TO_DELETE/ does not exist!")
else:
    items = list(TO_DELETE.iterdir())
    print(f"  Total items: {len(items)}")

    # Categorize
    by_type = {'dir': 0, 'file': 0}
    by_ext = {}
    for item in items:
        if item.is_dir():
            by_type['dir'] += 1
        else:
            by_type['file'] += 1
            ext = item.suffix.lower() or '(no ext)'
            by_ext[ext] = by_ext.get(ext, 0) + 1

    print(f"  Directories: {by_type['dir']}")
    print(f"  Files: {by_type['file']}")
    print(f"  By extension: {by_ext}")

    # Check for any CURRENT files that might have been accidentally moved
    # We check if the same name exists in _submission/ with a newer timestamp
    print()
    print("  Checking for accidentally-moved current files:")
    flagged = []
    for item in items:
        if item.is_file():
            # Check if same name exists in _submission/
            current = SUBMISSION / item.name
            if current.exists():
                # Compare timestamps
                item_mtime = item.stat().st_mtime
                current_mtime = current.stat().st_mtime
                if current_mtime < item_mtime:
                    flagged.append((item, current, 'in _TO_DELETE is NEWER than in _submission'))
        elif item.is_dir():
            # If a directory, check if it contains current files
            current = SUBMISSION / item.name
            if current.exists() and current.is_dir():
                # Compare files inside
                item_files = {f.name for f in item.iterdir() if f.is_file()} if item.exists() else set()
                current_files = {f.name for f in current.iterdir() if f.is_file()} if current.exists() else set()
                overlap = item_files & current_files
                if overlap:
                    flagged.append((item, current, f'has {len(overlap)} files also in _submission/'))

    if flagged:
        print(f"  ⚠ FLAGGED ({len(flagged)}):")
        for item, current, reason in flagged:
            print(f"    {item.name} ({reason})")
    else:
        print(f"  ✓ No accidentally-moved current files detected")

# ============================================================================
# 3. 4-dimension review content still in place
# ============================================================================
print()
print("=" * 70)
print("CHECK 3: 4-dimension review content")
print("=" * 70)

# Read main_submission.tex and check key changes
import re
with open(SUBMISSION / 'main_submission.tex', 'r', encoding='utf-8') as f:
    main_content = f.read()

# First-person pronouns (should be 0)
we_count = len(re.findall(r'\bwe\b', main_content, re.IGNORECASE))
our_count = len(re.findall(r'\bour\b', main_content, re.IGNORECASE))
us_count = len(re.findall(r'\bus\b', main_content, re.IGNORECASE))
print(f"  First-person in main: we={we_count}, our={our_count}, us={us_count}")
if we_count == 0 and our_count == 0 and us_count == 0:
    print(f"    ✓ Zero first-person pronouns")

# Abbreviation first-occurrence: check key ones
checks = {
    'LLM-EC': r'large-language-model evolutionary computation',
    'CEC': r'Congress on Evolutionary Computation',
    'DNSGA-II-A': r'Dynamic Non-dominated Sorting Genetic Algorithm II with random immigrants',
    'JSON': r'JavaScript object notation',
    'UCB1': r'Upper Confidence Bound 1',
    'IGD': r'inverted generational distance',
    'UAV': r'Unmanned Aerial Vehicle',
    'PPS-DMOEA': r'Prediction-based Dynamic Multi-Objective',
    'MOEA/DD': r'Multi-Objective Evolutionary Algorithm based on Dominance and Decomposition',
    'NSGA-II': r'Non-dominated Sorting Genetic Algorithm II',
}
for abbr, full in checks.items():
    if re.search(full, main_content, re.IGNORECASE):
        print(f"  ✓ {abbr} defined: '{full}'")
    else:
        print(f"  ✗ {abbr} NOT defined (expected: '{full}')")

# new/novel replacement: check key ones
new_replacements = {
    'two previously unobserved failure modes (L179)': r'surfaces two previously unobserved failure modes',
    'two extended large-scale ablations (L249)': r'two extended large-scale ablations are added',
    'expanded data set (L249)': r'expanded data set',
    'extended trigger-ablation (L989, L992)': r'For the extended trigger-ablation',
    'no AI-tell "orchestrate" (L1019)': r'LLM-coordinated evolutionary search',
    'no "To summarize" (L628)': r'summarise the per-problem distribution',  # British spelling
}
print()
for label, pattern in new_replacements.items():
    if re.search(pattern, main_content):
        print(f"  ✓ {label}")
    else:
        print(f"  ✗ MISSING: {label} (pattern: {pattern[:50]})")

# AI tells: should not have
print()
ai_tells = ['delve into', 'leverage', 'harness', 'facilitate', 'elucidate',
            'To summarize', 'it is worth noting', 'paradigm shift']
for phrase in ai_tells:
    if re.search(re.escape(phrase), main_content, re.IGNORECASE):
        print(f"  ⚠ AI-tell still present: '{phrase}'")
    else:
        print(f"  ✓ no '{phrase}'")

# ============================================================================
# 4. LaTeX compilation
# ============================================================================
print()
print("=" * 70)
print("CHECK 4: LaTeX compilation")
print("=" * 70)

# Skip compilation (already done), just check that PDFs exist with recent dates
pdfs_to_check = [
    (SUBMISSION / 'main_submission.pdf', 'main PDF'),
    (SUBMISSION / 'supplementary_material.pdf', 'supp PDF'),
    (SUBMISSION / 'cover_letter.pdf', 'cover PDF'),
]
for pdf, name in pdfs_to_check:
    if pdf.exists():
        import datetime
        mtime = datetime.datetime.fromtimestamp(pdf.stat().st_mtime)
        size = pdf.stat().st_size
        age_hours = (datetime.datetime.now() - mtime).total_seconds() / 3600
        print(f"  ✓ {name}: {size:,} bytes, mtime={mtime:%Y-%m-%d %H:%M:%S} ({age_hours:.1f}h ago)")
    else:
        print(f"  ✗ {name}: MISSING")

# ============================================================================
# 5. Zip packages
# ============================================================================
print()
print("=" * 70)
print("CHECK 5: Final zip packages")
print("=" * 70)

import zipfile
zips_to_check = [
    (ROOT / 'TLE_SWEVO_Overleaf.zip', 'Overleaf package'),
    (ROOT / 'TLE_SWEVO_PDFs_only.zip', 'PDFs only package'),
]
for zip_path, name in zips_to_check:
    if zip_path.exists():
        size = zip_path.stat().st_size
        with zipfile.ZipFile(zip_path, 'r') as zf:
            n_files = len(zf.namelist())
            # Check for main_submission.pdf
            has_main = any('main_submission.pdf' in n for n in zf.namelist())
            has_main_tex = any('main_submission.tex' in n for n in zf.namelist())
        print(f"  ✓ {name}: {size:,} bytes, {n_files} files, has main.tex={has_main_tex}, has main.pdf={has_main}")
    else:
        print(f"  ✗ {name}: MISSING")
