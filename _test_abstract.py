import re

# Test the abstract sentence pattern
abstract_text = "An extensive empirical study is conducted on the CEC 2018 dynamic multi-objective benchmark suite ($n = 8$ seeds per problem, $200$ generations, six algorithms) and on a dynamic multi-UAV task-allocation scenario ($n = 5$ seeds, two fleet sizes). A Friedman test reveals that TLE is statistically significantly worse than DNSGA-II-A and DE on the IGD metric ($\\chi^2_5 = 11.57$, $p = 0.041$, Nemenyi critical difference $\\mathrm{CD} = 3.408$); on the 8-UAV scenario, TLE shows a $16.8\\%$ higher mean cumulative task value than DE but the Wilcoxon signed-rank test (one-sided, $p = 0.156$ at $n = 5$ seeds) does not reach significance, and DNSGA-II-A achieves the highest overall mean on both UAV fleet sizes. A cross-LLM sensitivity analysis on three locally deployed open-source models (Qwen-2.5-7B, Qwen-3.5-9B, OmniCoder-9B) further delineates the regime in which LLM-guided DMO is beneficial: aggressive chat-tuned models unlock the projected improvement, whereas conservative reasoning- and code-tuned models produce byte-identical trajectories to plain DE. The framework, the LLM-call cache (5{,}156 entries), the benchmark scripts, and the run logs are released to facilitate reproducible follow-up research."

# Pattern 1: original
p1 = re.compile(
    r'on the 8-UAV scenario, TLE shows[^.]*?fleet sizes\.',
    re.DOTALL
)
m = p1.search(abstract_text)
print(f'Pattern 1: {bool(m)}')
if m:
    print(f'  matched: {m.group(0)[:200]}...')

# Pattern 2: just look for the period after fleet sizes
p2 = re.compile(
    r'on the 8-UAV scenario.*?fleet sizes\.',
    re.DOTALL
)
m = p2.search(abstract_text)
print(f'Pattern 2: {bool(m)}')
if m:
    print(f'  matched: {m.group(0)[:200]}...')

# Pattern 3: simple "8-UAV scenario" through "fleet sizes"
p3 = re.compile(
    r'(?:on the )?8-UAV scenario[^.]*?fleet sizes\.',
    re.DOTALL
)
m = p3.search(abstract_text)
print(f'Pattern 3: {bool(m)}')