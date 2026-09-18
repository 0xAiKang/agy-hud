#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGY-HUD Installer & Configuration Manager.
Configures Antigravity CLI to use AGY-HUD as its live statusline.
"""
import os
import sys
import json
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATUSLINE_SCRIPT = os.path.join(SCRIPT_DIR, "statusline.py")
SETTINGS_FILE = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")


def print_banner():
    print("\033[36m\033[1m🚀 AGY-HUD: Advanced Statusline HUD for Antigravity CLI\033[0m")
    print("-" * 60)


def install():
    print_banner()

    if not os.path.isfile(STATUSLINE_SCRIPT):
        print(f"\033[31mError: Cannot find statusline.py at {STATUSLINE_SCRIPT}\033[0m")
        sys.exit(1)

    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

    # Backup settings if exists
    if os.path.isfile(SETTINGS_FILE):
        backup_path = SETTINGS_FILE + ".bak"
        shutil.copy2(SETTINGS_FILE, backup_path)
        print(f"📦 Backed up existing settings to: {backup_path}")
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            settings = {}
    else:
        settings = {}

    # Update statusLine config
    python_cmd = sys.executable or "python3"
    command_str = f"{python_cmd} {STATUSLINE_SCRIPT}"

    settings["statusLine"] = {
        "type": "command",
        "command": command_str,
        "enabled": True
    }

    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully configured Antigravity CLI!")
    print(f"📁 Target script: \033[33m{STATUSLINE_SCRIPT}\033[0m")
    print(f"⚙️  Settings file: \033[33m{SETTINGS_FILE}\033[0m\n")

    print("\033[32m\033[1mPreviewing your new statusline:\033[0m")
    print("=" * 60)
    os.system(f"{python_cmd} {STATUSLINE_SCRIPT} --preview")
    print("=" * 60)
    print("\n✨ Ready to use! Open or resume your Antigravity CLI to see it live.")


def uninstall():
    print_banner()
    if not os.path.isfile(SETTINGS_FILE):
        print("ℹ️  No settings file found. Nothing to uninstall.")
        return

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception:
        settings = {}

    if "statusLine" in settings:
        del settings["statusLine"]
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        print("🗑️  Removed statusLine configuration from settings.json.")
    else:
        print("ℹ️  statusLine was not configured.")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ("--uninstall", "-u"):
            uninstall()
            return
        if arg in ("--preview", "-p"):
            python_cmd = sys.executable or "python3"
            mode = sys.argv[2] if len(sys.argv) > 2 else "full"
            os.system(f"{python_cmd} {STATUSLINE_SCRIPT} --preview {mode}")
            return

    install()


if __name__ == "__main__":
    main()
