# -*- coding: utf-8 -*-
"""
AGY-HUD: Advanced Statusline HUD for Google Antigravity CLI.
Main entry point for CLI statusline rendering.
"""
import sys
import os
import json

# Ensure parent directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Ensure UTF-8 output across Windows, macOS, and Linux
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

from hud.config import load_config
from hud.transcript import analyze_transcript
from hud.environment import scan_environment
from hud.renderer import render_hud


def get_preview_payload(mode="full"):
    """Generate realistic mock payload for testing and preview."""
    return {
        "cwd": os.getcwd(),
        "session_id": "mock-preview-session",
        "conversation_id": "mock-preview-session",
        "conversation_title": "调研开发 agy-hud",
        "model": {
            "id": "gemini-3.8-flash-high",
            "display_name": "Gemini 3.8 Flash (High)",
            "effort": "high"
        },
        "product": "antigravity",
        "agent_state": "working",
        "context_window": {
            "total_input_tokens": 128450,
            "total_output_tokens": 18230,
            "context_window_size": 1048576,
            "used_percentage": 14.0,
            "current_usage": {
                "input_tokens": 3420,
                "output_tokens": 680,
                "cache_read_input_tokens": 92100
            }
        },
        "quota": {
            "gemini-5h": {
                "remaining_fraction": 0.94,
                "reset_in_seconds": 16200
            },
            "gemini-weekly": {
                "remaining_fraction": 0.98,
                "reset_in_seconds": 518400
            }
        }
    }


def main():
    config = load_config()

    # Handle command-line preview / testing
    if len(sys.argv) > 1 and sys.argv[1] in ("--test", "-t", "--preview"):
        preview_mode = sys.argv[2] if len(sys.argv) > 2 else config.get("mode", "full")
        config["mode"] = preview_mode
        mock_data = get_preview_payload(preview_mode)
        mock_transcript = {
            "duration": "48m",
            "tool_counts": {"Bash": 43, "View": 10, "Edit": 5, "Web": 1},
            "skills": ["ak-skills-update", "agy-customizations"],
            "last_action": {"tool": "Bash", "summary": "git status"},
            "subagents_count": 0
        }
        mock_env = scan_environment(mock_data["cwd"])
        print(render_hud(mock_data, mock_transcript, mock_env, config))
        return

    # Read stdin from Antigravity CLI
    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            print("🤖 Antigravity HUD │ Ready")
            return
        data = json.loads(raw)
        if not isinstance(data, dict):
            print("🤖 Antigravity HUD │ Ready")
            return
    except Exception:
        print("🤖 Antigravity HUD │ Ready")
        return

    try:
        cwd = data.get("cwd") or os.getcwd()
        env_info = scan_environment(cwd)
        transcript_info = analyze_transcript(data)
        output = render_hud(data, transcript_info, env_info, config)
        print(output)
    except Exception:
        # Graceful fallback
        print(f"🤖 {data.get('model', {}).get('display_name', 'Gemini')} │ 🧠 Ready")


if __name__ == "__main__":
    main()
