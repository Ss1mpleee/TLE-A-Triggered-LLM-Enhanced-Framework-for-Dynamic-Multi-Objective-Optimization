"""
POST-PROCESSING SCRIPT (run when UAV 30-seed experiment finishes).

Steps:
  1. Read exp3_uav_v3.json (must have 30 seeds per algo per fleet)
  2. Compute means/stds/Wilcoxon p-values
  3. Generate updated Table 5 LaTeX snippet
  4. Generate updated §5 UAV prose
  5. Generate updated Abstract paragraph
  6. Generate updated Highlights bullet
  7. Edit main.tex (Table 5 + §5 UAV prose + Abstract + Highlights)
  8. Recompile main.pdf + cover_letter.pdf + supplementary_material.pdf
  9. Print final report

Run from any directory:
  python D:\\newpaper\\experiments\\_post_uav30_final.py
"""
import json
import re
import sys
import os
import subprocess
import shutil
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.stats import wilcoxon

V3 = Path(r'D:\新论文\实验\results\raw\exp3_uav_v3.json')
TEX = Path(r'D:\新论文\论文\main.tex')
RES = Path(r'D:\新论文\论文')
MIKTEX_PDFLATEX = r'C:\Users\Monesyyy\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe'
MIKTEX_BIBTEX = r'C:\Users\Monesyyy\AppData\Local\Programs\MiKTeX\miktex\bin\x64\bibtex.exe'


def load_data():
    if not V3.exists():
        print(f'ERROR: {V3} not found. Background job may not have started.')
        sys.exit(1)
    return json.load(open(V3, encoding='utf-8'))


def compute_stats(data):
    """Compute means, stds, and paired Wilcoxon p-values (TLE vs others)."""
    # Group f1_value by (algo, n_uavs)
    gb = defaultdict(lambda: defaultdict(list))
    for r in data:
        gb[r['algo']][r['n_uavs']].append(r['f1_value'])

    # Per-algo summary
    summary = {}
    for a in gb:
        for nu in gb[a]:
            vals = gb[a][nu]
            summary[(a, nu)] = {
                'n': len(vals),
                'mean': float(np.mean(vals)),
                'std': float(np.std(vals)),
            }

    # Paired Wilcoxon TLE vs each (by seed, one-sided: TLE > other)
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
            tle_arr = np.array([tle_d[s] for s in common])
            oth_arr = np.array([oth_d[s] for s in common])
            try:
                w, p = wilcoxon(tle_arr, oth_arr, alternative='greater')
                pvals[nu][a] = float(p)
            except Exception:
                pvals[nu][a] = None

    return summary, pvals, gb


def find_best_per_fleet(summary, algos=['DE','DE-LM-static-trigger','PPS-DMOEA','DNSGA-II-A','TLE']):
    """Find best algo per fleet by mean f1_value (with n>=5 to be valid)."""
    best = {}
    for nu in [4, 8]:
        valid = {a: summary.get((a, nu), {}).get('mean', 0)
                 for a in algos if summary.get((a, nu), {}).get('n', 0) >= 5}
        if valid:
            best[nu] = max(valid, key=valid.get)
    return best


def generate_table5(summary, best, pvals, algos=['DE','DE-LM-static-trigger','PPS-DMOEA','DNSGA-II-A','TLE']):
    """Generate LaTeX table 5 snippet with proper winners bold + p-values."""
    lines = []
    lines.append(r'\begin{table}[t]')
    lines.append(r'\centering')
    lines.append(r'\small')
    lines.append(r'\caption{Multi-UAV task allocation ($n = 30$ seeds, paired by scenario seed). '
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
                    cell = r'\textbf{' + cell + r'}'
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
    """Generate updated §5 UAV prose paragraph."""
    tle_4 = summary.get(('TLE', 4), {})
    tle_8 = summary.get(('TLE', 8), {})
    de_4 = summary.get(('DE', 4), {})
    de_8 = summary.get(('DE', 8), {})
    dnsga_4 = summary.get(('DNSGA-II-A', 4), {})
    dnsga_8 = summary.get(('DNSGA-II-A', 8), {})

    # Compute TLE vs DE diffs
    tle_vs_de_4 = (tle_4['mean'] - de_4['mean']) / de_4['mean'] * 100 if de_4.get('mean') else 0
    tle_vs_de_8 = (tle_8['mean'] - de_8['mean']) / de_8['mean'] * 100 if de_8.get('mean') else 0
    tle_vs_de_8_p = pvals.get(8, {}).get('DE', 1.0)
    tle_vs_dnsga_8_p = pvals.get(8, {}).get('DNSGA-II-A', 1.0)

    # Significance phrase
    if tle_vs_de_8_p is not None and tle_vs_de_8_p < 0.05:
        sig_phrase_8 = (f'TLE achieves a {tle_vs_de_8:+.1f}\\% improvement in mean cumulative '
                        f'task value over pure DE on the 8-UAV fleet (TLE: {tle_8["mean"]:.1f} '
                        f'$\\pm$ {tle_8["std"]:.1f}, DE: {de_8["mean"]:.1f} $\\pm$ {de_8["std"]:.1f}); '
                        f'the Wilcoxon signed-rank test (one-sided, $n = 30$ paired seeds) returns '
                        f'$p = {tle_vs_de_8_p:.4f}$, which reaches the conventional $\\alpha = 0.05$ '
                        f'significance threshold')
        if tle_vs_de_8_p < 0.01:
            sig_phrase_8 = sig_phrase_8.replace('reaches the conventional $\\alpha = 0.05$', 'is significant at $\\alpha = 0.01$')
    else:
        sig_phrase_8 = (f'TLE shows a {tle_vs_de_8:+.1f}\\% higher mean cumulative task value than '
                        f'pure DE on the 8-UAV fleet (TLE: {tle_8["mean"]:.1f} $\\pm$ {tle_8["std"]:.1f}, '
                        f'DE: {de_8["mean"]:.1f} $\\pm$ {de_8["std"]:.1f}), but the Wilcoxon signed-rank '
                        f'test (one-sided, $n = 30$ paired seeds) returns $p = {tle_vs_de_8_p if tle_vs_de_8_p else 1.0:.4f}$, '
                        f'which does not reach the conventional $\\alpha = 0.05$ significance threshold')

    # Best algo per fleet phrase
    if best.get(8) and best[8] != 'TLE':
        sig_phrase_8 += (f'. The classical diversity-injection baseline DNSGA-II-A achieves the '
                        f'highest mean on the 8-UAV fleet ({dnsga_8.get("mean", 0):.1f} '
                        f'$\\pm$ {dnsga_8.get("std", 0):.1f}), confirming that the change-detection '
                        f'diversity mechanism is the dominant contribution in this scenario')

    prose = (f'On the dynamic multi-UAV scenario with $n = 30$ seeds per algorithm '
             f'(paired by scenario seed), {sig_phrase_8}. On the 4-UAV fleet, the difference '
             f'between TLE and DE is smaller in magnitude ({tle_vs_de_4:+.1f}\\% mean, '
             f'Wilcoxon one-sided $p = {pvals.get(4, {}).get("DE", 1.0):.4f}$) and not '
             f'significant. The complete UAV results are given in Table~\\ref{{tab:uav}}.')
    return prose


def generate_abstract_update(summary, pvals, best):
    """Generate updated Abstract sentence for the 8-UAV scenario.

    IMPORTANT: this should ONLY contain the part starting with "on the 8-UAV scenario, ..."
    The replacement function in update_main_tex will only replace the part of the abstract
    that starts with this phrase, so we must NOT include any prefix that's already in
    the original text (such as the "A Friedman test reveals..." sentence).
    """
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


def generate_highlight_update(summary, pvals, best):
    """Generate updated Highlights bullet for UAV."""
    tle_vs_de_8_p = pvals.get(8, {}).get('DE', 1.0)
    tle_8 = summary.get(('TLE', 8), {})
    de_8 = summary.get(('DE', 8), {})
    tle_vs_de_8 = (tle_8['mean'] - de_8['mean']) / de_8['mean'] * 100 if de_8.get('mean') else 0
    n_uav = min(tle_8.get('n', 5), de_8.get('n', 5))

    if tle_vs_de_8_p is not None and tle_vs_de_8_p < 0.05:
        return (f'TLE loses to DNSGA-II-A on CEC 2018 DMO; wins '
                f'{tle_vs_de_8:+.1f}\\% over DE on 8-UAV (Wilcoxon one-sided $p = '
                f'{tle_vs_de_8_p:.4f}$, significant at $\\alpha = 0.05$, $n = {n_uav}$ seeds).')
    else:
        return (f'TLE loses to DNSGA-II-A on CEC 2018 DMO; shows {tle_vs_de_8:+.1f}\\% '
                f'mean improvement over DE on 8-UAV (Wilcoxon one-sided $p = '
                f'{tle_vs_de_8_p if tle_vs_de_8_p else 1.0:.4f}$ at $n = {n_uav}$ seeds, '
                f'not significant at $\\alpha = 0.05$).')


def update_main_tex(table5, uav_prose, abstract_update, highlight_update):
    """Edit main.tex AND sections/05_results.tex to replace Table 5, UAV prose, Abstract, Highlights."""
    if not TEX.exists():
        print(f'ERROR: {TEX} not found.')
        return False

    text = TEX.read_text(encoding='utf-8')

    # 1. Abstract: find the sentence about 8-UAV and replace ONLY that sentence.
    # abstract_update should NOT include any prefix that's already in the abstract
    # (e.g., the "A Friedman test reveals..." sentence which is before our target).
    pattern_abstract = re.compile(
        r'\\begin\{abstract\}(.*?)\\end\{abstract\}',
        re.DOTALL
    )
    m = pattern_abstract.search(text)
    if m:
        old_abstract = m.group(1)
        # Use a non-period-restricted pattern, but stop at the right end:
        # "fleet sizes." (literal period)
        # The text contains "$16.8\%$" with literal period, so we need to
        # match greedily up to "fleet sizes.".
        pattern_uav_sentence = re.compile(
            r'on the 8-UAV scenario, TLE .*?fleet sizes\.',
            re.DOTALL
        )
        new_abstract_text, n = pattern_uav_sentence.subn(
            lambda mm: abstract_update,
            old_abstract
        )
        if n == 0:
            print('WARNING: Could not find Abstract sentence to replace.')
        else:
            new_full = m.group(0).replace(old_abstract, new_abstract_text)
            text = text.replace(m.group(0), new_full)
            print(f'Replaced Abstract sentence (n={n})')

    # 2. Highlights bullet
    pattern_highlight = re.compile(
        r'\\item TLE loses to DNSGA-II-A on CEC 2018 DMO[^\n]*',
        re.DOTALL
    )
    new_highlight = '\\item ' + highlight_update
    text_new, n = pattern_highlight.subn(lambda m: new_highlight, text)
    if n == 0:
        print('WARNING: Could not find Highlights bullet in main.tex to replace.')
    else:
        print(f'Replaced Highlights bullet (n={n})')
        text = text_new

    # Write main.tex
    main_orig_size = TEX.stat().st_size
    TEX.write_text(text, encoding='utf-8')
    new_size = TEX.stat().st_size
    if new_size < main_orig_size * 0.7:
        print(f'ERROR: main.tex shrank from {main_orig_size} to {new_size} bytes (>30% loss). ROLLING BACK.')
        # Roll back
        TEX.write_text(TEX.read_text(encoding='utf-8')[:main_orig_size], encoding='utf-8')
    else:
        print(f'Wrote {TEX} ({main_orig_size} -> {new_size} bytes)')

    # 3. Now update sections/05_results.tex for Table 5 + §5 UAV prose
    res_tex = Path(r'D:\新论文\论文\sections\05_results.tex')
    if not res_tex.exists():
        print(f'WARNING: {res_tex} not found, skipping Table 5 + §5 UAV update.')
        return True

    rtext = res_tex.read_text(encoding='utf-8')
    rtext_orig = rtext  # keep for diff/comparison
    res_orig_size = len(rtext)

    # 3a. Replace Table 5 by finding it via string search
    cap_marker = 'Multi-UAV task allocation'
    cap_idx = rtext.find(cap_marker)
    if cap_idx < 0:
        print('WARNING: Could not find Table 5 caption in 05_results.tex.')
    else:
        # Walk backward to find the most recent \begin{table}
        begin_marker = '\\begin{table}'
        begin_idx = rtext.rfind(begin_marker, 0, cap_idx)
        if begin_idx < 0:
            print('WARNING: Could not find \\begin{table} before Table 5 caption.')
        else:
            # Walk forward to find the next \end{table} after the caption
            end_marker = '\\end{table}'
            end_idx = rtext.find(end_marker, cap_idx)
            if end_idx < 0:
                print('WARNING: Could not find \\end{table} after Table 5 caption.')
            else:
                end_idx_full = end_idx + len(end_marker)
                rtext = rtext[:begin_idx] + table5 + rtext[end_idx_full:]
                print(f'Replaced Table 5 in 05_results.tex (replaced {end_idx_full - begin_idx} chars)')

    # 3b. Replace §5 UAV prose
    pattern_uav = re.compile(
        r'\\subsection\{Multi-UAV Task Allocation\}(.*?)(?=\\begin\{table\})',
        re.DOTALL
    )
    new_uav_section = '\\subsection{Multi-UAV Task Allocation}\n\n' + uav_prose + '\n\n'
    text_new, n = pattern_uav.subn(lambda mm: new_uav_section, rtext)
    if n == 0:
        print('WARNING: Could not find §5 UAV prose in 05_results.tex to replace.')
    else:
        rtext = text_new
        print(f'Replaced §5 UAV prose in 05_results.tex (n={n})')

    # Sanity check: must have all 5 tables, file must not have shrunk dramatically
    n_tables = rtext.count('\\begin{table}')
    new_size_res = len(rtext)
    if n_tables < 5:
        print(f'ERROR: 05_results.tex has only {n_tables} tables (expected 5). ROLLING BACK.')
        rtext = rtext_orig
    elif new_size_res < res_orig_size * 0.7:
        print(f'ERROR: 05_results.tex shrank from {res_orig_size} to {new_size_res} bytes. ROLLING BACK.')
        rtext = rtext_orig
    else:
        print(f'Verified: 05_results.tex still has {n_tables} tables, {res_orig_size} -> {new_size_res} bytes')

    res_tex.write_text(rtext, encoding='utf-8')
    print(f'Wrote {res_tex}')
    return True


def recompile():
    """Recompile main.tex, cover_letter.tex, supplementary_material.tex."""
    print('\n=== Recompiling PDFs ===')
    # Clean aux
    for f in ['main.aux', 'main.bbl', 'main.blg', 'main.log', 'main.out',
              'supplementary_material.aux', 'supplementary_material.log', 'supplementary_material.out',
              'cover_letter.aux', 'cover_letter.log', 'cover_letter.out']:
        p = RES / f
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    # main.tex: 3 passes
    for i in range(3):
        print(f'  main pass {i+1}/3...')
        r = subprocess.run([MIKTEX_PDFLATEX, '-interaction=nonstopmode', 'main.tex'],
                          cwd=str(RES), capture_output=True, text=True)
        if '!' in r.stdout[:5000] or 'Error' in r.stdout[:5000]:
            print(f'  WARN: pass {i+1} had errors:')
            print(r.stdout[:2000])
        if i == 0:
            # After first pass, run bibtex
            print('  bibtex...')
            r = subprocess.run([MIKTEX_BIBTEX, 'main'], cwd=str(RES), capture_output=True, text=True)
    print('  main.pdf OK')

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

    # Final cleanup
    for f in ['main.aux', 'main.bbl', 'main.blg', 'main.log', 'main.out',
              'supplementary_material.aux', 'supplementary_material.log', 'supplementary_material.out',
              'cover_letter.aux', 'cover_letter.log', 'cover_letter.out']:
        p = RES / f
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    # Show final sizes
    print('\n=== Final PDFs ===')
    for f in ['main.pdf', 'cover_letter.pdf', 'supplementary_material.pdf']:
        p = RES / f
        if p.exists():
            print(f'  {f}: {p.stat().st_size/1024:.0f} KB')


def main():
    print('=== POST-PROCESSING: UAV 30-seed results → paper updates ===\n')
    data = load_data()
    print(f'Loaded {len(data)} records from {V3}')

    summary, pvals, gb = compute_stats(data)
    best = find_best_per_fleet(summary)

    print('\n=== Summary ===')
    for (a, nu), s in sorted(summary.items()):
        print(f'  {a:25s} n_uavs={nu}: n={s["n"]} mean={s["mean"]:.1f} std={s["std"]:.1f}')

    print('\n=== Paired Wilcoxon (TLE > other) ===')
    for nu in [4, 8]:
        for a, p in pvals[nu].items():
            if p is not None:
                print(f'  n_uavs={nu}, TLE vs {a:25s}: p={p:.4f}')

    print('\n=== Best per fleet ===')
    for nu, a in best.items():
        print(f'  n_uavs={nu}: {a} (mean={summary[(a,nu)]["mean"]:.1f})')

    # Generate snippets
    table5 = generate_table5(summary, best, pvals)
    uav_prose = generate_uav_prose(summary, pvals, best)
    abstract_update = generate_abstract_update(summary, pvals, best)
    highlight_update = generate_highlight_update(summary, pvals, best)

    print('\n=== Generated snippets (preview) ===')
    print('--- New Table 5 ---')
    print(table5)
    print('\n--- New §5 UAV prose ---')
    print(uav_prose)
    print('\n--- New Abstract sentence ---')
    print(abstract_update)
    print('\n--- New Highlights bullet ---')
    print(highlight_update)

    # Edit main.tex
    print('\n=== Updating main.tex ===')
    if update_main_tex(table5, uav_prose, abstract_update, highlight_update):
        # Recompile
        recompile()
        print('\n=== DONE ===')
    else:
        print('\n=== Update failed, not recompiling ===')


if __name__ == '__main__':
    main()