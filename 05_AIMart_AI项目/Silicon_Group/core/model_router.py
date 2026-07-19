import os
import time
import random

MODEL_TIER = {
    "high": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY_HIGH") or os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_API_BASE_HIGH") or "https://api.deepseek.com/v1",
        "model": os.getenv("OPENAI_MODEL_HIGH") or "deepseek-chat",
    },
    "medium": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_API_BASE") or "https://api.deepseek.com/v1",
        "model": os.getenv("OPENAI_MODEL_NAME") or "deepseek-chat",
    },
    "low": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY_LOW") or os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_API_BASE_LOW") or "https://api.deepseek.com/v1",
        "model": os.getenv("OPENAI_MODEL_LOW") or "deepseek-chat",
    },
}

FALLBACK_TIER = {
    "high": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY_HIGH") or os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_API_BASE_HIGH") or "https://api.deepseek.com/v1",
        "model": os.getenv("OPENAI_MODEL_HIGH_FALLBACK") or "deepseek-chat",
    },
    "medium": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_API_BASE") or "https://api.deepseek.com/v1",
        "model": os.getenv("OPENAI_MODEL_NAME_FALLBACK") or "deepseek-chat",
    },
    "low": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY_LOW") or os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_API_BASE_LOW") or "https://api.deepseek.com/v1",
        "model": os.getenv("OPENAI_MODEL_LOW") or "deepseek-chat",
    },
}

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2


def _build_config(config: dict, attempt: int, fallback: bool = False) -> dict:
    result = {
        "model": config["model"],
        "api_key": config["api_key"],
        "base_url": config["base_url"],
        "attempt": attempt,
    }
    if fallback:
        result["fallback"] = True
    return result


def get_llm_config(tier: str = "medium", attempt: int = 0) -> dict:
    config = MODEL_TIER.get(tier, MODEL_TIER["medium"])
    return _build_config(config, attempt)


def get_fallback_config(tier: str = "medium", attempt: int = 0) -> dict:
    config = FALLBACK_TIER.get(tier, FALLBACK_TIER["medium"])
    return _build_config(config, attempt, fallback=True)


def get_retry_delay(attempt: int) -> float:
    delay = RETRY_DELAY_BASE * (2 ** attempt) + random.uniform(0, 1)
    return min(delay, 15)


def describe_tiers():
    return {
        "high": "高阶决策（CEO/宪兵审计）— 默认 DeepSeek-Reasoner",
        "medium": "常规任务（量化分析/策略）— 默认 DeepSeek-Reasoner",
        "low": "脏活累活（翻译/爬虫/摘要）— 默认 DeepSeek-Chat",
    }
