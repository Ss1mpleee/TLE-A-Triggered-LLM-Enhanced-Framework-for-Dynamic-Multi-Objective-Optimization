import re

orig = ['wang2026adr-dmoea','huang2026knee-dmo','cao2026effective','zhang2026ga-gnn','shao2026dmo-benchmark','ding2026sparse-bo','zhong2026indicator','xu2026runtime','zhao2026multitask','zhang2025interval','li2025er-dmo','chen2025drl-trajectory','xu2025ensemble-dmo','li2025drl-moead','li2025llm-de-constrained','li2025transformer-dmo','wu2024evolutionary','wu2024ec-era-llm','liu2024llm','liu2024llm-de','tian2024predict-dmo','li2024knee-pareto','cao2024change-detection','azevedo2024dmo-review','liu2024drl-bandit','romera2024funsearch','zhou2024survey','tian2023transfer','wang2023dmo','li2023drl-dmo','azevedo2023dmo','nsga2','deb2007dnsga','zhou2014pps','li2015moead','auer2002ucb','besbes2014stochastic','garivier2011upper','farina2004','friedman1937','demvsar2006','storn1997de','zitzler2003performance','tian2017platemo','cec2018dmo','azevedo2016dmo','helbig2016dmo','li2014adaptive','wang2017drl-moead','sierra2014ucb','liu2017bandit-ea']
print(f'Original count: {len(orig)}')

with open(r'D:\新论文\论文\references.bib', 'r', encoding='utf-8') as f:
    text = f.read()
entries = re.findall(r'@(\w+)\{([^,]+),', text)
current = [e[1] for e in entries]
print(f'Current count: {len(current)}')

deleted = [k for k in orig if k not in current]
print(f'Deleted keys ({len(deleted)}):')
for k in deleted: print(f'  {k}')

added = [k for k in current if k not in orig]
print(f'Added keys ({len(added)}):')
for k in added: print(f'  {k}')