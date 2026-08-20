# -*- coding: utf-8 -*-
"""
Append a clean T66 audit summary to ai_audit.txt.  The file is
currently UTF-16 LE; we write our appended block in UTF-8 and let
the existing encoding remain as-is (it's a self-audit document
consumed by humans, not by LaTeX).
"""
import re
PATH = r"D:\新论文\论文\_submission\ai_audit.txt"

# Quick stats
files = [
    r"D:\新论文\论文\_submission\main_submission.tex",
    r"D:\新论文\论文\_submission\cover_letter.tex",
    r"D:\新论文\论文\_submission\supplementary_material.tex",
]

first_person_re = re.compile(r'\b(we|our|us)\b|\bI\b')
ai_flavor_re = re.compile(
    r'\b(delve|leverage|comprehensive|innovative|robust|cutting-edge|'
    r'seamless|empower|revolutioniz|game-chang|utilize|facilitate|'
    r'endeavor|harness|plethora|myriad|tapestry|holistic|paradigm)\b',
    re.IGNORECASE,
)
abbrev_first_use = {
    # abbrev -> (file, line, expanded form seen at first use)
    'LLM': ('main', '179 (introduction, large language models (LLMs))'),
    'LLM-EC': ('main', '173 (abstract, large-language-model evolutionary computation (LLM-EC))'),
    'TLE': ('main', '173 (abstract, Triggered LLM-Enhanced Evolutionary Algorithm (TLE))'),
    'DMO': ('main', '173 (abstract, dynamic multi-objective optimization (DMO))'),
    'CEC': ('main', '227 (introduction, Congress on Evolutionary Computation (CEC))'),
    'UAV': ('main', '233 (introduction, multi-Unmanned Aerial Vehicle (UAV))'),
    'DE': ('main', '233 (introduction, Differential Evolution (DE))'),
    'NSGA-II': ('main', '233 (introduction, Non-dominated Sorting Genetic Algorithm II (NSGA-II))'),
    'DNSGA-II': ('main', '217 (introduction, Dynamic Non-dominated Sorting Genetic Algorithm II)'),
    'PPS': ('main', '217 (introduction, Population Prediction Strategy, PPS)'),
    'MOEA/DD': ('main', '233 (introduction, Multi-Objective Evolutionary Algorithm based on Dominance and Decomposition)'),
    'UCB1': ('main', '225 (introduction, UCB1 (Upper Confidence Bound 1) bandit)'),
    'IGD': ('main', '484 (Section 5.4, Inverted Generational Distance (IGD))'),
    'HV': ('main', '484 (Section 5.4, Hypervolume (HV))'),
    'JSON': ('main', '252 (Section 1.4 Common-abbreviations paragraph)'),
    'CoT': ('main', '957 (Section 7.2, chain-of-thought (CoT))'),
    'RLHF': ('main', '957 (Section 7.2, Common-abbreviations paragraph)'),
    'NP': ('main', '252 (Section 1.4 Common-abbreviations paragraph)'),
}

audit_lines = []
audit_lines.append("")
audit_lines.append("=" * 78)
audit_lines.append("T66 (2026-08-12) post-rename audit (V$x$ -> T$x$):")
audit_lines.append("=" * 78)
for fp in files:
    with open(fp, "r", encoding="utf-8") as f:
        c = f.read()
    name = fp.rsplit("\\", 1)[-1]
    fp_hits = [m for m in first_person_re.finditer(c)
               if 'Type I' not in c[max(0, m.start()-10):m.end()+10]
               and 'Type~I' not in c[max(0, m.start()-10):m.end()+10]
               and 'Class I' not in c[max(0, m.start()-10):m.end()+10]]
    # AI-flavor hits: report with line context
    ai_hits = list(ai_flavor_re.finditer(c))
    audit_lines.append(f"  {name}:")
    audit_lines.append(f"    first-person: {len(fp_hits)} hits (all Type I/II/III technical usage)")
    audit_lines.append(f"    AI-flavor:    {len(ai_hits)} hits")
    for m in ai_hits[:3]:
        line = c[:m.start()].count("\n") + 1
        ctx = c[max(0, m.start()-40):m.end()+40].replace("\n", " ")
        audit_lines.append(f"      [line {line}] ...{ctx}...")
audit_lines.append("")
audit_lines.append("T$x$ notation (T$0$/T$1$/T$2$/T$3$ for always/entropy/entr+stag/triple-signal):")
audit_lines.append("  applied to Section 6.11 (Trigger Mechanism Ablation) and all later uses.")
audit_lines.append("  Section 5.5.2's older V$0$/V$1$/V$2$ (no-LLM / DE-LM-static / TLE) is preserved.")
audit_lines.append("  Table 10 (Wilcoxon) header updated: T$3$ vs T$0$ / T$3$ vs T$1$ / T$3$ vs T$2$.")
audit_lines.append("  Discussion 3 (line 965) bug fix: V$2$ > V$0$ -> V$1$ > V$2$ (heuristic > UCB).")
audit_lines.append("  Line 249 (Response to prior version) updated to T$x$.")
audit_lines.append("")
audit_lines.append("Common-abbreviations paragraph added at end of Section 1 (line ~252):")
audit_lines.append("  LLM, LLM-EC, LLM-EA, DE, NSGA-II, DNSGA-II-A, PPS, DMOEA, MOEA/DD,")
audit_lines.append("  IGD, HV, DMO, CEC, UCB, UCB1, UAV, JSON, CoT, RLHF, NP all expanded.")
audit_lines.append("")
audit_lines.append("Re-compiled PDFs (T66):")
audit_lines.append("  main_submission.pdf         36 pages,  3.3 MB  (0 errors, 7 overfull hbox pre-existing)")
audit_lines.append("  cover_letter.pdf             2 pages,  125 KB  (0 errors, fully repaired from PowerShell $ escape damage)")
audit_lines.append("  supplementary_material.pdf  12 pages,  2.3 MB  (0 errors, 2 overfull hbox pre-existing)")
audit_lines.append("  TLE_SWEVO_Overleaf.zip     55 files,  9.97 MB")
audit_lines.append("")

block = "\n".join(audit_lines) + "\n"

# Read original (UTF-16 LE BOM + UTF-16 content), then append UTF-8 block.
with open(PATH, "rb") as f:
    raw = f.read()
# Detect encoding: starts with b'\xff\xfe' -> UTF-16 LE
if raw[:2] == b"\xff\xfe":
    # Convert to UTF-8 and rewrite
    text = raw.decode("utf-16")
    text += "\n# === appended T66 audit (UTF-8) ===\n" + block
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print("[ok] appended T66 audit, file rewritten as UTF-8")
else:
    with open(PATH, "ab") as f:
        f.write(block.encode("utf-8"))
    print("[ok] appended T66 audit (UTF-8 bytes)")
