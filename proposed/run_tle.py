"""
Single-file CLI entry point for the TLE framework.

This is the script you run when you want to invoke TLE on a single problem
without going through the full experiment driver in `experiments/`. The
`experiments/` package contains the multi-seed / multi-algorithm comparison
scripts that produce the paper's tables and figures; this module is a thin
wrapper around the same `core.TLE` class.

Typical use:

    # 8 seeds × 5 problems (reproduces the headline table)
    python -m proposed.run_tle --problem DF1 --n_seeds 8

    # quick smoke test (cache-hits make this ~3 seconds)
    python -m proposed.run_tle --problem DF1 --n_seeds 1 --max_gen 20

    # disable the LLM (degrades to plain DE — useful for ablation)
    python -m proposed.run_tle --problem DF1 --n_seeds 1 --no-llm

The results are written to `results/raw/tle_<problem>_<seeds>s.json` (a
flat schema compatible with the multi-algorithm tables in the paper).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Standard preamble: make this script runnable from any working directory.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

RAW_DIR   = REPO_ROOT / "results" / "raw"
FIG_DIR   = REPO_ROOT / "results" / "figures"
CACHE_DIR = REPO_ROOT / "results" / "llm_cache"

import numpy as np
from core import TLE, LLMClient, DEFAULT_MODEL
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, compute_hv, fast_non_dominated_sort


PROBLEMS_2OBJ = ["DF1", "DF2", "DF3", "DF5", "DF7"]
PROBLEMS_3OBJ = ["DF10"]
ALL_PROBLEMS  = PROBLEMS_2OBJ + PROBLEMS_3OBJ


def run_single(
    problem_name: str,
    seed: int,
    pop_size: int,
    max_gen: int,
    d: int,
    trigger: str,
    scheduler: str,
    use_llm: bool,
    llm_model: str,
) -> dict:
    """Run a single (problem, seed) TLE configuration."""
    np.random.seed(seed)
    problem = DMOProblem(name=problem_name, d=d, nt=10, taut=10)
    ref_pf = get_reference_pf(problem_name, n=100)
    bounds = (problem.lower, problem.upper)

    def evaluate(pop):
        return problem.evaluate(pop)

    llm = LLMClient(model=llm_model, max_tokens=500, use_cache=True) if use_llm else None

    algo = TLE(
        d=d, bounds=bounds, n_obj=problem.M,
        pop_size=pop_size, max_gen=max_gen, llm=llm,
        trigger=trigger, scheduler=scheduler, seed=seed,
    )

    t0 = time.time()
    pop, fit, info = algo.optimize(evaluate, problem=problem)
    elapsed = time.time() - t0

    fronts = fast_non_dominated_sort(fit)
    nd_fit = fit[fronts[0]] if fronts else fit

    ref_point = np.array([1.1, 1.1]) if problem.M == 2 else np.array([1.1] * problem.M)
    try:
        igd = float(compute_igd(nd_fit, ref_pf))
    except Exception:
        igd = float("inf")
    try:
        hv = float(compute_hv(nd_fit, ref_point))
    except Exception:
        hv = 0.0

    return {
        "algo": "TLE",
        "problem": problem_name,
        "seed": seed,
        "pop_size": pop_size,
        "max_gen": max_gen,
        "igd": igd,
        "hv": hv,
        "elapsed_sec": elapsed,
        "invocations": info.get("invocations", 0),
        "trigger_stats": info.get("trigger_stats"),
        "scheduler_stats": info.get("scheduler_stats"),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Run the TLE framework on a single dynamic multi-objective problem.",
    )
    p.add_argument("--problem", choices=ALL_PROBLEMS, default="DF1",
                   help="DMO benchmark problem (default: DF1)")
    p.add_argument("--n-seeds", type=int, default=8,
                   help="Number of random seeds (default: 8)")
    p.add_argument("--seeds", nargs="+", type=int, default=None,
                   help="Explicit seed list (overrides --n-seeds)")
    p.add_argument("--pop-size", type=int, default=50)
    p.add_argument("--max-gen", type=int, default=200)
    p.add_argument("--d", type=int, default=10, help="Number of decision variables")
    p.add_argument("--trigger", choices=["triple", "single", "always", "never"],
                   default="triple")
    p.add_argument("--scheduler", choices=["bandit", "heuristic", "fixed"],
                   default="bandit")
    p.add_argument("--llm", "--model", dest="llm_model", default=DEFAULT_MODEL,
                   help=f"Ollama model name (default: {DEFAULT_MODEL})")
    p.add_argument("--no-llm", action="store_true",
                   help="Disable the LLM entirely (TLE degrades to DE)")
    p.add_argument("--output", type=str, default=None,
                   help="Output JSON path (default: results/raw/tle_<problem>_<n>s.json)")
    args = p.parse_args(argv)

    if args.seeds is not None:
        seeds = args.seeds
    else:
        seeds = list(range(args.n_seeds))

    use_llm = not args.no_llm

    if args.output is None:
        out_name = f"tle_{args.problem}_{len(seeds)}s.json"
        out_path = RAW_DIR / out_name
    else:
        out_path = Path(args.output)

    print(f"=== TLE single-problem runner ===")
    print(f"Problem      : {args.problem}")
    print(f"Seeds        : {seeds}")
    print(f"Pop / T      : {args.pop_size} / {args.max_gen}")
    print(f"Trigger      : {args.trigger}")
    print(f"Scheduler    : {args.scheduler}")
    print(f"LLM          : {args.llm_model if use_llm else 'disabled (degrades to DE)'}")
    print(f"Output       : {out_path}")
    print(f"Started      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results: list[dict] = []
    for i, seed in enumerate(seeds, 1):
        try:
            r = run_single(
                problem_name=args.problem,
                seed=seed,
                pop_size=args.pop_size,
                max_gen=args.max_gen,
                d=args.d,
                trigger=args.trigger,
                scheduler=args.scheduler,
                use_llm=use_llm,
                llm_model=args.llm_model,
            )
            results.append(r)
            print(f"[{i}/{len(seeds)}] seed={seed}  IGD={r['igd']:.4f}  "
                f"HV={r['hv']:.4f}  inv={r['invocations']:3d}  "
                f"t={r['elapsed_sec']:.1f}s")
        except Exception as e:
            print(f"[{i}/{len(seeds)}] seed={seed}  ERROR: {e}")
            results.append({
                "algo": "TLE", "problem": args.problem, "seed": seed,
                "error": str(e),
            })

        # Save intermediate.
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    # Summary.
    ok = [r for r in results if "error" not in r]
    if ok:
        igds = [r["igd"] for r in ok if np.isfinite(r["igd"])]
        hvs  = [r["hv"]  for r in ok]
        invs = [r["invocations"] for r in ok]
        print()
        print(f"=== Summary ({len(ok)}/{len(results)} successful) ===")
        if igds:
            print(f"IGD  : mean={np.mean(igds):.4f}  std={np.std(igds):.4f}  "
                f"min={min(igds):.4f}  max={max(igds):.4f}")
        print(f"HV   : mean={np.mean(hvs):.4f}  std={np.std(hvs):.4f}")
        print(f"Inv  : mean={np.mean(invs):.1f}  "
            f"(range {min(invs)}-{max(invs)} = "
            f"{min(invs)/args.max_gen*100:.1f}-{max(invs)/args.max_gen*100:.1f}% of T)")
    print(f"\nWrote {len(results)} runs to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
