# 🚀 AGY-HUD

**An advanced, information-dense Statusline HUD for Google Antigravity CLI (`agy`).**

Inspired by Claude-HUD's comprehensive layout, AGY-HUD renders real-time telemetry (active model, USD cost, context window capacity, tool execution tallies, triggered skills, and workspace assets) with near-zero latency (< 20ms) and zero external dependencies.

[English](README.md) | [中文文档](README_zh.md)

<p align="center">
  <img src="docs/preview.svg" alt="AGY-HUD live preview" width="100%">
</p>

---

## ✨ Key Features

- 💰 **Real-time Cost Estimation**: Computes session token expenditure in USD dynamically based on model pricing (including prompt cache read discounts).
- 🔧 **Tool Execution Tracker**: Keeps a live count of commands run (`✓ Bash ×43`), files read (`✓ View ×10`), and files modified (`✓ Edit ×5`).
- 🎯 **Skill Awareness**: Automatically detects and lists skills loaded by the agent during the conversation.
- 🧠 **Context Meter**: Clear progress bar with green/yellow/red thresholds showing current input occupancy, total limit, and percentage (`14.0% (147k/1.05M)`).
- ⏳ **Dual Quota Monitoring**: Tracks rolling 5-hour and 7-day rate limits with live reset countdown timers (`94% (4h 30m)`).
- ⚡ **Environment Assets**: Displays active workspace rules (`AGENTS.md`), registered MCP servers (`river-memory`), skills count, and permission bypass status.
- 📊 **Token Breakdown**: Displays in/out tokens and prompt cache hit rate.
- 🪶 **Zero Dependencies**: Pure Python standard library (`sys`, `json`, `os`). Works out-of-the-box on macOS, Linux, and Windows.

---

## 🖥️ Layout Modes

Configure preset layouts easily via `config.json`:

### 1. Full Mode (`full`, Default)
Comprehensive 5-line statusline:
```text
[3.8 Flash (High) ◑ high] │ Antigravity │ 调研开发 agy-hud │ ⏱ 48m │ Cost ~$0.04
🧠 Context █░░░░░░░░░ 14.0% (147k/1.05M) │ ⏳ 5h: 94% (4h 30m) │ 📅 Wk: 98% (6d 0h)
⚡ 1 AGENTS.md │ 1 MCP (river-memory) │ 93 Skills │ 🛡️ bypass permissions on
🔧 ✓ Bash ×43 │ ✓ View ×10 │ ✓ Edit ×5 │ ✓ Web ×1 │ 🎯 Skills: ak-skills-update
📊 Tokens: 147k (in: 3.4k, out: 680, cache: 92.1k · 96.4% hit)
```

### 2. Standard Mode (`standard`)
Balanced 3-line layout:
```text
[3.8 Flash (High) ◑ high] │ Antigravity │ 调研开发 agy-hud │ ⏱ 48m │ Cost ~$0.04
🧠 Context █░░░░░░░░░ 14.0% (147k/1.05M) │ ⏳ 5h: 94% (4h 30m) │ 📅 Wk: 98% (6d 0h)
🔧 ✓ Bash ×43 │ ✓ View ×10 │ ✓ Edit ×5 │ 🎯 Skills: ak-skills-update
```

### 3. Compact Mode (`compact`)
Classic 2-line layout:
```text
🤖 3.8 Flash (High) │ 📁 agy-hud │ 🌿 main │ ⚡ working
🧠 Context █░░░░░░░░░ 14.0% (147k/1.05M) │ ⏳ 5h: 94% (4h 30m) │ 📅 Wk: 98% (6d 0h) │ ~$0.04
```

### 4. Minimal Mode (`minimal`)
Single-line statusline:
```text
🤖 3.8 Flash (High) │ 🧠 █░░░░░░░ 14% │ ⚡ working
```

---

## ⚡ Quick Setup

### One-Click Install

Run the installer from the repository directory:

```bash
cd /Users/boo/Projects/0xAiKang/agy-hud
python3 install.py
```

The installer:
1. Backs up `~/.gemini/antigravity-cli/settings.json`.
2. Adds the `"statusLine"` entry pointing to `statusline.py`.
3. Renders a live preview to verify the setup.

### Live Preview Without Restarting CLI

```bash
# Preview current default mode
python3 statusline.py --preview

# Preview specific layout presets
python3 statusline.py --preview standard
python3 statusline.py --preview compact
python3 statusline.py --preview minimal
```

---

## ⚙️ Configuration (`config.json`)

Create `config.json` in the project directory (see [`config.example.json`](config.example.json)):

```json
{
  "mode": "full",
  "show_header": true,
  "show_context": true,
  "show_quotas": true,
  "show_assets": true,
  "show_tools": true,
  "show_tokens": true,
  "show_cost": true,
  "show_duration": true,
  "show_skills": true,
  "progress_bar_width": 10,
  "cost_currency": "$"
}
```

---

## 🗑️ Uninstall

To remove the statusline configuration:

```bash
python3 install.py --uninstall
```

---

## 📄 License

MIT License. Forked and enhanced from [doraemonkeys/agy-statusline](https://github.com/doraemonkeys/agy-statusline).
