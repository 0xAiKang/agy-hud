# -*- coding: utf-8 -*-
"""
AGY Statusline Installer
Installs and configures agy-statusline for Google Antigravity CLI (agy).
"""
import os
import sys
import json
import shutil
import time
import subprocess

# Ensure UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_default_config_dir():
    """Get the default Antigravity CLI directory."""
    return os.path.expanduser("~/.gemini/antigravity-cli")


def install():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    source_script = os.path.join(repo_dir, "statusline.py")

    if not os.path.isfile(source_script):
        print(f"❌ Error: Could not find statusline.py in {repo_dir}")
        sys.exit(1)

    config_dir = get_default_config_dir()
    os.makedirs(config_dir, exist_ok=True)

    target_script = os.path.join(config_dir, "statusline.py")
    settings_file = os.path.join(config_dir, "settings.json")

    # 1. Copy script into ~/.gemini/antigravity-cli/
    print(f"📦 Copying statusline.py to {target_script} ...")
    shutil.copy2(source_script, target_script)

    # 2. Read existing settings or create empty dict
    settings = {}
    if os.path.isfile(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
            # Create backup
            backup_file = f"{settings_file}.bak.{int(time.time())}"
            shutil.copy2(settings_file, backup_file)
            print(f"🛡️  Backup created: {backup_file}")
        except Exception as e:
            print(f"⚠️  Warning: Could not parse existing settings.json: {e}")
            settings = {}

    # 3. Use python command with forward slashes for cross-platform safety
    normalized_path = target_script.replace("\\", "/")
    command_str = f"python {normalized_path}"

    settings["statusLine"] = {
        "type": "command",
        "command": command_str,
        "enabled": True
    }

    # 4. Save settings.json
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"✅ Successfully updated {settings_file}")
    print(f"✨ StatusLine command set to: {command_str}")
    print("\n🔍 Running preview test:")
    try:
        subprocess.run([sys.executable, target_script, "--preview"], check=True)
    except Exception as e:
        print(f"⚠️ Preview test warning: {e}")

    print("\n🎉 Installation complete! Restart or run `agy` to see your new statusline.")


def uninstall():
    config_dir = get_default_config_dir()
    settings_file = os.path.join(config_dir, "settings.json")

    if not os.path.isfile(settings_file):
        print("ℹ️ No settings.json found, nothing to uninstall.")
        return

    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception as e:
        print(f"❌ Error reading settings.json: {e}")
        return

    if "statusLine" in settings:
        del settings["statusLine"]
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"✅ Removed statusLine configuration from {settings_file}")
    else:
        print("ℹ️ statusLine was not configured.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--uninstall", "-u"):
        uninstall()
    else:
        install()
