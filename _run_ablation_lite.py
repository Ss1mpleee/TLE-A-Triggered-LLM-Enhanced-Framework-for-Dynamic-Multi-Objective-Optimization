"""Trigger ablation: 4 versions on 14 problems x n=15 seeds.

Versions:
  V0_baseline  = always-invoke trigger (capped at 50 calls)
  V1_single    = single-signal trigger (entropy only)
  V2_double    = double-signal trigger (entropy + stagnation, no change)
  V3_triple    = TLE production (entropy + stagnation + change)  -- reuses n=30 main run

For V3, we load results/raw/sec_main_v3.json (algo=TLE, seeds 0..14) directly.
For V0/V1/V2, fresh runs are added to results/raw/exp7_ablation_lite.json.

The script is resumable: existing (problem, seed, version) keys are skipped.
"""
import json
import time
import sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from core import LLMClient, TLE, DEFAULT_MODEL
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort

OUT_NEW = REPO / "results" / "raw" / "exp7_ablation_lite.json"
OUT_FINAL = REPO / "results" / "raw" / "exp7_ablation_combined.json"
MAIN = REPO / "results" / "raw" / "sec_main_v3.json"
MODEL = "qwen2.5:7b"

PROBLEMS = ["DF1","DF2","DF3","DF4","DF5","DF6","DF7","DF8",
            "DF9","DF10","DF11","DF12","DF13","DF14"]
SEEDS = list(range(30))  # 0..29, n=30 (per user requirement: full n=30)

# V0: always-invoke with budget cap = 50 (every 4th gen, mirrors DE-LM-always)
V0_TRIGGER = "always"
V0_CAP = 50
# V1/V2/V3: trigger-based, scheduler=bandit
VERSIONS = [
    ("V0_baseline", V0_TRIGGER, "fixed", V0_CAP),
    ("V1_single",   "single",   "bandit", None),
    ("V2_double",   "double",   "bandit", None),
    ("V3_triple",   "triple",   "bandit", None),
]


def main():
    OUT_NEW.parent.mkdir(parents=True, exist_ok=True)

    # 1) Load existing fresh runs (resumable)
    fresh = []
    done_keys = set()
    if OUT_NEW.exists():
        try:
            with open(OUT_NEW) as f:
                fresh = json.load(f)
            for r in fresh:
                if "error" not in r and "version" in r:
                    done_keys.add((r["version"], r["problem"], r["seed"]))
            print(f"[Resume] {len(fresh)} fresh runs loaded, {len(done_keys)} keys will be skipped")
        except Exception as e:
            print(f"[Resume] Could not load: {e}")

    # 2) V3 from main run
    v3_loaded = 0
    if MAIN.exists():
        with open(MAIN) as f:
            main_data = json.load(f)
        for r in main_data:
            if r.get("algo") != "TLE": continue
            if r.get("problem") not in PROBLEMS: continue
            if r.get("seed") not in SEEDS: continue
            if "error" in r: continue
            v3_loaded += 1
    print(f"[V3] {v3_loaded} runs loaded from main n=30 experiment")

    # 3) Iterate V0/V1/V2
    t_start = time.time()
    to_run = [v for v in VERSIONS if v[0] != "V3_triple"]
    total = len(to_run) * len(PROBLEMS) * len(SEEDS)
    done_idx = 0
    skipped = 0

    for vname, trigger, sched, budget in to_run:
        for prob in PROBLEMS:
            for seed in SEEDS:
                done_idx += 1
                key = (vname, prob, seed)
                if key in done_keys:
                    skipped += 1
                    if done_idx % 20 == 0:
                        eta = (time.time() - t_start) / (done_idx - skipped + 1e-9) * (total - done_idx + skipped)
                        print(f"[{done_idx:4d}/{total}] SKIP {vname} {prob} seed={seed} (skipped={skipped}, ETA {eta/60:.1f}m)")
                    continue
                try:
                    np.random.seed(seed)
                    problem = DMOProblem(name=prob, d=10, nt=10, taut=10)
                    ref_pf = get_reference_pf(prob, n=100)
                    bounds = (problem.lower, problem.upper)

                    def evaluate(pop):
                        return problem.evaluate(pop)

                    llm = LLMClient(model=MODEL, max_tokens=500, use_cache=True)
                    llm.reset_stats()

                    kwargs = dict(
                        d=10, bounds=bounds, n_obj=problem.M,
                        pop_size=50, max_gen=200, llm=llm,
                        trigger=trigger, scheduler=sched, seed=seed,
                    )
                    if budget is not None:
                        # Use the same FixedBudgetScheduler path as DE-LM-always
                        from core.bandit import FixedBudgetScheduler
                        algo = TLE(**kwargs)
                        algo.scheduler = FixedBudgetScheduler(budget, 200)
                    else:
                        algo = TLE(**kwargs)
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
                    # Trigger fire rate
                    trig_stats = info.get('trigger_stats', {}) or {}
                    rate = trig_stats.get('invocation_rate', None)
                    fresh.append({
                        'version': vname, 'trigger': trigger, 'scheduler': sched,
                        'problem': prob, 'seed': seed,
                        'igd': igd, 'invocations': inv,
                        'cache_hits': cache_hits,
                        'elapsed_sec': elapsed,
                        'fire_rate': rate,
                    })
                    done_keys.add(key)
                    elapsed_total = time.time() - t_start
                    eta = elapsed_total / (done_idx - skipped + 1e-9) * (total - done_idx + skipped)
                    print(f"[{done_idx:4d}/{total}] {vname:12s} {prob:5s} seed={seed:2d} "
                          f"IGD={igd:.4f} inv={inv:3d} cache={cache_hits:3d} "
                          f"t={elapsed:5.1f}s (total {elapsed_total/60:5.1f}m, ETA {eta/60:5.1f}m)",
                          flush=True)
                    if len(fresh) % 5 == 0:
                        with open(OUT_NEW, 'w', encoding='utf-8') as f:
                            json.dump(fresh, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"  -> ERROR {vname} {prob} seed={seed}: {e}", flush=True)
                    fresh.append({
                        'version': vname, 'problem': prob, 'seed': seed, 'error': str(e)
                    })

    # 4) Save fresh
    with open(OUT_NEW, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, ensure_ascii=False, indent=2)

    # 5) Combine: V3 (from main) + V0/V1/V2 (fresh)
    combined = []
    if MAIN.exists():
        with open(MAIN) as f:
            main_data = json.load(f)
        for r in main_data:
            if r.get("algo") != "TLE": continue
            if r.get("problem") not in PROBLEMS: continue
            if r.get("seed") not in SEEDS: continue
            if "error" in r: continue
            combined.append({
                'version': 'V3_triple', 'trigger': 'triple', 'scheduler': 'bandit',
                'problem': r['problem'], 'seed': r['seed'],
                'igd': r['igd'], 'invocations': r.get('invocations', 0),
                'cache_hits': 0,
                'elapsed_sec': r.get('elapsed_sec', 0),
                'fire_rate': None,  # not available
            })
    combined.extend([r for r in fresh if 'error' not in r])
    with open(OUT_FINAL, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"\n[Final] Combined {len(combined)} runs saved to {OUT_FINAL}")
    print(f"[Done] Total time: {(time.time() - t_start)/60:.1f} min")


if __name__ == '__main__':
    main()
