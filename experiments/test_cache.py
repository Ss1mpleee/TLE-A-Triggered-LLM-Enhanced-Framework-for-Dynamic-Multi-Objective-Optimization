import sys
sys.path.insert(0, "D:/新论文/实验")
from core.llm_interface import LLMClient, CACHE_DIR
print(f'Cache dir: {CACHE_DIR}')
n_before = len(list(CACHE_DIR.glob('*.json')))
client = LLMClient(model='gemma4:26b', use_cache=True)
r1 = client.call('Tell me a haiku about programming.', max_tokens=80)
print(f'Response 1: {r1[:100]}')
r2 = client.call('Tell me a haiku about programming.', max_tokens=80)
print(f'Response 2: {r2[:100]}')
print(f'Same? {r1 == r2}')
stats = client.get_stats()
print(f'Cache hits: {stats["cache_hits"]} / calls: {stats["total_calls"]}')
