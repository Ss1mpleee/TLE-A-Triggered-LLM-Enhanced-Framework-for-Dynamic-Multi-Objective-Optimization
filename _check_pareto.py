import json
data = json.load(open(r'D:\新论文\实验\results\raw\exp_pareto_fronts.json', encoding='utf-8'))
print('Total runs:', len(data))
print('First item keys:', list(data[0].keys()) if data else 'empty')
print()
print('DF2 data:')
for d in data:
    if d.get('problem') == 'DF2':
        print(f'  seed={d.get("seed")}, algo={d["algo"]}, IGD={d.get("igd", 0):.3f}, n_pts={len(d.get("pareto_front", []))}')

print()
print('All algorithms for seed 0:')
for d in data:
    if d.get('seed') == 0:
        print(f'  algo={d["algo"]}, prob={d["problem"]}, IGD={d.get("igd", 0):.3f}, n_pts={len(d.get("pareto_front", []))}')
