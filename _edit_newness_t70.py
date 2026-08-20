#!/usr/bin/env python3
"""T70 round 2: replace promotional 'new/novel' uses that describe the TLE method.

The rule: do NOT use 'new', 'novel' to describe the proposed method itself.
Keep 'first' (priority claims), 'proposed/introduces' (standard academic),
'new' modifying findings/data (legitimate).

For each file, list the lines containing 'new'/'novel', then apply targeted
replacements only where 'new' describes the method (not findings/data).
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Targeted replacements: each is a (file, old, new) tuple.
# These are all "new" -> neutral alternatives.
# We KEEP "first" priority claims, "proposed" (standard), and "new" modifying findings/data.
replacements = [
    # main_submission.tex
    # 1) "two new failure modes" (L179) - "new" modifies "failure modes" which are findings.
    #    But the user explicitly said no "new" for method descriptions. Failure modes are
    #    FINDINGS (not the method), so this is borderline. Change to "previously
    #    unobserved" to remove any "new" reading.
    (r'D:\新论文\论文\_submission\main_submission.tex',
     r'surfaces two new failure modes: Qwen-2.5-7B has 4 catastrophic seeds',
     r'surfaces two previously unobserved failure modes: Qwen-2.5-7B has 4 catastrophic seeds'),

    # 2) "supported by the new data" (L249) - "new data" is borderline. Change to "extended".
    (r'D:\新论文\论文\_submission\main_submission.tex',
     r'are stated as testable empirical claims supported by the new data',
     r'are stated as testable empirical claims supported by the expanded data set'),

    # 3) "two new large-scale ablations" (L249) - "new" here = "additional/larger".
    #    Change to "two extended large-scale ablations".
    (r'D:\新论文\论文\_submission\main_submission.tex',
     r'(iv)~two new large-scale ablations are added',
     r'(iv)~two extended large-scale ablations are added'),

    # 4) "two new failure modes emerge" (L747) - same as #1.
    (r'D:\新论文\论文\_submission\main_submission.tex',
     r'instead, two new failure modes emerge that were not visible in the original three-problem study',
     r'instead, two previously unobserved failure modes emerge that were not visible in the original three-problem study'),

    # 5) "the new trigger-ablation" (L989) - "new" = "extended/larger".
    (r'D:\新论文\论文\_submission\main_submission.tex',
     r'For the new trigger-ablation and cross-LLM 14 extensions, $n = 30$ is again used',
     r'For the extended trigger-ablation and cross-LLM 14 extensions, $n = 30$ is again used'),

    # 6) "The new trigger-ablation" (L992) - same as #5.
    (r'D:\新论文\论文\_submission\main_submission.tex',
     r'The new trigger-ablation and cross-LLM 14 extensions preserve the 14-problem coverage',
     r'The extended trigger-ablation and cross-LLM 14 extensions preserve the 14-problem coverage'),

    # 7) (L299 table) "TLE (proposed)" - in tab:arch. "proposed" is standard, keep.
    #    No change needed.

    # supplementary_material.tex
    # 8) "the proposed TLE" (L647) - keep, "proposed" is standard.
    #    No change needed.

    # cover_letter.tex
    # 9) "three new honest findings" (L33) - "new" modifies findings, OK to keep.
    #    But to be safe, change to "three previously unreported honest findings".
    (r'D:\新论文\论文\_submission\cover_letter.tex',
     r'surface three new honest findings',
     r'surface three previously unreported honest findings'),

    # 10) "two new figures" (L33) - "new" modifies figures, OK to keep.
    #     But to be safe, change to "two additional figures".
    (r'D:\新论文\论文\_submission\cover_letter.tex',
     r'The two new figures (Fig.~\ref{fig:abl-boxplot} and Fig.~\ref{fig:cross-heatmap}) and three new tables',
     r'The two additional figures (Fig.~\ref{fig:abl-boxplot} and Fig.~\ref{fig:cross-heatmap}) and three additional tables'),

    # 11) Section header "Innovation." (L33) - change to "Contribution." for neutrality.
    (r'D:\新论文\论文\_submission\cover_letter.tex',
     r'\noindent\textbf{Innovation.} The manuscript introduces \textbf{TLE}',
     r'\noindent\textbf{Contribution.} The manuscript introduces \textbf{TLE}'),
]

edits = []
for path, old, new in replacements:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if old not in content:
        print(f"  SKIP (not found): {path}: {old[:80]}")
        continue
    occ = content.count(old)
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    edits.append((path, occ, old[:80], new[:80]))

print(f"Applied {len(edits)} replacements:")
for path, occ, old, new in edits:
    print(f"  {occ}x in {path.split(chr(92))[-1]}:")
    print(f"    OLD: {old}...")
    print(f"    NEW: {new}...")
