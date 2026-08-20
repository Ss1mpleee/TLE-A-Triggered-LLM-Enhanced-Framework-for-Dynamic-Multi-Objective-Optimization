"""Cross-LLM on full 14 problems x n=10 seeds.

Reuses existing n=30 main for Qwen-2.5-7B on DF1/5/7 (already have 30 seeds there).
Runs Qwen-3.5-9B and OmniCoder-9B on all 14 problems at n=10.
Also runs Qwen-2.5-7B on the 11 problems NOT in original 3-problem study (n=10).

Total: 3 LLMs x 14 problems x 10 seeds = 420 runs
Already have: Qwen-2.5-7B on DF1/5/7 at n=30 (use first 10 seeds)
New: Qwen-2.5-7B on DF2/3/4/6/8/9/10/11/12/13/14 at n=10 = 110 runs
      Qwen-3.5-9B on all 14 at n=10 = 140 runs
      OmniCoder-9B on all 14 at n=10 = 140 runs
Total new: 390 runs
"""
import json
import time
import sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from core import LLMClient, TLE
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort

OUT = REPO / "results" / "raw" / "exp6_cross_llm_n14.json"
EXISTING_N30 = REPO / "results" / "raw" / "exp6_cross_llm_n30.json"

MODELS = [
    "qwen2.5:7b",
    "qwen3.5:9b",
    "carstenuhlig/omnicoder-9b:q8_0",
]
PROBS_2OBJ = ["DF1","DF2","DF3","DF4","DF5","DF6","DF7","DF8"]
PROBS_3OBJ = ["DF9","DF10","DF11","DF12","DF13","DF14"]
ALL_PROBS = PROBS_2OBJ + PROBS_3OBJ
ORIG_3 = {"DF1","DF5","DF7"}  # originally tested problems
SEEDS = list(range(30))  # n=30 (per user requirement: full n=30)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    results = []
    done_keys = set()

    # 1) Load existing results
    if OUT.exists():
        try:
            with open(OUT) as f:
                results = json.load(f)
            for r in results:
                if "error" not in r and "model" in r:
                    done_keys.add((r["model"], r["prob"], r["seed"]))
            print(f"[Resume] {len(results)} existing runs, {len(done_keys)} keys skipped")
        except Exception as e:
            print(f"[Resume] Could not load: {e}")

    # 2) For Qwen-2.5-7B on DF1/5/7, import from n=30 file
    if EXISTING_N30.exists():
        with open(EXISTING_N30) as f:
            n30 = json.load(f)
        imported = 0
        for r in n30:
            if r.get("model") != "qwen2.5:7b": continue
            if r.get("prob") not in ORIG_3: continue
            if r.get("seed") not in SEEDS: continue
            if "error" in r: continue
            key = (r["model"], r["prob"], r["seed"])
            if key in done_keys: continue
            results.append({
                "model": r["model"], "prob": r["prob"], "seed": r["seed"],
                "igd": r["igd"], "invocations": r.get("invocations", 0),
                "elapsed_sec": r.get("elapsed_sec", 0),
                "cache_hits": r.get("cache_hits", 0),
                "source": "imported_n30",
            })
            done_keys.add(key)
            imported += 1
        print(f"[Import] {imported} Qwen-2.5-7B on DF1/5/7 imported from n=30")

    # 3) Run fresh for remaining
    t_start = time.time()
    total_new = 0
    for model in MODELS:
        for prob in ALL_PROBS:
            # Skip if Qwen-2.5-7B on DF1/5/7 already imported
            if model == "qwen2.5:7b" and prob in ORIG_3:
                continue
            for seed in SEEDS:
                total_new += 1
                key = (model, prob, seed)
                if key in done_keys:
                    continue
                try:
                    np.random.seed(seed)
                    problem = DMOProblem(name=prob, d=10, nt=10, taut=10)
                    ref_pf = get_reference_pf(prob, n=100)
                    bounds = (problem.lower, problem.upper)

                    def evaluate(pop):
                        return problem.evaluate(pop)

                    llm = LLMClient(model=model, max_tokens=500, use_cache=True)
                    llm.reset_stats()
                    algo = TLE(d=10, bounds=bounds, n_obj=problem.M,
                               pop_size=50, max_gen=200, llm=llm,
                               trigger='triple', scheduler='bandit', seed=seed)
                    t0 = time.time()
                    pop, fit, info = algo.optimize(evaluate, problem=problem)
                    elapsed = time.time() - t0
                    fronts = fast_non_dominated_sort(fit)
                    nd = fit[fronts[0]] if fronts else fit
                    try:
                        igd = float(compute_igd(nd, ref_pf))
                    except Exception:
                        igd = float('inf')
                    inv = info.get('invocations', 0)
                    cache_hits = llm.cache_hits
                    results.append({
                        "model": model, "prob": prob, "seed": seed,
                        "igd": igd, "invocations": inv, "elapsed_sec": elapsed,
                        "cache_hits": cache_hits,
                        "source": "fresh",
                    })
                    done_keys.add(key)
                    elapsed_total = time.time() - t_start
                    n_done = sum(1 for r in results if "error" not in r) - 30  # subtract imports
                    eta = elapsed_total / max(1, n_done) * max(1, total_new - n_done)
                    print(f"[{n_done:3d}/{total_new}] {model:34s} {prob:5s} seed={seed:2d} "
                          f"IGD={igd:.4f} inv={inv:3d} cache={cache_hits:3d} "
                          f"t={elapsed:5.1f}s (total {elapsed_total/60:5.1f}m, ETA {eta/60:5.1f}m)",
                          flush=True)
                    if n_done % 5 == 0:
                        with open(OUT, 'w', encoding='utf-8') as f:
                            json.dump(results, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"  -> ERROR {model} {prob} seed={seed}: {e}", flush=True)
                    results.append({"model": model, "prob": prob, "seed": seed, "error": str(e)})

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[Done] {len(results)} total runs, {(time.time()-t_start)/60:.1f} min")
    print(f"Saved to {OUT}")


if __name__ == '__main__':
    main()
