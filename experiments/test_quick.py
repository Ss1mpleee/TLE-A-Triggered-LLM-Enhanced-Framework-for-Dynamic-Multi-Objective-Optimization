"""
Quick test: verify LLM interface and basic TLE flow work.
"""
import sys
sys.path.insert(0, "D:/新论文/实验")

import numpy as np
from core import LLMClient, TLE, DEBaseline
from benchmarks import DMOProblem, get_reference_pf


def test_llm_connection():
    """Test that Ollama is reachable and LLM responds."""
    print("=" * 60)
    print("Test 1: LLM Connection")
    print("=" * 60)
    client = LLMClient(model="gemma4:26b", max_tokens=200)
    response = client.call(
        "Respond with one word: the capital of France?",
        temperature=0.0
    )
    print(f"Response: {response[:100]}")
    print(f"Stats: {client.get_stats()}")
    return client


def test_cec2018():
    """Test TLE on a simple CEC2018 dynamic problem."""
    print("\n" + "=" * 60)
    print("Test 2: TLE on CEC2018 DF1")
    print("=" * 60)

    # Setup
    problem = DMOProblem(name="DF1", d=10, nt=10, taut=10)
    ref_pf = get_reference_pf("DF1", n=100)

    def evaluate(pop):
        return problem.evaluate(pop)

    # Run TLE
    tle = TLE(
        d=10,
        bounds=(problem.lower, problem.upper),
        n_obj=2,
        pop_size=50,
        max_gen=30,  # very short for test
        llm=None,  # disable LLM first
        trigger="never",
        seed=42,
    )
    pop, fit, info = tle.optimize(evaluate, problem=problem)
    print(f"TLE result: pop shape={pop.shape}, fit shape={fit.shape}")
    print(f"Best fitness: {info['best_fitness_history'][-1]:.4f}")
    print(f"Invocations: {info['invocations']}")


def test_cec2018_with_llm():
    """Test TLE with LLM on a small case."""
    print("\n" + "=" * 60)
    print("Test 3: TLE + LLM on CEC2018 DF1 (small)")
    print("=" * 60)

    problem = DMOProblem(name="DF1", d=10, nt=10, taut=10)

    def evaluate(pop):
        return problem.evaluate(pop)

    llm = LLMClient(model="gemma4:26b", max_tokens=200, use_cache=True)

    tle = TLE(
        d=10,
        bounds=(problem.lower, problem.upper),
        n_obj=2,
        pop_size=30,
        max_gen=20,
        llm=llm,
        trigger="triple",
        scheduler="bandit",
        seed=42,
    )
    pop, fit, info = tle.optimize(evaluate, problem=problem)
    print(f"TLE+LLM result: pop shape={pop.shape}")
    print(f"Invocations: {info['invocations']}")
    print(f"LLM stats: {info.get('llm_stats', 'N/A')}")
    print(f"Trigger stats: {info['trigger_stats']}")
    print(f"Last 5 fitness values: {info['best_fitness_history'][-5:]}")


if __name__ == "__main__":
    test_llm_connection()
    test_cec2018()
    test_cec2018_with_llm()
    print("\n✓ All tests passed!")
