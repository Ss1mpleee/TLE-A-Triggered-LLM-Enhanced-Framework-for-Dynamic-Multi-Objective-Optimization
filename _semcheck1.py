import json
files = {
    'cross_llm_n30': r'results\raw\exp6_cross_llm_n30.json',
    'cross_llm_n14': r'results\raw\exp6_cross_llm_n14.json',
    'ablation_lite': r'results\raw\exp7_ablation_lite.json',
    'ablation_combined': r'results\raw\exp7_ablation_combined.json',
    'uav_v3': r'results\raw\exp3_uav_v3.json',
    'uav_combined': r'results\raw\exp3_uav_combined.json',
    'sec_main_v3': r'results\raw\sec_main_v3.json',
    'sec_main_df46': r'results\raw\sec_main_df46.json',
    'pareto_fronts': r'results\raw\exp_pareto_fronts.json',
    'moeadd': r'results\raw\exp4_moeadd.json',
    'trigger_thresh': r'results\raw\exp_trigger_threshold.json',
    'sec_ablation_v2': r'results\raw\sec_ablation_v2.json',
}
for k, f in files.items():
    try:
        with open(f, encoding='utf-8') as fp:
            d = json.load(fp)
        if isinstance(d, dict):
            print(f'{k}: dict, keys={list(d.keys())[:8]}, size={len(d)}')
        elif isinstance(d, list):
            print(f'{k}: list, len={len(d)}; first={str(d[0])[:300]}')
    except Exception as e:
        print(f'{k}: ERROR {e}')
