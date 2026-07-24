"""Restore main.tex and 05_results.tex to TRUE n=5 baseline (pre-dry-run).
This is the canonical n=5 / 16.8% / p=0.156 state that the post-script will use
as its starting point.
"""
import re
from pathlib import Path

ORIG = Path(r'D:\新论文\论文\main.tex.original')
RES_ORIG = Path(r'D:\新论文\论文\sections\05_results.tex.original')

# Fix main.tex.original
text = ORIG.read_text(encoding='utf-8')

# Restore Highlights
old_hl = (r"\item TLE loses to DNSGA-II-A on CEC 2018 DMO; shows +41.5\% mean improvement "
          r"over DE on 8-UAV (Wilcoxon one-sided $p = 0.1562$ at $n = 5$ seeds, "
          r"not significant at $\alpha = 0.05$).")
new_hl = (r"\item TLE loses to DNSGA-II-A on CEC 2018 DMO; shows +16.8\% mean improvement "
          r"over DE on 8-UAV (Wilcoxon signed-rank one-sided $p = 0.156$ at $n = 5$ seeds, "
          r"not significant at $\alpha = 0.05$).")
if old_hl in text:
    text = text.replace(old_hl, new_hl)
    print('Restored Highlights')
else:
    print('WARNING: old Highlights not found in .original')

# Restore Abstract sentence
old_abs = (r"on the 8-UAV scenario, TLE shows a +41.5\% mean improvement over DE but "
           r"the Wilcoxon signed-rank test (one-sided, $p = 0.1562$ at $n = 5$ seeds) does "
           r"not reach significance, and DNSGA-II-A achieves the highest overall mean on both UAV fleet sizes")
new_abs = (r"on the 8-UAV scenario, TLE shows a $16.8\%$ higher mean cumulative task value "
           r"than DE but the Wilcoxon signed-rank test (one-sided, $p = 0.156$ at $n = 5$ "
           r"seeds) does not reach significance, and DNSGA-II-A achieves the highest overall "
           r"mean on both UAV fleet sizes")
if old_abs in text:
    text = text.replace(old_abs, new_abs)
    print('Restored Abstract')
else:
    print('WARNING: old Abstract sentence not found in .original')

ORIG.write_text(text, encoding='utf-8')
print(f'Wrote {ORIG}')

# Fix 05_results.tex.original
res_text = RES_ORIG.read_text(encoding='utf-8')

# Restore §5 UAV prose (find the dry-run version)
old_prose = (r"On the dynamic multi-UAV scenario with $n = 30$ seeds per algorithm "
             r"(paired by scenario seed), TLE shows a +41.5\% higher mean cumulative task value "
             r"than pure DE on the 8-UAV fleet (TLE: $389.0 \pm 117.5$, DE: $274.8 \pm 54.0$), "
             r"but the Wilcoxon signed-rank test (one-sided, $n = 30$ paired seeds) returns "
             r"$p = 0.1562$, which does not reach the conventional $\alpha = 0.05$ significance "
             r"threshold. The classical diversity-injection baseline DNSGA-II-A achieves the highest "
             r"mean on the 8-UAV fleet ($460.0 \pm 100.0$), confirming that the change-detection "
             r"diversity mechanism is the dominant contribution in this scenario. On the 4-UAV fleet, "
             r"the difference between TLE and DE is smaller in magnitude (+11.8\% mean, Wilcoxon one-sided "
             r"$p = 0.2812$) and not significant. The complete UAV results are given in Table~\ref{tab:uav}.")
new_prose = (r"On the dynamic multi-UAV scenario, TLE achieves a $16.8\%$ improvement in mean "
             r"cumulative task value over pure DE on the 8-UAV fleet (TLE: $389.0 \pm 117.5$, "
             r"DE: $333.0 \pm 57.1$), although the Wilcoxon signed-rank test (one-sided, $n = 5$ seeds) "
             r"returns $p = 0.156$, which does not reach the conventional $\alpha = 0.05$ "
             r"significance threshold. On the 4-UAV fleet, the difference is smaller in magnitude "
             r"and not significant ($p = 0.28$). The complete UAV results are given in "
             r"Table~\ref{tab:uav}. A noteworthy observation is that the classical diversity-injection "
             r"baseline DNSGA-II-A achieves the highest mean on both fleet sizes ($460.0 \pm 100.0$ "
             r"on 8-UAV), confirming that the change-detection diversity mechanism is the dominant "
             r"contribution in this scenario rather than the LLM-triggered parameter adaptation; "
             r"the LLM contribution is most visible in the upper tail of the 8-UAV distribution "
             r"(TLE seed 4 reaches $f_1 = 555.0$ vs.\ DE seed 4 $385.0$, a $+44\%$ single-seed gap), "
             r"but the small sample size limits the statistical power. The Pareto fronts reached by "
             r"DE, DNSGA-II-A, and TLE on DF1, DF5, and DF7 (which the main paper only shows for DF2 "
             r"because DF2 is the only catastrophic-failure problem) are provided in "
             r"\textbf{Supplementary Material, Section~S5, Fig.~S5}.")
if old_prose in res_text:
    res_text = res_text.replace(old_prose, new_prose)
    print('Restored §5 UAV prose')
else:
    print('WARNING: old §5 UAV prose not found in 05_results.original')

# Restore Table 5 (find the dry-run version)
old_table5_cap = (r"\caption{Multi-UAV task allocation ($n = 30$ seeds, paired by scenario seed). "
                  r"Cumulative task value $f_1$ (higher is better). The Wilcoxon signed-rank "
                  r"$p$-values are computed one-sided against each baseline (alternative: "
                  r"\texttt{TLE} $>$ baseline). Significance markers: $^{*}p<0.05$, $^{**}p<0.01$, "
                  r"$^{***}p<0.001$.}")
new_table5_cap = (r"\caption{Multi-UAV task allocation ($n = 5$ seeds). Cumulative task value $f_1$ "
                  r"(higher is better). The Wilcoxon signed-rank $p$-values are computed one-sided "
                  r"against DE (alternative: algorithm $>$ DE). TLE shows a $16.8\%$ mean improvement "
                  r"over DE on 8-UAV but does not reach $\alpha = 0.05$ significance at $n = 5$; "
                  r"DNSGA-II-A achieves the highest mean on both fleet sizes.}")
if old_table5_cap in res_text:
    res_text = res_text.replace(old_table5_cap, new_table5_cap)
    print('Restored Table 5 caption')
else:
    print('WARNING: old Table 5 caption not found')

# Restore Table 5 contents (4-UAV $f_1$ & 4-UAV $p$ vs.\ DE & 8-UAV $f_1$ & 8-UAV $p$ vs.\ DE)
old_table5_header = (r"\toprule" + "\n"
                     r"Algorithm & 4-UAV $f_1$ & 4-UAV $p$ vs.\ TLE & 8-UAV $f_1$ & 8-UAV $p$ vs.\ TLE \\")
new_table5_header = (r"\toprule" + "\n"
                     r"Algorithm & 4-UAV $f_1$ & 4-UAV $p$ vs.\ DE & 8-UAV $f_1$ & 8-UAV $p$ vs.\ DE \\")
if old_table5_header in res_text:
    res_text = res_text.replace(old_table5_header, new_table5_header)
    print('Restored Table 5 header')

# Restore Table 5 data rows (DE-LM-static, PPS, DNSGA, TLE)
# Find and replace DE-LM-static row
old_rows_data = [
    (r"DE & 220.0 $\pm$ 54.8 & 0.2812 & 274.8 $\pm$ 54.0 & 0.1562 \\",
     r"DE & 245.0 $\pm$ 65.1 & -- & 333.0 $\pm$ 57.1 & -- \\"),
    (r"DE-LM-static-trigger & 219.5 $\pm$ 59.0 & 0.0938 & 308.8 $\pm$ 70.1 & 0.1250 \\",
     r"DE-LM-static-trigger & 225.0 $\pm$ 58.1 & 0.78 & 358.0 $\pm$ 82.6 & 0.31 \\"),
    (r"PPS-DMOEA & 222.0 $\pm$ 53.3 & 0.1562 & 352.0 $\pm$ 92.4 & 0.2188 \\",
     r"PPS-DMOEA & 222.0 $\pm$ 53.3 & 0.84 & 352.0 $\pm$ 92.4 & 0.41 \\"),
    (r"DNSGA-II-A & \textbf{273.0 $\pm$ 59.2} & 1.0000 & \textbf{460.0 $\pm$ 100.0} & 1.0000 \\",
     r"DNSGA-II-A & \textbf{273.0} $\pm$ 59.2 & 0.16 & \textbf{460.0} $\pm$ 100.0 & 0.94 \\"),
    (r"TLE & 246.0 $\pm$ 71.2 & -- & 389.0 $\pm$ 117.5 & -- \\",
     r"TLE (V0, UCB) & 246.0 $\pm$ 71.2 & 0.28 & 389.0 $\pm$ 117.5 & 0.16 \\"),
]
for old, new in old_rows_data:
    if old in res_text:
        res_text = res_text.replace(old, new)
        print(f'  Restored row: {old[:50]}...')
    else:
        print(f'  WARNING: row not found: {old[:50]}...')

RES_ORIG.write_text(res_text, encoding='utf-8')
print(f'\nWrote {RES_ORIG}')

# Verification
print('\n=== Verification ===')
text_check = ORIG.read_text(encoding='utf-8')
print('main.original has 16.8%:', '16.8\\%' in text_check)
print('main.original has 41.5%:', '41.5%' in text_check)
print('main.original has 0.156 (not 0.1562):', '$p = 0.156$' in text_check)
print('main.original has 0.1562 (BAD):', '$p = 0.1562$' in text_check)

res_check = RES_ORIG.read_text(encoding='utf-8')
print('05_results.original has 16.8%:', '16.8\\%' in res_check)
print('05_results.original has 41.5%:', '41.5%' in res_check)
print('05_results.original has 0.1562 (BAD):', '0.1562' in res_check)
print('05_results.original has 5 tables:', res_check.count('\\begin{table}'))
print('05_results.original has 8 subsections:', res_check.count('\\subsection{'))