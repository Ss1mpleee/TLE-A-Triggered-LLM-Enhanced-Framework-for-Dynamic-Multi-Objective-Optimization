#!/usr/bin/env python3
"""T70 round 1b: add abbreviation definitions at first use in main abstract."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = r'D:\新论文\论文\_submission\main_submission.tex'
with open(f, 'r', encoding='utf-8') as fh:
    content = fh.read()

edits = []

def apply(label, old, new, count=1):
    global content
    if old not in content:
        raise AssertionError(f"Edit anchor not found: {label}")
    occ = content.count(old)
    if occ < count:
        raise AssertionError(f"Edit anchor found {occ} times but {count} requested: {label}")
    content = content.replace(old, new, count)
    edits.append((label, occ, count))


# 1) Abstract (i) Scalability: define DNSGA-II-A and UAV
apply("abstract (i) DNSGA-II-A + UAV definition",
      r"\textbf{(i)~Scalability.} On the multi-UAV scenario, TLE reduces task cost by $\mathbf{21.2\%}$ / $\mathbf{20.4\%}$ / $\mathbf{19.0\%}$ over DNSGA-II-A at fleet sizes 8, 16, 32",
      r"\textbf{(i)~Scalability.} On the multi-Unmanned Aerial Vehicle (UAV) scenario, TLE reduces task cost by $\mathbf{21.2\%}$ / $\mathbf{20.4\%}$ / $\mathbf{19.0\%}$ over DNSGA-II-A (Dynamic Non-dominated Sorting Genetic Algorithm II with random immigrants) at fleet sizes 8, 16, 32")

# 2) Abstract (iii) Cross-LLM: define JSON before its first use
apply("abstract (iii) JSON definition first use",
      r"conservative code-tuned models produce byte-identical LLM JSON outputs and are indistinguishable from plain DE",
      r"conservative code-tuned models produce byte-identical LLM JavaScript object notation (JSON) outputs and are indistinguishable from plain DE")

# 3) Abstract (iii) Cross-LLM: define CD (critical difference)
apply("abstract (iii) CD first use (instance 1)",
      r"$\mathrm{CD} = 0.886$ for $k = 3$, $N = 14$",
      r"critical difference $\mathrm{CD} = 0.886$ for $k = 3$ LLMs, $N = 14$ problems",
      count=1)

# 4) Section 3.3 (architecture, L229): add NSGA-II full name
apply("L229 NSGA-II definition in arch caption",
      r"DE/rand/1/bin + NSGA-II search engine that runs the population at every generation",
      r"DE/rand/1/bin + NSGA-II (Non-dominated Sorting Genetic Algorithm II) search engine that runs the population at every generation")

# 5) Section 2 related work: add MOEA/DD full name first use
apply("L275 MOEA/DD full name first use",
      r"MOEA/DD~\cite{li2008moead} is itself a descendant of the original \mbox{{MOEA/D}} framework~\cite{zhang2007moead}",
      r"MOEA/DD (Multi-Objective Evolutionary Algorithm based on Dominance and Decomposition)~\cite{li2008moead} is itself a descendant of the original \mbox{{MOEA/D}} framework~\cite{zhang2007moead}")

# 6) Section 4 baselines: add DNSGA-II-A full name
apply("L494 DNSGA-II-A full name baselines",
      r"\item \textbf{DNSGA-II-A}~\cite{deb2007dnsga}: a classical dynamic MOEA that injects random immigrants after a change is detected",
      r"\item \textbf{DNSGA-II-A (Dynamic Non-dominated Sorting Genetic Algorithm II with random immigrants)}~\cite{deb2007dnsga}: a classical dynamic MOEA that injects random immigrants after a change is detected")

# 7) Section 4 baselines: PPS-DMOEA full name
apply("L495 PPS-DMOEA full name baselines",
      r"\item \textbf{PPS-DMOEA}~\cite{zhou2013pps}: a prediction-based dynamic MOEA that forecasts the next Pareto front",
      r"\item \textbf{PPS-DMOEA (Prediction-based Dynamic Multi-Objective Evolutionary Algorithm)}~\cite{zhou2013pps}: a prediction-based dynamic MOEA that forecasts the next Pareto front")

# 8) Section 4 baselines: MOEA/DD full name (if not already)
# Already added in (5)

# 9) Abstract (i): also define CEC if not defined (it IS in body, but add to abstract for completeness)
# Actually CEC is mentioned in the abstract intro: "On the full CEC 2018 DMO benchmark suite" but no definition.
# Let me add the CEC definition early in the abstract
apply("abstract CEC definition",
      r"On the full CEC 2018 DMO benchmark suite",
      r"On the full Congress on Evolutionary Computation (CEC) 2018 DMO benchmark suite")

# Save
with open(f, 'w', encoding='utf-8') as fh:
    fh.write(content)

print(f"\n=== main_submission.tex: {len(edits)} edit batches applied ===")
for label, occ, cnt in edits:
    print(f"  - {label}: {occ}x occurrence(s) -> replaced {cnt}x")
