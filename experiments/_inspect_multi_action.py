"""
Inspect what LLM actually returns for multi-action prompts.
"""
import sys
import json
from pathlib import Path

ROOT = Path(r"D:\新论文\实验")
sys.path.insert(0, str(ROOT))

import numpy as np
from core.llm_interface import LLMClient
from core.prompts import (
    SYSTEM_PROMPT_MULTI_ACTION,
    build_population_summary,
    build_change_signal_info,
)


def main():
    # Try multiple models
    for model in ["qwen3.5:9b", "qwen2.5:7b", "gemma4:26b"]:
        print(f"\n========== {model} ==========")
        llm = LLMClient(model=model, temperature=0.0, max_tokens=400)

        # Build a simple mock population
        pop = np.random.uniform(0, 1, (50, 10))
        fit = np.random.uniform(0, 1, (50, 2))
        bounds = (np.zeros(10), np.ones(10))

        pop_summary = build_population_summary(pop, fit, bounds)
        user_prompt = f"""Current generation: 50

{pop_summary}

Choose ONE of the four actions (param / archive_reset / restart_top /
diversity_injection) and provide its parameters.

Output JSON only."""

        response = llm.call(user_prompt, system=SYSTEM_PROMPT_MULTI_ACTION,
                             temperature=0.0, max_tokens=400, force_json=True)
        print(f"RAW RESPONSE:")
        print(response[:500])
        print()
        parsed = llm.parse_json(response)
        print(f"PARSED:")
        print(json.dumps(parsed, indent=2, default=str)[:500])
        print()

        # Try with change signal
        print(f"--- WITH CHANGE SIGNAL ---")
        change_info = build_change_signal_info(0.7, {"signal_3_change": True})
        user_prompt2 = f"""Current generation: 50

{pop_summary}
{change_info}

Choose ONE of the four actions (param / archive_reset / restart_top /
diversity_injection) and provide its parameters.

Output JSON only."""
        response2 = llm.call(user_prompt2, system=SYSTEM_PROMPT_MULTI_ACTION,
                              temperature=0.0, max_tokens=400, force_json=True)
        print(f"RAW RESPONSE 2:")
        print(response2[:500])
        parsed2 = llm.parse_json(response2)
        print(f"PARSED 2:")
        print(json.dumps(parsed2, indent=2, default=str)[:500])


if __name__ == "__main__":
    main()