# -*- coding: utf-8 -*-
"""
Configuration manager for AGY-HUD.
Loads settings from config.json, environment variables, or falls back to defaults.
"""
import os
import json

DEFAULT_CONFIG = {
    # Layout mode: "full" (5 lines), "standard" (3 lines), "compact" (2 lines), "minimal" (1 line)
    "mode": "full",

    # Section toggles
    "show_header": True,          # Line 1: Model, product, title, duration, cost
    "show_context": True,         # Line 2: Context window meter
    "show_quotas": True,          # Line 2: 5h and weekly quota counters
    "show_assets": True,          # Line 3: Rules, MCPs, Skills count, permissions
    "show_tools": True,           # Line 4: Tool execution counts & active skill
    "show_tokens": True,          # Line 5: Tokens detail (in, out, cache)

    # Detailed switches
    "show_cost": True,            # Show estimated USD cost
    "show_duration": True,        # Show session running duration
    "show_skills": True,          # Show triggered skills in activity line
    "show_last_action": True,     # Show last executed tool action summary
    "show_git_branch": True,      # Show git branch in header / compact mode
    "show_cwd": True,             # Show current project folder

    # Visual style
    "use_nerd_fonts": False,      # False = clean Unicode emoji, True = Nerd Font glyphs
    "progress_bar_width": 10,     # Context progress bar character length
    "cost_currency": "$",

    # Pricing overrides per 1M tokens (USD)
    "custom_pricing": {}
}

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
GRAY = "\033[90m"
RED = "\033[31m"
WHITE = "\033[37m"


def load_config():
    """Load configuration with hierarchical precedence."""
    config = dict(DEFAULT_CONFIG)

    # Search paths for config.json
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.environ.get("AGY_HUD_CONFIG"),
        os.path.join(script_dir, "config.json"),
        os.path.expanduser("~/.config/agy-hud/config.json"),
        os.path.expanduser("~/.gemini/antigravity-cli/agy-hud.json"),
    ]

    for path in candidates:
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    user_conf = json.load(f)
                    if isinstance(user_conf, dict):
                        config.update(user_conf)
                        config["_loaded_from"] = path
                        break
            except Exception:
                pass

    # Environment variable overrides
    if os.environ.get("AGY_HUD_MODE"):
        config["mode"] = os.environ.get("AGY_HUD_MODE").lower()

    return config
