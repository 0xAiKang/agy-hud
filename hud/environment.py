# -*- coding: utf-8 -*-
"""
Environment asset scanner for AGY-HUD.
Scans workspace rules, MCP servers, installed skills, permissions, and git status.
"""
import os
import json


def get_git_branch(start_path):
    """
    Ultra-fast Git branch detector.
    Reads .git/HEAD directly without spawning subprocesses.
    """
    if not start_path:
        return ""
    try:
        cur = os.path.abspath(start_path)
    except Exception:
        return ""

    for _ in range(8):
        git_dir = os.path.join(cur, ".git")
        if os.path.isdir(git_dir):
            head_file = os.path.join(git_dir, "HEAD")
            if os.path.isfile(head_file):
                try:
                    with open(head_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().strip()
                        if content.startswith("ref: refs/heads/"):
                            return content[len("ref: refs/heads/"):]
                        elif len(content) >= 7:
                            return content[:7]
                except Exception:
                    pass
        elif os.path.isfile(git_dir):
            # Worktree gitdir pointer
            try:
                with open(git_dir, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                    if content.startswith("gitdir:"):
                        real_git = content[len("gitdir:"):].strip()
                        if not os.path.isabs(real_git):
                            real_git = os.path.join(cur, real_git)
                        head_file = os.path.join(real_git, "HEAD")
                        if os.path.isfile(head_file):
                            with open(head_file, "r", encoding="utf-8", errors="ignore") as hf:
                                hcontent = hf.read().strip()
                                if hcontent.startswith("ref: refs/heads/"):
                                    return hcontent[len("ref: refs/heads/"):]
                                elif len(hcontent) >= 7:
                                    return hcontent[:7]
            except Exception:
                pass

        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    return ""


def scan_environment(cwd):
    """Scan local assets: rules, MCPs, skills count, and permission policy."""
    info = {
        "rules_label": "",
        "mcp_label": "",
        "skills_count": 0,
        "permission_mode": "",
        "git_branch": get_git_branch(cwd),
    }

    # 1. Scan Rules in workspace
    rule_files = []
    if cwd and os.path.isdir(cwd):
        for fname in ["AGENTS.md", "GEMINI.md", "CLAUDE.md"]:
            if os.path.isfile(os.path.join(cwd, fname)):
                rule_files.append(fname)
        rules_dir = os.path.join(cwd, ".agents", "rules")
        if os.path.isdir(rules_dir):
            try:
                rule_files.extend([f for f in os.listdir(rules_dir) if f.endswith(".md")])
            except Exception:
                pass

    if rule_files:
        info["rules_label"] = f"{len(rule_files)} {rule_files[0]}"
    else:
        info["rules_label"] = "No Rules"

    # 2. Scan MCPs
    mcp_names = []
    mcp_base = os.path.expanduser("~/.gemini/antigravity-cli/mcp")
    if os.path.isdir(mcp_base):
        try:
            for item in os.listdir(mcp_base):
                if not item.startswith(".") and os.path.isdir(os.path.join(mcp_base, item)):
                    mcp_names.append(item)
        except Exception:
            pass

    if mcp_names:
        first_mcp = mcp_names[0]
        if len(mcp_names) == 1:
            info["mcp_label"] = f"1 MCP ({first_mcp})"
        else:
            info["mcp_label"] = f"{len(mcp_names)} MCPs ({first_mcp}...)"
    else:
        info["mcp_label"] = "0 MCPs"

    # 3. Scan Skills Count
    total_skills = 0
    skills_dir = os.path.expanduser("~/.gemini/config/skills")
    if os.path.isdir(skills_dir):
        try:
            total_skills += len([d for d in os.listdir(skills_dir) if not d.startswith(".")])
        except Exception:
            pass
    info["skills_count"] = total_skills

    # 4. Permissions Mode
    settings_path = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
    perm_mode = "prompt"
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as sf:
                sdata = json.load(sf)
                policy = sdata.get("autoExecutionPolicy") or sdata.get("toolPermission") or ""
                if policy == "always-proceed":
                    perm_mode = "bypass"
                elif "proceed" in policy:
                    perm_mode = "auto"
        except Exception:
            pass

    if perm_mode == "bypass":
        info["permission_mode"] = "bypass permissions on"
    else:
        info["permission_mode"] = "permissions prompt"

    return info
