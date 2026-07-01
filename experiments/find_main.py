import json
from pathlib import Path

for path in [Path('D:/新论文/实验/results/raw/sec_main.json'),
             Path('D:/新论文/实验/实验/results/raw/sec_main.json')]:
    if path.exists():
        print(f'Found: {path}')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f'  Records: {len(data)}')
        if data:
            algo = data[0].get('algo')
            prob = data[0].get('problem')
            seed = data[0].get('seed')
            igd = data[0].get('igd')
            print(f'  Sample: algo={algo} prob={prob} seed={seed} igd={igd}')
    else:
        print(f'NOT FOUND: {path}')
