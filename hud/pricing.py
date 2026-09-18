# -*- coding: utf-8 -*-
"""
Model pricing table and session cost estimator for AGY-HUD.
Prices are in USD per 1,000,000 tokens.
"""

MODEL_PRICING = {
    # Gemini Flash models
    "gemini-3.8-flash": {"input": 0.15, "output": 0.60, "cache": 0.0375},
    "gemini-3.5-flash": {"input": 0.10, "output": 0.40, "cache": 0.025},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30, "cache": 0.01875},
    "flash": {"input": 0.15, "output": 0.60, "cache": 0.0375},

    # Gemini Pro models
    "gemini-3.1-pro": {"input": 1.25, "output": 5.00, "cache": 0.3125},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00, "cache": 0.3125},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00, "cache": 0.3125},
    "pro": {"input": 1.25, "output": 5.00, "cache": 0.3125},

    # Claude models (via third-party / Vertex)
    "claude-3-7-sonnet": {"input": 3.00, "output": 15.00, "cache": 0.30},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00, "cache": 0.30},
    "sonnet": {"input": 3.00, "output": 15.00, "cache": 0.30},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00, "cache": 0.08},
    "haiku": {"input": 0.80, "output": 4.00, "cache": 0.08},
    "claude-3-opus": {"input": 15.00, "output": 75.00, "cache": 1.50},
    "opus": {"input": 15.00, "output": 75.00, "cache": 1.50},

    # Fallback default
    "default": {"input": 0.20, "output": 0.80, "cache": 0.05},
}


def resolve_model_rates(model_name_or_id, custom_pricing=None):
    """Match model identifier to pricing rates."""
    if custom_pricing and isinstance(custom_pricing, dict):
        if model_name_or_id in custom_pricing:
            return custom_pricing[model_name_or_id]

    norm = str(model_name_or_id).lower().replace(" ", "-").replace("_", "-")
    for key, rates in MODEL_PRICING.items():
        if key in norm:
            return rates

    # Fuzzy checks
    if "flash" in norm:
        return MODEL_PRICING["gemini-3.8-flash"]
    if "pro" in norm:
        return MODEL_PRICING["gemini-3.1-pro"]
    if "sonnet" in norm:
        return MODEL_PRICING["sonnet"]
    if "haiku" in norm:
        return MODEL_PRICING["haiku"]
    if "opus" in norm:
        return MODEL_PRICING["opus"]

    return MODEL_PRICING["default"]


def calculate_cost(model_name_or_id, total_input, total_output, cache_read=0, custom_pricing=None):
    """
    Calculate dollar cost based on accumulated tokens and cache discount.
    Formula: (net_input * input_rate + output * output_rate + cache * cache_rate) / 1,000,000
    """
    try:
        total_input = float(total_input or 0)
        total_output = float(total_output or 0)
        cache_read = float(cache_read or 0)

        # Net input is input that didn't hit prompt cache
        net_input = max(0.0, total_input - cache_read)

        rates = resolve_model_rates(model_name_or_id, custom_pricing)
        cost = (
            (net_input * rates["input"]) +
            (total_output * rates["output"]) +
            (cache_read * rates["cache"])
        ) / 1_000_000.0

        return max(0.0, cost)
    except Exception:
        return 0.0


def format_cost(cost_usd, currency="$"):
    """Format cost nicely for terminal output (e.g. <$0.001, ~$0.04, $1.25)."""
    if cost_usd <= 0.0:
        return f"{currency}0.00"
    if cost_usd < 0.001:
        return f"<{currency}0.001"
    if cost_usd < 0.01:
        return f"~{currency}{cost_usd:.3f}"
    if cost_usd < 10.0:
        return f"~{currency}{cost_usd:.2f}"
    return f"{currency}{cost_usd:.2f}"
