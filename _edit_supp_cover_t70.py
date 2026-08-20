#!/usr/bin/env python3
"""T70 round 1b: add abbreviation definitions in supp abstract and cover letter.

The supp L184 has a comprehensive abbreviation block but the abstract (L150-168)
uses IGD, HV, DE, etc. before that block. Add inline definitions.

The cover letter uses DE, NSGA-II, TLE, DNSGA-II-A, DMOEA etc. Add definitions.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Supp
f_supp = r'D:\新论文\论文\_submission\supplementary_material.tex'
with open(f_supp, 'r', encoding='utf-8') as fh:
    supp = fh.read()

edits_supp = []
def apply_supp(label, old, new, count=1):
    global supp
    if old not in supp:
        raise AssertionError(f"Supp edit anchor not found: {label}")
    occ = supp.count(old)
    if occ < count:
        raise AssertionError(f"Supp edit anchor found {occ} times but {count} requested: {label}")
    supp = supp.replace(old, new, count)
    edits_supp.append((label, occ, count))


# Supp abstract (L150-168): add IGD, HV, DE, TLE definitions
apply_supp("supp abstract IGD + DE definitions",
           r"This supplementary material complements the main manuscript with five",
           r"This supplementary material complements the main manuscript, where IGD = Inverted Generational Distance, HV = Hypervolume, DE = Differential Evolution, NSGA-II = Non-dominated Sorting Genetic Algorithm II, TLE = Triggered LLM-Enhanced Evolutionary Algorithm, and DNSGA-II-A = Dynamic NSGA-II with random immigrants (the same abbreviations as in the main manuscript), with five")

# Cover letter
f_cover = r'D:\新论文\论文\_submission\cover_letter.tex'
with open(f_cover, 'r', encoding='utf-8') as fh:
    cover = fh.read()

edits_cover = []
def apply_cover(label, old, new, count=1):
    global cover
    if old not in cover:
        raise AssertionError(f"Cover edit anchor not found: {label}")
    occ = cover.count(old)
    if occ < count:
        raise AssertionError(f"Cover edit anchor found {occ} times but {count} requested: {label}")
    cover = cover.replace(old, new, count)
    edits_cover.append((label, occ, count))


# Cover letter: add DE definition (when first used)
apply_cover("cover DE definition",
            r"the 3-objective DF9--DF14, six algorithms, $n = 30$ seeds per problem",
            r"the 3-objective DF9--DF14, six algorithms (DE = Differential Evolution, TLE = Triggered LLM-Enhanced Evolutionary Algorithm, DNSGA-II-A = Dynamic NSGA-II with random immigrants, MOEA/DD = Multi-Objective Evolutionary Algorithm based on Dominance and Decomposition), $n = 30$ seeds per problem")

# Cover letter: add Friedman test definition
apply_cover("cover Friedman test definition",
            r"TLE is statistically competitive with the strongest classical baseline (Friedman rank",
            r"TLE is statistically competitive with the strongest classical baseline (Friedman test rank")

# Cover letter: add Wilcoxon definition
apply_cover("cover Wilcoxon definition",
            r"fleet sizes 8/16/32 (Wilcoxon $\mathbf{p} \leq 0.0312$)",
            r"fleet sizes 8/16/32 (Wilcoxon signed-rank test $\mathbf{p} \leq 0.0312$)")

# Save
with open(f_supp, 'w', encoding='utf-8') as fh:
    fh.write(supp)
with open(f_cover, 'w', encoding='utf-8') as fh:
    fh.write(cover)

print(f"=== supplementary_material.tex: {len(edits_supp)} edit batches applied ===")
for label, occ, cnt in edits_supp:
    print(f"  - {label}: {occ}x occurrence(s) -> replaced {cnt}x")
print(f"\n=== cover_letter.tex: {len(edits_cover)} edit batches applied ===")
for label, occ, cnt in edits_cover:
    print(f"  - {label}: {occ}x occurrence(s) -> replaced {cnt}x")
