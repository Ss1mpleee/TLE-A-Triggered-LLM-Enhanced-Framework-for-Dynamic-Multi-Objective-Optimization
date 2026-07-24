"""Restore 05_results.tex.original to TRUE n=5 baseline.
This is a second pass to fix remaining issues.
"""
from pathlib import Path

RES_ORIG = Path(r'D:\新论文\论文\sections\05_results.tex.original')
text = RES_ORIG.read_text(encoding='utf-8')

# DE-LM-static 8-UAV mean changed (296.5 vs the script's expected 308.8)
# Just replace with the n=5 version
fixes = [
    (r"DE-LM-static-trigger & 219.5 $\pm$ 59.0 & 0.0938 & 296.5 $\pm$ 69.6 & 0.1250 \\",
     r"DE-LM-static-trigger & 225.0 $\pm$ 58.1 & 0.78 & 358.0 $\pm$ 82.6 & 0.31 \\"),
    # Other potential values
    (r"DE-LM-static-trigger & 219.5 $\pm$ 59.0 & 0.0938 & 303.1 $\pm$ 66.3 & 0.1250 \\",
     r"DE-LM-static-trigger & 225.0 $\pm$ 58.1 & 0.78 & 358.0 $\pm$ 82.6 & 0.31 \\"),
    (r"DE-LM-static-trigger & 219.5 $\pm$ 59.0 & 0.0938 & 308.8 $\pm$ 70.1 & 0.1250 \\",
     r"DE-LM-static-trigger & 225.0 $\pm$ 58.1 & 0.78 & 358.0 $\pm$ 82.6 & 0.31 \\"),
]
for old, new in fixes:
    if old in text:
        text = text.replace(old, new)
        print(f'Fixed: {old[:60]}')

# §5 UAV prose: find the dry-run version and replace
old_prose_marker = "On the dynamic multi-UAV scenario with $n = 30$ seeds per algorithm"
new_prose_marker = "On the dynamic multi-UAV scenario, TLE achieves a $16.8\\%$ improvement"
if old_prose_marker in text:
    # Find the full prose block
    start = text.find(old_prose_marker)
    end = text.find("The complete UAV results are given in Table~\\ref{tab:uav}.", start)
    if end > 0:
        end = end + len("The complete UAV results are given in Table~\\ref{tab_uav}.")
        # Find the next \n\n after end
        nl = text.find("\n\n", end)
        if nl > 0:
            end = nl
        print(f'Prose block: chars {start}-{end}')
        # Replace with original
        replacement = ("On the dynamic multi-UAV scenario, TLE achieves a $16.8\\%$ improvement in mean "
                       "cumulative task value over pure DE on the 8-UAV fleet (TLE: $389.0 \\pm 117.5$, "
                       "DE: $333.0 \\pm 57.1$), although the Wilcoxon signed-rank test (one-sided, $n = 5$ seeds) "
                       "returns $p = 0.156$, which does not reach the conventional $\\alpha = 0.05$ "
                       "significance threshold. On the 4-UAV fleet, the difference is smaller in magnitude "
                       "and not significant ($p = 0.28$). The complete UAV results are given in "
                       "Table~\\ref{tab:uav}. A noteworthy observation is that the classical diversity-injection "
                       "baseline DNSGA-II-A achieves the highest mean on both fleet sizes ($460.0 \\pm 100.0$ "
                       "on 8-UAV), confirming that the change-detection diversity mechanism is the dominant "
                       "contribution in this scenario rather than the LLM-triggered parameter adaptation; "
                       "the LLM contribution is most visible in the upper tail of the 8-UAV distribution "
                       "(TLE seed 4 reaches $f_1 = 555.0$ vs.\\ DE seed 4 $385.0$, a $+44\\%$ single-seed gap), "
                       "but the small sample size limits the statistical power. The Pareto fronts reached by "
                       "DE, DNSGA-II-A, and TLE on DF1, DF5, and DF7 (which the main paper only shows for DF2 "
                       "because DF2 is the only catastrophic-failure problem) are provided in "
                       "\\textbf{Supplementary Material, Section~S5, Fig.~S5}.\n\n")
        text = text[:start] + replacement + text[end:]
        print('Restored §5 UAV prose')
    else:
        print('Could not find end of §5 UAV prose')
else:
    print('§5 UAV prose not found')

# TLE row check (might be different)
# The n=5 baseline TLE row is:
# TLE (V0, UCB) & 246.0 $\pm$ 71.2 & 0.28 & 389.0 $\pm$ 117.5 & 0.16 \\
# The dry-run may have changed it to:
# TLE & 246.0 $\pm$ 71.2 & -- & 389.0 $\pm$ 117.5 & -- \\
old_tle = r"TLE & 246.0 $\pm$ 71.2 & -- & 389.0 $\pm$ 117.5 & -- \\"
new_tle = r"TLE (V0, UCB) & 246.0 $\pm$ 71.2 & 0.28 & 389.0 $\pm$ 117.5 & 0.16 \\"
if old_tle in text:
    text = text.replace(old_tle, new_tle)
    print('Restored TLE row')

# DNSGA row check
# Original: DNSGA-II-A & \textbf{273.0} $\pm$ 59.2 & 0.16 & \textbf{460.0} $\pm$ 100.0 & 0.94 \\
# Dry-run: DNSGA-II-A & \textbf{273.0 $\pm$ 59.2} & 1.0000 & \textbf{460.0 $\pm$ 100.0} & 1.0000 \\
old_dnsga = r"DNSGA-II-A & \textbf{273.0 $\pm$ 59.2} & 1.0000 & \textbf{460.0 $\pm$ 100.0} & 1.0000 \\"
new_dnsga = r"DNSGA-II-A & \textbf{273.0} $\pm$ 59.2 & 0.16 & \textbf{460.0} $\pm$ 100.0 & 0.94 \\"
if old_dnsga in text:
    text = text.replace(old_dnsga, new_dnsga)
    print('Restored DNSGA row')

# PPS row check
old_pps = r"PPS-DMOEA & 222.0 $\pm$ 53.3 & 0.1562 & 352.0 $\pm$ 92.4 & 0.2188 \\"
new_pps = r"PPS-DMOEA & 222.0 $\pm$ 53.3 & 0.84 & 352.0 $\pm$ 92.4 & 0.41 \\"
if old_pps in text:
    text = text.replace(old_pps, new_pps)
    print('Restored PPS row')

# DE row check
old_de = r"DE & 220.0 $\pm$ 54.8 & 0.2812 & 274.8 $\pm$ 54.0 & 0.1562 \\"
new_de = r"DE & 245.0 $\pm$ 65.1 & -- & 333.0 $\pm$ 57.1 & -- \\"
if old_de in text:
    text = text.replace(old_de, new_de)
    print('Restored DE row')

RES_ORIG.write_text(text, encoding='utf-8')

# Verify
print()
print('=== Verification ===')
print('n = 5 seeds count:', text.count('n = 5 seeds'))
print('n = 30 seeds count:', text.count('n = 30 seeds'))
print('16.8%:', '16.8\\%' in text)
print('41.5%:', '41.5%' in text)
print('0.1562 (BAD):', '0.1562' in text)
print('Tables:', text.count('\\begin{table}'))
print('Subsections:', text.count('\\subsection{'))