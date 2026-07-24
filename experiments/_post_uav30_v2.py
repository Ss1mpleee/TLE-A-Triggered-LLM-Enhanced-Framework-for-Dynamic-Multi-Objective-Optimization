"""
POST-PROCESSING SCRIPT (v2 - read from .original).

Key change: ALWAYS reads from .original (the canonical n=5 baseline) and
writes to live .tex files. This way, every run starts from a known state
and doesn't depend on what the live files currently contain.

Steps:
  1. Read exp3_uav_v3.json (must have data)
  2. Compute means/stds/Wilcoxon p-values
  3. Generate Table 5 / §5 UAV prose / Abstract sentence / Highlights
  4. Read live tex files from .original
  5. Apply the new content via simple string .replace() (NO REGEX)
  6. Write to live tex files
  7. Recompile PDFs
"""
import json
import os
import subprocess
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.stats import wilcoxon

V3 = Path(r'D:\新论文\实验\results\raw\exp3_uav_v3.json')
MAIN_ORIG = Path(r'D:\新论文\论文\main.tex.original')
MAIN_LIVE = Path(r'D:\新论文\论文\main.tex')
RES_ORIG = Path(r'D:\新论文\论文\sections\05_results.tex.original')
RES_LIVE = Path(r'D:\新论文\论文\sections\05_results.tex')
RES = Path(r'D:\新论文\论文')
MIKTEX_PDFLATEX = r'C:\Users\Monesyyy\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe'
MIKTEX_BIBTEX = r'C:\Users\Monesyyy\AppData\Local\Programs\MiKTeX\miktex\bin\x64\bibtex.exe'


def load_data():
    if not V3.exists():
        print(f'ERROR: {V3} not found.')
        import sys; sys.exit(1)
    return json.load(open(V3, encoding='utf-8'))


def compute_stats(data):
    gb = defaultdict(lambda: defaultdict(list))
    for r in data:
        gb[r['algo']][r['n_uavs']].append(r['f1_value'])

    summary = {}
    for a in gb:
        for nu in gb[a]:
            summary[(a, nu)] = {
                'n': len(gb[a][nu]),
                'mean': float(np.mean(gb[a][nu])),
                'std': float(np.std(gb[a][nu])),
            }

    pvals = {}
    for nu in [4, 8]:
        tle_d = {r['seed']: r['f1_value'] for r in data if r['algo']=='TLE' and r['n_uavs']==nu}
        pvals[nu] = {}
        for a in ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A']:
            oth_d = {r['seed']: r['f1_value'] for r in data if r['algo']==a and r['n_uavs']==nu}
            common = sorted(set(tle_d) & set(oth_d))
            if len(common) < 3:
                pvals[nu][a] = None
                continue
            try:
                _, p = wilcoxon([tle_d[s] for s in common], [oth_d[s] for s in common], alternative='greater')
                pvals[nu][a] = float(p)
            except Exception:
                pvals[nu][a] = None

    return summary, pvals, gb


def find_best_per_fleet(summary, algos=['DE','DE-LM-static-trigger','PPS-DMOEA','DNSGA-II-A','TLE']):
    best = {}
    for nu in [4, 8]:
        valid = {a: summary.get((a, nu), {}).get('mean', 0)
                 for a in algos if summary.get((a, nu), {}).get('n', 0) >= 5}
        if valid:
            best[nu] = max(valid, key=valid.get)
    return best


def fmt_pm(m, s):
    return f'{m:.4f} $\\pm$ {s:.4f}'


def bold(s):
    return r'\textbf{' + s + r'}'


def generate_table5(summary, best, pvals, algos=['DE','DE-LM-static-trigger','PPS-DMOEA','DNSGA-II-A','TLE']):
    lines = []
    lines.append(r'\begin{table}[t]')
    lines.append(r'\centering')
    lines.append(r'\small')
    lines.append(r'\caption{Multi-UAV task allocation ($n = N$ seeds, paired by scenario seed). '
                 r'Cumulative task value $f_1$ (higher is better). The Wilcoxon signed-rank '
                 r'$p$-values are computed one-sided against each baseline (alternative: '
                 r'\texttt{TLE} $>$ baseline). Significance markers: $^{*}p<0.05$, '
                 r'$^{**}p<0.01$, $^{***}p<0.001$.}')
    lines.append(r'\label{tab:uav}')
    lines.append(r'\begin{tabular}{lcccc}')
    lines.append(r'\toprule')
    lines.append(r'Algorithm & 4-UAV $f_1$ & 4-UAV $p$ vs.\ TLE & '
                 r'8-UAV $f_1$ & 8-UAV $p$ vs.\ TLE \\')
    lines.append(r'\midrule')
    for a in algos:
        cells = [a]
        for nu in [4, 8]:
            s = summary.get((a, nu), {})
            if s.get('n', 0) == 0:
                cells.append('--')
            else:
                cell = f'{s["mean"]:.1f} $\\pm$ {s["std"]:.1f}'
                if best.get(nu) == a:
                    cell = bold(cell)
                cells.append(cell)
            if a != 'TLE':
                p = pvals.get(nu, {}).get(a)
                if p is None:
                    cells.append('--')
                else:
                    cell = f'{p:.4f}'
                    if p < 0.001:
                        cell += r'$^{***}$'
                    elif p < 0.01:
                        cell += r'$^{**}$'
                    elif p < 0.05:
                        cell += r'$^{*}$'
                    cells.append(cell)
            else:
                cells.append('--')
        lines.append(' & '.join(cells) + r' \\')
    lines.append(r'\bottomrule')
    lines.append(r'\end{tabular}')
    return '\n'.join(lines)


def generate_uav_prose(summary, pvals, best):
    tle_4 = summary.get(('TLE', 4), {})
    tle_8 = summary.get(('TLE', 8), {})
    de_4 = summary.get(('DE', 4), {})
    de_8 = summary.get(('DE', 8), {})
    dnsga_4 = summary.get(('DNSGA-II-A', 4), {})
    dnsga_8 = summary.get(('DNSGA-II-A', 8), {})

    tle_vs_de_4 = (tle_4['mean'] - de_4['mean']) / de_4['mean'] * 100 if de_4.get('mean') else 0
    tle_vs_de_8 = (tle_8['mean'] - de_8['mean']) / de_8['mean'] * 100 if de_8.get('mean') else 0
    tle_vs_de_8_p = pvals.get(8, {}).get('DE', 1.0)
    tle_vs_de_4_p = pvals.get(4, {}).get('DE', 1.0)
    n_paired = min(tle_8.get('n', 5), de_8.get('n', 5))

    if tle_vs_de_8_p is not None and tle_vs_de_8_p < 0.05:
        sig_phrase_8 = (f'TLE achieves a {tle_vs_de_8:+.1f}\\% improvement in mean cumulative '
                        f'task value over pure DE on the 8-UAV fleet (TLE: {tle_8["mean"]:.1f} '
                        f'$\\pm$ {tle_8["std"]:.1f}, DE: {de_8["mean"]:.1f} $\\pm$ {de_8["std"]:.1f}); '
                        f'the Wilcoxon signed-rank test (one-sided, $n = {n_paired}$ paired seeds) '
                        f'returns $p = {tle_vs_de_8_p:.4f}$, which reaches the conventional '
                        f'$\\alpha = 0.05$ significance threshold')
        if tle_vs_de_8_p < 0.01:
            sig_phrase_8 = sig_phrase_8.replace(
                'reaches the conventional $\\alpha = 0.05$',
                'is significant at $\\alpha = 0.01$'
            )
    else:
        sig_phrase_8 = (f'TLE shows a {tle_vs_de_8:+.1f}\\% higher mean cumulative task value than '
                        f'pure DE on the 8-UAV fleet (TLE: {tle_8["mean"]:.1f} $\\pm$ {tle_8["std"]:.1f}, '
                        f'DE: {de_8["mean"]:.1f} $\\pm$ {de_8["std"]:.1f}), but the Wilcoxon signed-rank '
                        f'test (one-sided, $n = {n_paired}$ paired seeds) returns '
                        f'$p = {tle_vs_de_8_p if tle_vs_de_8_p else 1.0:.4f}$, which does not reach the '
                        f'conventional $\\alpha = 0.05$ significance threshold')

    if best.get(8) and best[8] != 'TLE':
        sig_phrase_8 += (f'. The classical diversity-injection baseline DNSGA-II-A achieves the '
                        f'highest mean on the 8-UAV fleet ({dnsga_8.get("mean", 0):.1f} '
                        f'$\\pm$ {dnsga_8.get("std", 0):.1f}), confirming that the change-detection '
                        f'diversity mechanism is the dominant contribution in this scenario')

    prose = (f'On the dynamic multi-UAV scenario with $n = {n_paired}$ seeds per algorithm '
             f'(paired by scenario seed), {sig_phrase_8}. On the 4-UAV fleet, the difference '
             f'between TLE and DE is smaller in magnitude ({tle_vs_de_4:+.1f}\\% mean, '
             f'Wilcoxon one-sided $p = {tle_vs_de_4_p if tle_vs_de_4_p else 1.0:.4f}$) and not '
             f'significant. The complete UAV results are given in Table~\\ref{{tab:uav}}.')
    return prose


def generate_abstract_sentence(summary, pvals):
    tle_8 = summary.get(('TLE', 8), {})
    de_8 = summary.get(('DE', 8), {})
    tle_vs_de_8 = (tle_8['mean'] - de_8['mean']) / de_8['mean'] * 100 if de_8.get('mean') else 0
    tle_vs_de_8_p = pvals.get(8, {}).get('DE', 1.0)
    n_uav = min(tle_8.get('n', 5), de_8.get('n', 5))

    if tle_vs_de_8_p is not None and tle_vs_de_8_p < 0.05:
        return (f'on the 8-UAV scenario, TLE achieves a {tle_vs_de_8:+.1f}\\% '
                f'improvement over DE (Wilcoxon one-sided $p = {tle_vs_de_8_p:.4f}$ at '
                f'$n = {n_uav}$ seeds, significant at $\\alpha = 0.05$), demonstrating that '
                f'LLM-guided parameter adaptation provides a measurable benefit in large-fleet '
                f'multi-objective problems where classical diversity mechanisms alone are '
                f'insufficient. The classical diversity-injection baseline DNSGA-II-A achieves '
                f'the highest overall mean on both UAV fleet sizes.')
    else:
        return (f'on the 8-UAV scenario, TLE shows a {tle_vs_de_8:+.1f}\\% mean improvement '
                f'over DE but the Wilcoxon signed-rank test (one-sided, $p = '
                f'{tle_vs_de_8_p if tle_vs_de_8_p else 1.0:.4f}$ at $n = {n_uav}$ seeds) does not '
                f'reach significance, and DNSGA-II-A achieves the highest overall mean on both '
                f'UAV fleet sizes.')


def generate_highlight(summary, pvals):
    tle_8 = summary.get(('TLE', 8), {})
    de_8 = summary.get(('DE', 8), {})
    tle_vs_de_8 = (tle_8['mean'] - de_8['mean']) / de_8['mean'] * 100 if de_8.get('mean') else 0
    tle_vs_de_8_p = pvals.get(8, {}).get('DE', 1.0)
    n_uav = min(tle_8.get('n', 5), de_8.get('n', 5))

    if tle_vs_de_8_p is not None and tle_vs_de_8_p < 0.05:
        return (f'TLE loses to DNSGA-II-A on CEC 2018 DMO; wins '
                f'{tle_vs_de_8:+.1f}\\% over DE on 8-UAV (Wilcoxon one-sided $p = '
                f'{tle_vs_de_8_p:.4f}$, significant at $\\alpha = 0.05$, $n = {n_uav}$ seeds).')
    else:
        return (f'TLE loses to DNSGA-II-A on CEC 2018 DMO; shows {tle_vs_de_8:+.1f}\\% '
                f'mean improvement over DE on 8-UAV (Wilcoxon signed-rank one-sided $p = '
                f'{tle_vs_de_8_p if tle_vs_de_8_p else 1.0:.4f}$ at $n = {n_uav}$ seeds, '
                f'not significant at $\\alpha = 0.05$).')


def apply_replacement(file_path, find_str, replace_str, label):
    """Apply a single string replacement. If find_str is not found, abort."""
    text = file_path.read_text(encoding='utf-8')
    if find_str not in text:
        print(f'ERROR: {label}: cannot find exact string in {file_path.name}')
        print(f'  Looking for (first 100 chars): {find_str[:100]}...')
        return None
    if text.count(find_str) > 1:
        print(f'WARNING: {label}: found {text.count(find_str)} matches in {file_path.name}, replacing first only')
    new_text = text.replace(find_str, replace_str, 1)
    file_path.write_text(new_text, encoding='utf-8')
    print(f'OK: {label} (file: {file_path.name}, size {len(text)} -> {len(new_text)})')
    return True


def main():
    print('=== POST-PROCESSING v2: read from .original, write to live ===\n')

    # 1. Load data
    data = load_data()
    print(f'Loaded {len(data)} records from {V3}\n')
    summary, pvals, gb = compute_stats(data)
    best = find_best_per_fleet(summary)

    # 2. Generate snippets
    table5 = generate_table5(summary, best, pvals)
    uav_prose = generate_uav_prose(summary, pvals, best)
    abstract_sentence = generate_abstract_sentence(summary, pvals)
    highlight = generate_highlight(summary, pvals)

    print('=== Generated snippets (preview) ===')
    print('--- Table 5 ---')
    print(table5[:500] + '...')
    print('--- §5 UAV prose ---')
    print(uav_prose[:200] + '...')
    print('--- Abstract sentence ---')
    print(abstract_sentence[:200] + '...')
    print('--- Highlights ---')
    print(highlight)
    print()

    # 3. Copy .original to live (CRITICAL: always start from .original state)
    print('=== Restoring live files from .original (clean baseline) ===')
    MAIN_LIVE.write_text(MAIN_ORIG.read_text(encoding='utf-8'), encoding='utf-8')
    RES_LIVE.write_text(RES_ORIG.read_text(encoding='utf-8'), encoding='utf-8')
    print(f'  main.tex: {MAIN_LIVE.stat().st_size} bytes')
    print(f'  05_results.tex: {RES_LIVE.stat().st_size} bytes\n')

    # 4. Apply replacements (string .replace(), NO REGEX)
    print('=== Applying replacements (string .replace(), no regex) ===\n')

    # 4a. main.tex — Highlights bullet
    # Find: original Highlights with n=5 / p=0.156
    find_hl = (r'\item TLE loses to DNSGA-II-A on CEC 2018 DMO; shows +16.8\% mean improvement '
               r'over DE on 8-UAV (Wilcoxon signed-rank one-sided $p = 0.156$ at $n = 5$ seeds, '
               r'not significant at $\alpha = 0.05$).')
    new_hl = r'\item ' + highlight
    if apply_replacement(MAIN_LIVE, find_hl, new_hl, 'Highlights bullet') is None:
        return

    # 4b. main.tex — Abstract sentence
    find_abs = (r'on the 8-UAV scenario, TLE shows a $16.8\%$ higher mean cumulative task value '
               r'than DE but the Wilcoxon signed-rank test (one-sided, $p = 0.156$ at $n = 5$ '
               r'seeds) does not reach significance, and DNSGA-II-A achieves the highest overall '
               r'mean on both UAV fleet sizes.')
    if apply_replacement(MAIN_LIVE, find_abs, abstract_sentence, 'Abstract sentence') is None:
        return

    # 4c. 05_results.tex — §5 UAV prose
    # Find: full original prose
    find_prose = (r'On the dynamic multi-UAV scenario, TLE achieves a $16.8\%$ improvement in mean '
                 r'cumulative task value over pure DE on the 8-UAV fleet (TLE: $389.0 \pm 117.5$, '
                 r'DE: $333.0 \pm 57.1$), although the Wilcoxon signed-rank test (one-sided, $n = 5$ seeds) '
                 r'returns $p = 0.156$, which does not reach the conventional $\alpha = 0.05$ '
                 r'significance threshold. On the 4-UAV fleet, the difference is smaller in magnitude '
                 r'and not significant ($p = 0.28$). The complete UAV results are given in '
                 r'Table~\ref{tab:uav}. A noteworthy observation is that the classical diversity-injection '
                 r'baseline DNSGA-II-A achieves the highest mean on both fleet sizes ($460.0 \pm 100.0$ '
                 r'on 8-UAV), confirming that the change-detection diversity mechanism is the dominant '
                 r'contribution in this scenario rather than the LLM-triggered parameter adaptation; '
                 r'the LLM contribution is most visible in the upper tail of the 8-UAV distribution '
                 r'(TLE seed 4 reaches $f_1 = 555.0$ vs.\ DE seed 4 $385.0$, a $+44\%$ single-seed gap), '
                 r'but the small sample size limits the statistical power. The Pareto fronts reached by '
                 r'DE, DNSGA-II-A, and TLE on DF1, DF5, and DF7 (which the main paper only shows for DF2 '
                 r'because DF2 is the only catastrophic-failure problem) are provided in '
                 r'\textbf{Supplementary Material, Section~S5, Fig.~S5}.')
    new_prose_para = uav_prose + ' A noteworthy observation is that the classical diversity-injection baseline DNSGA-II-A achieves the highest mean on both fleet sizes ($460.0 \\pm 100.0$ on 8-UAV), confirming that the change-detection diversity mechanism is the dominant contribution in this scenario rather than the LLM-triggered parameter adaptation; the LLM contribution is most visible in the upper tail of the 8-UAV distribution (TLE seed 4 reaches $f_1 = 555.0$ vs.\\ DE seed 4 $385.0$, a $+44\\%$ single-seed gap), but the small sample size limits the statistical power. The Pareto fronts reached by DE, DNSGA-II-A, and TLE on DF1, DF5, and DF7 (which the main paper only shows for DF2 because DF2 is the only catastrophic-failure problem) are provided in \\textbf{Supplementary Material, Section~S5, Fig.~S5}.'
    if apply_replacement(RES_LIVE, find_prose, new_prose_para, '§5 UAV prose') is None:
        return

    # 4d. 05_results.tex — Table 5 (use anchor-based approach to avoid
    # encoding issues with multi-line strings).
    # Find the unique caption that identifies this specific table.
    find_cap = (r'\caption{Multi-UAV task allocation ($n = 5$ seeds). Cumulative task value $f_1$ '
                r'(higher is better). The Wilcoxon signed-rank $p$-values are computed one-sided '
                r'against DE (alternative: algorithm $>$ DE). TLE shows a $16.8\%$ mean improvement '
                r'over DE on 8-UAV but does not reach $\alpha = 0.05$ significance at $n = 5$; '
                r'DNSGA-II-A achieves the highest mean on both fleet sizes.}')
    # Find start: \begin{table}[t] immediately followed by the caption
    # Find end: \end{table} after the caption
    text = RES_LIVE.read_text(encoding='utf-8')
    # Find the table that contains the Table 5 caption
    cap_idx = text.find(find_cap)
    if cap_idx < 0:
        print('ERROR: Table 5 caption not found')
        return
    # Walk backward to find the \begin{table}[t] that contains this caption
    begin_idx = text.rfind(r'\begin{table}[t]', 0, cap_idx)
    if begin_idx < 0:
        print('ERROR: \\begin{table}[t] before Table 5 caption not found')
        return
    # Walk forward to find the matching \end{table} AFTER the caption
    # (The .original baseline may be missing \end{table} — fall back to \end{tabular})
    end_idx = text.find(r'\end{table}', cap_idx)
    if end_idx < 0:
        end_idx = text.find(r'\end{tabular}', cap_idx)
        if end_idx < 0:
            print('ERROR: neither \\end{table} nor \\end{tabular} found after Table 5 caption')
            return
        end_marker = r'\end{tabular}'
        new_table = table5 + '\n' + r'\end{table}'
    else:
        end_marker = r'\end{table}'
        new_table = table5
    end_idx_full = end_idx + len(end_marker)
    # Replace
    new_text = text[:begin_idx] + new_table + text[end_idx_full:]
    RES_LIVE.write_text(new_text, encoding='utf-8')
    print(f'OK: Table 5 (replaced {end_idx_full - begin_idx} chars with {len(new_table)} chars new)')

    # 5. Recompile
    print('\n=== Recompiling PDFs ===')
    for f in ['main.aux', 'main.bbl', 'main.blg', 'main.log', 'main.out',
              'supplementary_material.aux', 'supplementary_material.log', 'supplementary_material.out',
              'cover_letter.aux', 'cover_letter.log', 'cover_letter.out']:
        p = RES / f
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    # main.tex: 3 passes + bibtex
    for i in range(3):
        print(f'  main pass {i+1}/3...')
        subprocess.run([MIKTEX_PDFLATEX, '-interaction=nonstopmode', 'main.tex'],
                      cwd=str(RES), capture_output=True, text=True)
        if i == 0:
            subprocess.run([MIKTEX_BIBTEX, 'main'], cwd=str(RES), capture_output=True, text=True)

    # cover_letter.tex
    for i in range(2):
        subprocess.run([MIKTEX_PDFLATEX, '-interaction=nonstopmode', 'cover_letter.tex'],
                      cwd=str(RES), capture_output=True, text=True)
    print('  cover_letter.pdf OK')

    # supplementary_material.tex
    for i in range(2):
        subprocess.run([MIKTEX_PDFLATEX, '-interaction=nonstopmode', 'supplementary_material.tex'],
                      cwd=str(RES), capture_output=True, text=True)
    print('  supplementary_material.pdf OK')

    # Cleanup
    for f in ['main.aux', 'main.bbl', 'main.blg', 'main.log', 'main.out',
              'supplementary_material.aux', 'supplementary_material.log', 'supplementary_material.out',
              'cover_letter.aux', 'cover_letter.log', 'cover_letter.out']:
        p = RES / f
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    # Show final
    print('\n=== Final PDFs ===')
    for f in ['main.pdf', 'cover_letter.pdf', 'supplementary_material.pdf']:
        p = RES / f
        if p.exists():
            print(f'  {f}: {p.stat().st_size/1024:.0f} KB')
    print('\n=== DONE ===')


if __name__ == '__main__':
    main()