# -*- coding: utf-8 -*-
"""
View renderer for AGY-HUD.
Assembles layout lines based on active mode, telemetry, and configuration.
"""
import os
from .config import (
    RESET, BOLD, DIM, CYAN, GREEN, YELLOW, MAGENTA, BLUE, GRAY, RED, WHITE
)
from .pricing import calculate_cost, format_cost


def format_tokens(n):
    """Format token count into readable units (e.g. 218, 58.4k, 17.4M)."""
    try:
        n = float(n)
        if n >= 1_000_000:
            val = n / 1_000_000
            return f"{val:.2f}M" if val < 10 else f"{val:.1f}M"
        if n >= 1_000:
            val = n / 1_000
            return f"{val:.1f}k" if val < 100 else f"{int(round(val))}k"
        return str(int(n))
    except Exception:
        return "0"


def format_time_remaining(seconds):
    """Format seconds into concise time units (e.g. 35m, 4h 56m, 5d 1h)."""
    try:
        seconds = float(seconds)
        if seconds <= 0:
            return ""
        total_min = int(seconds // 60)
        hours = total_min // 60
        days = hours // 24

        if days > 0:
            rem_hours = hours % 24
            return f"{days}d {rem_hours}h"
        if hours > 0:
            rem_min = total_min % 60
            return f"{hours}h {rem_min}m"
        return f"{total_min}m"
    except Exception:
        return ""


def make_progress_bar(pct, width=10, use_nerd_fonts=False):
    """Generate a colored progress bar block with safety tiers."""
    try:
        pct = max(0.0, min(100.0, float(pct)))
        filled = int(round((pct / 100.0) * width))
        empty = width - filled

        # Color thresholds: Low (<60% Green), Medium (60-85% Yellow), High (>=85% Red)
        bar_color = GREEN if pct < 60 else (YELLOW if pct < 85 else RED)
        char_filled = "█"
        char_empty = "░"
        return f"{bar_color}{char_filled * filled}{GRAY}{char_empty * empty}{RESET}"
    except Exception:
        return f"{'░' * width}"


def clean_model_name(raw_name):
    """Clean model identifier into a concise label."""
    if not raw_name:
        return "Gemini"
    cleaned = raw_name.replace("Google", "").replace("Gemini", "").replace("Anthropic", "").strip()
    return cleaned if cleaned else raw_name


def render_header_line(data, transcript_info, config):
    """
    Line 1: [Model ◑ effort] │ Product │ Title │ ⏱ Duration │ Cost $X.XX
    """
    items = []

    # Model & Effort
    model_obj = data.get("model") or {}
    m_name = ""
    effort = ""
    if isinstance(model_obj, dict):
        m_name = model_obj.get("display_name") or model_obj.get("id") or "Gemini"
        effort = model_obj.get("effort") or ""
    else:
        m_name = str(model_obj)

    short_model = clean_model_name(m_name)
    effort_str = f" {MAGENTA}◑ {effort}{RESET}" if effort else ""
    items.append(f"[{CYAN}{BOLD}{short_model}{RESET}{effort_str}]")

    # Product
    product = data.get("product") or "Antigravity"
    items.append(f"{YELLOW}{product.capitalize()}{RESET}")

    # Conversation Title
    title = data.get("conversation_title") or ""
    if title:
        if len(title) > 28:
            title = title[:26] + "..."
        items.append(f"{WHITE}{title}{RESET}")

    # Session Duration
    if config.get("show_duration", True):
        duration = transcript_info.get("duration")
        if duration:
            items.append(f"⏱ {duration}")

    # Cost
    if config.get("show_cost", True):
        cw = data.get("context_window") or {}
        tot_in = cw.get("total_input_tokens") or 0
        tot_out = cw.get("total_output_tokens") or 0
        cur_u = cw.get("current_usage") or {}
        cache_r = cur_u.get("cache_read_input_tokens") or 0

        cost_val = calculate_cost(
            m_name, tot_in, tot_out, cache_r, config.get("custom_pricing")
        )
        cost_str = format_cost(cost_val, config.get("cost_currency", "$"))
        items.append(f"Cost {GREEN}{cost_str}{RESET}")

    return f" {GRAY}│{RESET} ".join(items)


def render_context_and_quotas_line(data, config):
    """
    Line 2: 🧠 Context ██░░░░░░░░ 24.5% (244.6k/1.0M) │ ⏳ 5h: 95% (4h 56m) │ 📅 Wk: 99% (167h 56m)
    """
    items = []
    cw = data.get("context_window") or {}

    # Context window progress
    if config.get("show_context", True):
        tot_in = cw.get("total_input_tokens") or 0
        tot_out = cw.get("total_output_tokens") or 0
        total_tokens = tot_in + tot_out
        max_tokens = cw.get("context_window_size") or 1_000_000

        used_pct = cw.get("used_percentage")
        if used_pct is None:
            used_pct = (total_tokens / max_tokens * 100) if max_tokens > 0 else 0.0
        else:
            used_pct = float(used_pct)

        bar_width = config.get("progress_bar_width", 10)
        p_bar = make_progress_bar(used_pct, width=bar_width)
        items.append(
            f"🧠 {BOLD}Context{RESET} {p_bar} {used_pct:.1f}% ({format_tokens(total_tokens)}/{format_tokens(max_tokens)})"
        )

    # Quotas: 5h and Weekly
    if config.get("show_quotas", True):
        quotas = data.get("quota") or {}
        # Resolve 5h
        q5h = quotas.get("gemini-5h") or quotas.get("3p-5h") or quotas.get("five_hour")
        if isinstance(q5h, dict):
            rem = q5h.get("remaining_fraction")
            res_sec = q5h.get("reset_in_seconds", 0)
            if rem is not None:
                pct = float(rem) * 100
                res_str = f" {GRAY}({format_time_remaining(res_sec)}){RESET}" if res_sec else ""
                color = GREEN if pct > 30 else (YELLOW if pct > 10 else RED)
                items.append(f"⏳ 5h: {color}{pct:.0f}%{RESET}{res_str}")

        # Resolve Weekly
        qwk = quotas.get("gemini-weekly") or quotas.get("3p-weekly") or quotas.get("weekly")
        if isinstance(qwk, dict):
            rem = qwk.get("remaining_fraction")
            res_sec = qwk.get("reset_in_seconds", 0)
            if rem is not None:
                pct = float(rem) * 100
                res_str = f" {GRAY}({format_time_remaining(res_sec)}){RESET}" if res_sec else ""
                color = GREEN if pct > 30 else (YELLOW if pct > 10 else RED)
                items.append(f"📅 Wk: {color}{pct:.0f}%{RESET}{res_str}")

    return f" {GRAY}│{RESET} ".join(items)


def render_assets_line(env_info, config):
    """
    Line 3: ⚡ 1 AGENTS.md │ 1 MCP (river-memory) │ 93 Skills │ 🛡️ bypass permissions on
    """
    items = []
    if env_info.get("rules_label"):
        items.append(f"⚡ {YELLOW}{env_info['rules_label']}{RESET}")

    if env_info.get("mcp_label"):
        items.append(f"{CYAN}{env_info['mcp_label']}{RESET}")

    if env_info.get("skills_count", 0) > 0:
        items.append(f"{MAGENTA}{env_info['skills_count']} Skills{RESET}")

    if env_info.get("permission_mode"):
        perm = env_info["permission_mode"]
        perm_color = GREEN if "bypass" in perm else YELLOW
        items.append(f"🛡️ {perm_color}{perm}{RESET}")

    return f" {GRAY}│{RESET} ".join(items)


def render_tools_line(transcript_info, config):
    """
    Line 4: 🔧 ✓ Bash ×54 │ ✓ View ×10 │ ✓ Edit ×5 │ 🎯 Skills: agy-customizations
    """
    items = []
    tool_counts = transcript_info.get("tool_counts") or {}

    t_parts = []
    for tname in ["Bash", "View", "Edit", "Write", "Web", "Grep", "Find", "URL", "Agent"]:
        if tname in tool_counts and tool_counts[tname] > 0:
            t_parts.append(f"{GREEN}✓{RESET} {tname} {GRAY}×{tool_counts[tname]}{RESET}")

    # Add other tools not in standard list
    for tname, cnt in tool_counts.items():
        if tname not in ["Bash", "View", "Edit", "Write", "Web", "Grep", "Find", "URL", "Agent"] and cnt > 0:
            t_parts.append(f"{GREEN}✓{RESET} {tname} {GRAY}×{cnt}{RESET}")

    if t_parts:
        items.append("🔧 " + f" {GRAY}│{RESET} ".join(t_parts[:5]))

    # Triggered skills
    if config.get("show_skills", True):
        skills = transcript_info.get("skills") or []
        if skills:
            skills_display = ", ".join(skills[:3])
            if len(skills) > 3:
                skills_display += f" (+{len(skills)-3})"
            items.append(f"🎯 {CYAN}Skills: {skills_display}{RESET}")

    return f" {GRAY}│{RESET} ".join(items) if items else ""


def render_tokens_line(data, config):
    """
    Line 5: 📊 Tokens: 128k (in: 2.6k, out: 426, cache: 93.9k · 97.2% hit)
    """
    cw = data.get("context_window") or {}
    tot_in = cw.get("total_input_tokens") or 0
    tot_out = cw.get("total_output_tokens") or 0
    cur_u = cw.get("current_usage") or {}

    in_t = cur_u.get("input_tokens") or 0
    out_t = cur_u.get("output_tokens") or 0
    cache_r = cur_u.get("cache_read_input_tokens") or 0

    tot_session = tot_in + tot_out
    parts = [f"in: {format_tokens(in_t)}", f"out: {format_tokens(out_t)}"]

    if cache_r > 0:
        total_eval = in_t + cache_r
        hit_pct = (cache_r / total_eval * 100) if total_eval > 0 else 0
        parts.append(f"cache: {format_tokens(cache_r)} · {GREEN}{hit_pct:.1f}% hit{RESET}")

    return f"📊 {BOLD}Tokens{RESET}: {format_tokens(tot_session)} ({', '.join(parts)})"


def render_hud(data, transcript_info, env_info, config):
    """Master renderer choosing layout according to config['mode']."""
    mode = config.get("mode", "full").lower()
    lines = []

    if mode == "full":
        # 5-line comprehensive dashboard
        if config.get("show_header", True):
            l1 = render_header_line(data, transcript_info, config)
            if l1:
                lines.append(l1)

        l2 = render_context_and_quotas_line(data, config)
        if l2:
            lines.append(l2)

        if config.get("show_assets", True):
            l3 = render_assets_line(env_info, config)
            if l3:
                lines.append(l3)

        if config.get("show_tools", True):
            l4 = render_tools_line(transcript_info, config)
            if l4:
                lines.append(l4)

        if config.get("show_tokens", True):
            l5 = render_tokens_line(data, config)
            if l5:
                lines.append(l5)

    elif mode == "standard":
        # 3-line balanced layout
        l1 = render_header_line(data, transcript_info, config)
        if l1:
            lines.append(l1)

        l2 = render_context_and_quotas_line(data, config)
        if l2:
            lines.append(l2)

        l4 = render_tools_line(transcript_info, config)
        if l4:
            lines.append(l4)

    elif mode == "compact":
        # 2-line classic layout
        # Line 1: Model, Directory, Branch, Agent State
        m_name = clean_model_name((data.get("model") or {}).get("display_name") or "Gemini")
        cwd = os.path.basename(data.get("cwd", "")) or "workspace"
        branch = env_info.get("git_branch") or "main"
        state = data.get("agent_state", "idle")
        s_color = GREEN if state.lower() in ("idle", "ready") else YELLOW

        l1_parts = [
            f"🤖 {CYAN}{BOLD}{m_name}{RESET}",
            f"📁 {YELLOW}{cwd}{RESET}",
            f"🌿 {MAGENTA}{branch}{RESET}",
            f"⚡ {s_color}{state}{RESET}"
        ]
        lines.append(f" {GRAY}│{RESET} ".join(l1_parts))

        # Line 2: Context + Quotas + Cost
        l2 = render_context_and_quotas_line(data, config)
        if config.get("show_cost", True):
            cw = data.get("context_window") or {}
            c_val = calculate_cost(m_name, cw.get("total_input_tokens"), cw.get("total_output_tokens"))
            l2 += f" {GRAY}│{RESET} {GREEN}{format_cost(c_val)}{RESET}"
        lines.append(l2)

    elif mode == "minimal":
        # 1-line ultra compact
        m_name = clean_model_name((data.get("model") or {}).get("display_name") or "Gemini")
        cw = data.get("context_window") or {}
        used_pct = cw.get("used_percentage") or 0.0
        p_bar = make_progress_bar(used_pct, width=8)
        lines.append(f"🤖 {m_name} │ 🧠 {p_bar} {float(used_pct):.0f}% │ ⚡ {data.get('agent_state', 'idle')}")

    return "\n".join(lines)
