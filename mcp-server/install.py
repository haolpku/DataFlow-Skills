#!/usr/bin/env python3
"""
install.py  —  Register DataFlow WebUI MCP Server into Claude Code and/or Cursor,
               and copy Skills to the appropriate locations.

Usage:
    python install.py                        # register MCP for Claude Code (global)
    python install.py --target cursor        # register MCP for Cursor
    python install.py --target both          # register MCP for both
    python install.py --webui-url http://host:8000  # custom WebUI URL
    python install.py --skills-path /path/to/DataFlow-Skills

What gets installed:
    Claude Code:
      - MCP server registered in ~/.claude/claude_desktop_config.json
      - Skills (slash commands) copied to ~/.claude/skills/
    Cursor:
      - MCP server registered in Cursor settings.json
      - Cursor Skills copied to ~/.cursor/skills/
        (dataflow-pipeline-generator, dataflow-webui)
"""

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_DIR.parent

# ── Helpers ─────────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Wrote {path}")


def _mcp_entry(server_script: Path, webui_url: str, skills_path: Path) -> dict:
    python_exe = sys.executable
    return {
        "command": python_exe,
        "args": [str(server_script)],
        "env": {
            "DATAFLOW_WEBUI_URL": webui_url,
            "DATAFLOW_SKILLS_PATH": str(skills_path),
        },
    }


# ── Claude Code ─────────────────────────────────────────────────────────────────

def install_claude_code(server_script: Path, webui_url: str, skills_path: Path):
    """Write to ~/.claude/claude_desktop_config.json (global Claude Code config)."""
    config_path = Path.home() / ".claude" / "claude_desktop_config.json"
    cfg = _load_json(config_path)
    cfg.setdefault("mcpServers", {})
    cfg["mcpServers"]["dataflow-webui"] = _mcp_entry(server_script, webui_url, skills_path)
    _save_json(config_path, cfg)
    print(f"  Claude Code MCP registered at: {config_path}")


# ── Cursor ───────────────────────────────────────────────────────────────────────

def _cursor_settings_path() -> Path:
    """Locate Cursor's settings.json based on OS."""
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "settings.json"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "settings.json"
    else:  # Linux
        return Path.home() / ".config" / "Cursor" / "User" / "settings.json"


def install_cursor(server_script: Path, webui_url: str, skills_path: Path):
    """Write MCP config into Cursor settings.json."""
    settings_path = _cursor_settings_path()
    cfg = _load_json(settings_path)

    entry = _mcp_entry(server_script, webui_url, skills_path)
    # Cursor uses "mcp.servers" key
    cfg.setdefault("mcp", {}).setdefault("servers", {})
    cfg["mcp"]["servers"]["dataflow-webui"] = entry
    _save_json(settings_path, cfg)
    print(f"  Cursor MCP registered at: {settings_path}")


# ── Claude Code skills copy ───────────────────────────────────────────────────────

def install_claude_skills(skills_path: Path):
    """Copy skills to ~/.claude/skills/ for Claude Code slash commands."""
    import shutil
    skills_dest = Path.home() / ".claude" / "skills"
    skills_dest.mkdir(parents=True, exist_ok=True)

    skill_dirs = [
        "generating-dataflow-pipeline",
        "dataflow-operator-builder",
        "prompt-template-builder",
        "dataflow-dev",
        "core_text",
    ]
    for d in skill_dirs:
        src = skills_path / d
        dst = skills_dest / d
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  Copied skill: {d} → {dst}")
        else:
            print(f"  Skipped (not found): {src}")

    print(f"\n  Skills installed to: {skills_dest}")
    print("  In Claude Code, use slash commands: /generating-dataflow-pipeline, /dataflow-operator-builder, etc.")


def install_cursor_skills(skills_path: Path):
    """Copy Cursor Skills to ~/.cursor/skills/ for Cursor agent discovery."""
    import shutil
    cursor_skills_src = skills_path / ".cursor" / "skills"
    if not cursor_skills_src.exists():
        print(f"  Cursor Skills source not found: {cursor_skills_src}")
        return

    cursor_skills_dest = Path.home() / ".cursor" / "skills"
    cursor_skills_dest.mkdir(parents=True, exist_ok=True)

    for skill_dir in cursor_skills_src.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            dst = cursor_skills_dest / skill_dir.name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(skill_dir, dst)
            print(f"  Copied Cursor Skill: {skill_dir.name} → {dst}")

    print(f"\n  Cursor Skills installed to: {cursor_skills_dest}")
    print("  Cursor will auto-discover these skills based on their descriptions.")


# ── Main ─────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Install DataFlow MCP Server")
    parser.add_argument(
        "--target",
        choices=["claude", "cursor", "both"],
        default="claude",
        help="Which editor to configure (default: claude)",
    )
    parser.add_argument(
        "--webui-url",
        default="http://localhost:8000",
        help="DataFlow WebUI backend URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--skills-path",
        default=str(SKILLS_ROOT),
        help=f"Path to DataFlow-Skills root (default: {SKILLS_ROOT})",
    )
    parser.add_argument(
        "--no-skills",
        action="store_true",
        help="Skip copying skills to Claude Code ~/.claude/skills/",
    )
    args = parser.parse_args()

    server_script = SCRIPT_DIR / "server.py"
    skills_path = Path(args.skills_path)
    webui_url = args.webui_url

    print(f"\nDataFlow MCP Server Installer")
    print(f"  Server script : {server_script}")
    print(f"  Skills path   : {skills_path}")
    print(f"  WebUI URL     : {webui_url}")
    print(f"  Target        : {args.target}\n")

    if args.target in ("claude", "both"):
        print("[1/2] Registering MCP server for Claude Code...")
        install_claude_code(server_script, webui_url, skills_path)
        if not args.no_skills:
            print("[2/2] Copying skills to Claude Code...")
            install_claude_skills(skills_path)

    if args.target in ("cursor", "both"):
        print("[1/2] Registering MCP server for Cursor...")
        install_cursor(server_script, webui_url, skills_path)
        if not args.no_skills:
            print("[2/2] Copying Cursor Skills to ~/.cursor/skills/...")
            install_cursor_skills(skills_path)

    print("\nInstallation complete!")
    print("Make sure to:")
    print(f"  1. Install dependencies: pip install -r {SCRIPT_DIR / 'requirements.txt'}")
    print(f"  2. Start DataFlow WebUI backend: cd DataFlow-WebUI/backend && uvicorn app.main:app --port 8000")
    print(f"  3. Restart Claude Code / Cursor to pick up the new MCP server and Skills")


if __name__ == "__main__":
    main()
