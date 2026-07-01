"""
LLM Interface for Local Ollama Deployment
=========================================
Supports: gemma4:26b, qwen2.5:7b, qwen3.5:9b, omnicoder-9b

Author: Mavis (LLM-EA Research Framework)
Date: 2026-06-26
"""
import requests
import json
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np


# ==================== Configuration ====================
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b"

# Cache directory: relative to current working directory or project root
# Detect: if cwd ends with "实验", use "results/llm_cache"
# Otherwise, use "实验/results/llm_cache"
_cwd = Path.cwd()
if _cwd.name == "实验":
    CACHE_DIR = _cwd / "results" / "llm_cache"
else:
    CACHE_DIR = _cwd / "实验" / "results" / "llm_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class LLMClient:
    """Wrapper for Ollama local LLM with caching and statistics."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = OLLAMA_BASE_URL,
        temperature: float = 0.0,
        max_tokens: int = 512,
        timeout: int = 120,
        use_cache: bool = True,
    ):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.use_cache = use_cache

        # Statistics
        self.total_calls = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.total_latency = 0.0
        self.cache_hits = 0
        self.failed_calls = 0

    def _cache_key(self, prompt: str, system: str = "") -> str:
        """Generate cache key from prompt + system."""
        content = f"MODEL={self.model}|T={self.temperature}|S={system}|P={prompt}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _load_cache(self, key: str) -> Optional[str]:
        """Load from cache if available."""
        if not self.use_cache:
            return None
        cache_file = CACHE_DIR / f"{key}.json"
        if cache_file.exists():
            self.cache_hits += 1
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)["response"]
        return None

    def _save_cache(self, key: str, response: str):
        """Save response to cache (skip empty responses)."""
        if not self.use_cache:
            return
        # Don't cache empty or very short responses (likely failures)
        if not response or len(response.strip()) < 3:
            return
        cache_file = CACHE_DIR / f"{key}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"response": response, "model": self.model,
                       "ts": time.time()}, f, ensure_ascii=False)

    def call(
        self,
        prompt: str,
        system: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        force_json: bool = False,
    ) -> str:
        """
        Call LLM with the given prompt.

        Args:
            prompt: User prompt
            system: System message (optional)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            force_json: Add "Return JSON only" suffix to prompt

        Returns:
            Generated text response
        """
        temp = temperature if temperature is not None else self.temperature
        max_t = max_tokens if max_tokens is not None else self.max_tokens

        if force_json and "json" not in prompt.lower():
            prompt = prompt + "\n\nIMPORTANT: Return ONLY a valid JSON object, no markdown, no explanation."

        # Check cache
        cache_key = self._cache_key(prompt, system)
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached

        # Build request
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": max_t,
            },
        }
        if system:
            payload["system"] = system

        # Call
        start_time = time.time()
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            result = resp.json()
            text = result.get("response", "").strip()
            latency = time.time() - start_time

            # Update statistics
            self.total_calls += 1
            self.total_latency += latency
            self.total_tokens_in += result.get("prompt_eval_count", len(prompt) // 4)
            self.total_tokens_out += result.get("eval_count", len(text) // 4)

            # Cache
            self._save_cache(cache_key, text)
            return text

        except Exception as e:
            self.failed_calls += 1
            print(f"[LLM ERROR] Call {self.total_calls} failed: {e}")
            return ""

    def parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON object from LLM response."""
        # Try direct parse
        try:
            return json.loads(response)
        except Exception:
            pass

        # Try to find JSON block
        import re
        # Match {...} including nested
        for pattern in [r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", r"\{.*\}"]:
            matches = re.findall(pattern, response, re.DOTALL)
            for m in matches:
                try:
                    return json.loads(m)
                except Exception:
                    continue
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Return usage statistics."""
        return {
            "model": self.model,
            "total_calls": self.total_calls,
            "cache_hits": self.cache_hits,
            "failed_calls": self.failed_calls,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "total_latency_sec": self.total_latency,
            "avg_latency_sec": (self.total_latency / self.total_calls
                                if self.total_calls > 0 else 0),
        }

    def reset_stats(self):
        """Reset statistics counters."""
        self.total_calls = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.total_latency = 0.0
        self.cache_hits = 0
        self.failed_calls = 0


# ==================== Convenience: Singleton-style global client ====================
_GLOBAL_CLIENT = None

def get_llm(model: str = DEFAULT_MODEL) -> LLMClient:
    """Get or create a global LLM client."""
    global _GLOBAL_CLIENT
    if _GLOBAL_CLIENT is None or _GLOBAL_CLIENT.model != model:
        _GLOBAL_CLIENT = LLMClient(model=model)
    return _GLOBAL_CLIENT


def quick_test():
    """Quick test that LLM is reachable."""
    client = LLMClient()
    response = client.call("What is 2+2? Answer with one number only.", temperature=0.0)
    print(f"LLM Response: {response}")
    print(f"Stats: {client.get_stats()}")
    return response


if __name__ == "__main__":
    quick_test()
