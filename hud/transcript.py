# -*- coding: utf-8 -*-
"""
Incremental transcript analyzer for AGY-HUD.
Tracks tool calls, triggered skills, recent actions, and session duration.
"""
import os
import json
import re
from datetime import datetime, timezone

FRIENDLY_TOOLS = {
    "run_command": "Bash",
    "view_file": "View",
    "replace_file_content": "Edit",
    "write_to_file": "Write",
    "search_web": "Web",
    "grep_search": "Grep",
    "find_by_name": "Find",
    "read_url_content": "URL",
    "invoke_subagent": "Agent",
    "ask_question": "Ask",
}


def resolve_transcript_path(data):
    """Find the valid path to transcript.jsonl."""
    raw_path = data.get("transcript_path", "")
    if raw_path and os.path.isfile(raw_path):
        return raw_path

    # Check antigravity vs antigravity-cli path differences
    if raw_path and "antigravity" in raw_path and not os.path.isfile(raw_path):
        alt_path = raw_path.replace("/.gemini/antigravity/", "/.gemini/antigravity-cli/")
        if os.path.isfile(alt_path):
            return alt_path

    # Fallback to session_id / conversation_id under ~/.gemini/antigravity-cli/brain/
    cid = data.get("conversation_id") or data.get("session_id")
    if cid:
        for base in ["~/.gemini/antigravity-cli/brain", "~/.gemini/antigravity/brain"]:
            cand = os.path.expanduser(f"{base}/{cid}/.system_generated/logs/transcript.jsonl")
            if os.path.isfile(cand):
                return cand

    return None


def parse_iso_time(ts_str):
    """Safely parse ISO 8601 UTC timestamp."""
    if not ts_str:
        return None
    try:
        # Handle trailing Z
        ts = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def format_duration(start_time_iso):
    """Format duration from start timestamp to now (e.g. 15m, 2h 45m, 3d 12h)."""
    start_dt = parse_iso_time(start_time_iso)
    if not start_dt:
        return ""
    try:
        now = datetime.now(timezone.utc)
        diff = now - start_dt
        total_seconds = int(diff.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds}s"
        minutes = total_seconds // 60
        hours = minutes // 60
        days = hours // 24

        if days > 0:
            rem_hours = hours % 24
            return f"{days}d {rem_hours}h"
        if hours > 0:
            rem_min = minutes % 60
            return f"{hours}h {rem_min}m"
        return f"{minutes}m"
    except Exception:
        return ""


def analyze_transcript(data):
    """
    Incrementally scan transcript.jsonl for tool stats, skills, and session duration.
    Uses seek offset caching to ensure execution is fast (< 5ms).
    """
    result = {
        "start_time": "",
        "duration": "",
        "tool_counts": {},
        "skills": [],
        "last_action": None,
        "subagents_count": 0,
    }

    transcript_path = resolve_transcript_path(data)
    if not transcript_path or not os.path.isfile(transcript_path):
        return result

    cid = data.get("conversation_id") or data.get("session_id") or "default"
    cache_path = f"/tmp/agy_hud_cache_{cid}.json"

    cached_state = {
        "offset": 0,
        "start_time": "",
        "tool_counts": {},
        "skills": [],
        "last_action": None,
        "subagents_count": 0,
    }

    # Load cache if available
    if os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    cached_state.update(loaded)
        except Exception:
            pass

    try:
        file_size = os.path.getsize(transcript_path)
        offset = cached_state.get("offset", 0)

        # File was truncated or rotated
        if offset > file_size:
            offset = 0
            cached_state = {
                "offset": 0,
                "start_time": "",
                "tool_counts": {},
                "skills": [],
                "last_action": None,
                "subagents_count": 0,
            }

        tool_counts = dict(cached_state.get("tool_counts", {}))
        skills_set = set(cached_state.get("skills", []))
        start_time = cached_state.get("start_time", "")
        last_action = cached_state.get("last_action")
        subagents = cached_state.get("subagents_count", 0)

        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            if offset > 0:
                f.seek(offset)

            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    entry = json.loads(line_str)
                    if not start_time and "created_at" in entry:
                        start_time = entry["created_at"]

                    # Check tool calls
                    tool_calls = entry.get("tool_calls")
                    if tool_calls and isinstance(tool_calls, list):
                        for tc in tool_calls:
                            raw_name = tc.get("name", "tool")
                            friendly = FRIENDLY_TOOLS.get(raw_name, raw_name)
                            tool_counts[friendly] = tool_counts.get(friendly, 0) + 1

                            args = tc.get("args") or {}
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except Exception:
                                    pass

                            summary = ""
                            if isinstance(args, dict):
                                summary = args.get("toolSummary") or args.get("toolAction") or args.get("CommandLine") or ""
                            if summary:
                                summary = str(summary).strip("\"' ")
                                if len(summary) > 30:
                                    summary = summary[:27] + "..."
                                last_action = {"tool": friendly, "summary": summary}

                            if raw_name == "invoke_subagent":
                                subagents += 1

                            # Detect skills referenced in arguments
                            args_serialized = json.dumps(args, ensure_ascii=False)
                            matches = re.findall(r"/skills/([a-zA-Z0-9_\-]+)/", args_serialized)
                            for s in matches:
                                skills_set.add(s)

                except Exception:
                    continue

            new_offset = f.tell()

        # Update and save cache
        cached_state = {
            "offset": new_offset,
            "start_time": start_time,
            "tool_counts": tool_counts,
            "skills": sorted(list(skills_set)),
            "last_action": last_action,
            "subagents_count": subagents,
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as cf:
                json.dump(cached_state, cf)
        except Exception:
            pass

        result["start_time"] = start_time
        result["duration"] = format_duration(start_time)
        result["tool_counts"] = tool_counts
        result["skills"] = cached_state["skills"]
        result["last_action"] = last_action
        result["subagents_count"] = subagents

    except Exception:
        pass

    return result
