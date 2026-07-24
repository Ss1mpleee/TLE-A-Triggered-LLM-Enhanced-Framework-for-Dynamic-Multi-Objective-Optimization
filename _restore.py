"""Restore main.tex Abstract to original (n=5, 16.8%) and Highlights to original.
This undoes the damage from _post_uav30_final.py dry-runs.
"""
import re
from pathlib import Path

TEX = Path(r'D:\新论文\论文\main.tex')
text = TEX.read_text(encoding='utf-8')

# Fix 1: Abstract — replace the corrupted duplicate with original
# The corrupted text has "on a dynamic multi-UAV task-allocation scenario ($n = 30$ seeds, two fleet sizes). A Friedman test reveals..."
# The original should be just "on the 8-UAV scenario, TLE shows a $16.8\%$ higher mean..."

old_abstract_pattern = re.compile(
    r"on a dynamic multi-UAV task-allocation scenario \(\$n = 30\$ seeds, two fleet sizes\)\. "
    r"A Friedman test reveals that TLE is statistically significantly worse than DNSGA-II-A and DE on the IGD metric "
    r"\(\$\\chi\^2_5 = 11\.57\$, \$p = 0\.041\$, Nemenyi critical difference \$\\mathrm\{CD\} = 3\.408\$\); "
    r"on the 8-UAV scenario, TLE shows a \+41\.5\\% mean improvement over DE but the Wilcoxon signed-rank test "
    r"\(one-sided, \$p = 0\.1562\$ at \$n = 30\$ seeds\) does not reach significance, and DNSGA-II-A achieves "
    r"the highest overall mean on both UAV fleet sizes"
)

new_abstract_text = ("on the 8-UAV scenario, TLE shows a $16.8\\%$ higher mean cumulative task value than DE "
                     "but the Wilcoxon signed-rank test (one-sided, $p = 0.156$ at $n = 5$ seeds) does not "
                     "reach significance, and DNSGA-II-A achieves the highest overall mean on both UAV fleet sizes")

text_new, n = old_abstract_pattern.subn(new_abstract_text, text)
if n == 0:
    print('WARNING: Abstract pattern not found')
else:
    text = text_new
    print(f'Restored Abstract (n={n})')

# Fix 2: Highlights — replace the +41.5% / n=30 with +16.8% / n=5
old_highlight = r"\item TLE loses to DNSGA-II-A on CEC 2018 DMO; shows +41.5\% mean improvement over DE on 8-UAV (Wilcoxon one-sided $p = 0.1562$ at $n = 30$ seeds, not significant at $\alpha = 0.05$)."
new_highlight = r"\item TLE loses to DNSGA-II-A on CEC 2018 DMO; shows +16.8\% mean improvement over DE on 8-UAV (Wilcoxon signed-rank one-sided $p = 0.156$ at $n = 5$ seeds, not significant at $\alpha = 0.05$)."

if old_highlight in text:
    text = text.replace(old_highlight, new_highlight)
    print('Restored Highlights bullet')
else:
    print('WARNING: Highlights bullet not found')

TEX.write_text(text, encoding='utf-8')
print(f'\nWrote {TEX}')

# Verify
text_after = TEX.read_text(encoding='utf-8')
print()
print('=== Verification ===')
print(f'Abstract "Friedman test reveals" count: {text_after.count("Friedman test reveals")}')
print(f'Abstract "16.8%" count: {text_after.count("16.8\\%")}')
print(f'Abstract "n = 5 seeds" count: {text_after.count("n = 5 seeds")}')
print(f'Abstract "n = 30 seeds" count: {text_after.count("n = 30 seeds")}')

# Highlights
m = re.search(r'item TLE loses to DNSGA-II-A[^\\]*?\\\\', text_after)
if m:
    print(f'Highlight: {m.group(0)[:200]}')