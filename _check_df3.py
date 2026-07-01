import json
d = json.load(open(r'D:\新论文\实验\results\raw\df3_fix.json', encoding='utf-8'))
print(f'DF3 fix: {len(d)} runs')
for r in d:
    print(f"  {r['algo']:22s} seed={r['seed']} IGD={r['igd']:.4f} HV={r['hv']:.4f}")
