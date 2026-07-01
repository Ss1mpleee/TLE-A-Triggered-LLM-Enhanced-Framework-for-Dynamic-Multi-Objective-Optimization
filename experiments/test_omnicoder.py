import sys, time
sys.path.insert(0, "D:/新论文/实验")
from core.llm_interface import LLMClient

# Test 2: coding-oriented prompt
print('=== Test 2: code prompt ===')
client = LLMClient(model='carstenuhlig/omnicoder-9b:q8_0', use_cache=False, max_tokens=200)
t = time.time()
r = client.call('def hello():\n    return ', temperature=0.0)
elapsed = time.time() - t
print(f'Response: {repr(r)}')
print(f'Latency: {elapsed:.2f}s')
print(f'Out tokens: {client.get_stats()["total_tokens_out"]}')

# Test 3: simpler JSON-style prompt
print('\n=== Test 3: JSON request ===')
client2 = LLMClient(model='carstenuhlig/omnicoder-9b:q8_0', use_cache=False, max_tokens=200)
t = time.time()
r = client2.call('Output JSON: {"name": "John", "age": 30}', temperature=0.0)
elapsed = time.time() - t
print(f'Response: {repr(r)}')
print(f'Latency: {elapsed:.2f}s')

# Test 4: ask for our actual advice
print('\n=== Test 4: DE advice request ===')
prompt = """Population size: 30, Dimensions: 10, Objectives: 2
  x[0]: mean=0.50, std=0.200, range=[0.10, 0.90]
Top-3 individuals:
  rank 1: f0=0.450, f1=0.380

Output JSON with keys: strategy (exploit/explore/focus), F (0.1-1.0), CR (0.1-1.0), reasoning"""
client3 = LLMClient(model='carstenuhlig/omnicoder-9b:q8_0', use_cache=False, max_tokens=300)
t = time.time()
r = client3.call(prompt, temperature=0.0)
elapsed = time.time() - t
print(f'Response: {repr(r[:300])}')
print(f'Latency: {elapsed:.2f}s')
