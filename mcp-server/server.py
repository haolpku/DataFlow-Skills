#!/usr/bin/env python3
"""
DataFlow WebUI MCP Server
Exposes DataFlow WebUI REST API as MCP tools for Claude Code / Cursor agents,
and serves DataFlow-Skills content as MCP resources.

Usage:
    python server.py

Environment variables:
    DATAFLOW_WEBUI_URL   - WebUI backend URL (default: http://localhost:8000)
    DATAFLOW_SKILLS_PATH - Path to DataFlow-Skills root (default: parent of this file)
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Any, Optional, Sequence
import httpx

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# ── Configuration ──────────────────────────────────────────────────────────────

WEBUI_BASE_URL = os.environ.get("DATAFLOW_WEBUI_URL", "http://localhost:8000").rstrip("/")
SKILLS_ROOT = Path(os.environ.get("DATAFLOW_SKILLS_PATH", Path(__file__).parent.parent))

# ── Server instance ─────────────────────────────────────────────────────────────

server = Server("dataflow-webui")

# ── HTTP helpers ────────────────────────────────────────────────────────────────

def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=WEBUI_BASE_URL, timeout=60.0)


async def _get(path: str, params: dict | None = None) -> Any:
    async with _client() as c:
        r = await c.get(path, params=params)
        r.raise_for_status()
        return r.json()


async def _post(path: str, body: dict | None = None, params: dict | None = None) -> Any:
    async with _client() as c:
        r = await c.post(path, json=body, params=params)
        r.raise_for_status()
        return r.json()


async def _delete(path: str) -> Any:
    async with _client() as c:
        r = await c.delete(path)
        r.raise_for_status()
        return r.json()


def _ok(data: Any) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


def _err(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"ERROR: {msg}")]


# ── Skill content reader ────────────────────────────────────────────────────────

def _read_skill(relative_path: str) -> str:
    """Read a skill file from DataFlow-Skills directory."""
    full = SKILLS_ROOT / relative_path
    if not full.exists():
        return f"[File not found: {full}]"
    return full.read_text(encoding="utf-8")


def _list_skills() -> list[dict]:
    """Walk DataFlow-Skills directory and enumerate all SKILL.md files."""
    skills = []
    for md in SKILLS_ROOT.rglob("SKILL.md"):
        rel = md.relative_to(SKILLS_ROOT)
        parts = list(rel.parts)
        # Extract name from frontmatter if available
        text = md.read_text(encoding="utf-8")
        name = str(rel.parent).replace("\\", "/")
        for line in text.splitlines():
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
                break
        skills.append({
            "name": name,
            "path": str(rel).replace("\\", "/"),
            "uri": f"skill://{str(rel.parent).replace(chr(92), '/')}",
        })
    return skills


# ── Tools ───────────────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── Dataset tools ─────────────────────────────────────────────────────
        types.Tool(
            name="list_datasets",
            description="List all datasets registered in DataFlow WebUI. Returns dataset IDs, names, and file paths.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_dataset_preview",
            description="Preview sample rows from a dataset.",
            inputSchema={
                "type": "object",
                "required": ["dataset_id"],
                "properties": {
                    "dataset_id": {"type": "string", "description": "Dataset ID to preview"},
                },
            },
        ),
        # ── Operator tools ────────────────────────────────────────────────────
        types.Tool(
            name="list_operators",
            description="List all available DataFlow operators. Use this to discover what operators are registered in the WebUI.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_operator_details",
            description="Get detailed parameter schema for a specific DataFlow operator.",
            inputSchema={
                "type": "object",
                "required": ["operator_name"],
                "properties": {
                    "operator_name": {"type": "string", "description": "Exact operator class name, e.g. PromptedGenerator"},
                },
            },
        ),
        # ── Pipeline tools ────────────────────────────────────────────────────
        types.Tool(
            name="list_pipelines",
            description="List all pipelines saved in DataFlow WebUI.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_pipeline",
            description="Get full configuration of a pipeline by its ID.",
            inputSchema={
                "type": "object",
                "required": ["pipeline_id"],
                "properties": {
                    "pipeline_id": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="create_pipeline",
            description=(
                "Create and save a new pipeline in DataFlow WebUI. "
                "The pipeline config describes operators in execution order. "
                "Use list_operators to check available operator names and their params."
            ),
            inputSchema={
                "type": "object",
                "required": ["name", "input_dataset_id", "operators"],
                "properties": {
                    "name": {"type": "string", "description": "Human-readable pipeline name"},
                    "input_dataset_id": {"type": "string", "description": "Dataset ID (from list_datasets)"},
                    "operators": {
                        "type": "array",
                        "description": "Ordered list of operators",
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string", "description": "Operator class name"},
                                "params": {
                                    "type": "object",
                                    "description": "Operator params with 'init' and 'run' sub-keys",
                                    "properties": {
                                        "init": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "value": {},
                                                },
                                            },
                                        },
                                        "run": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "value": {},
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for the pipeline",
                    },
                },
            },
        ),
        types.Tool(
            name="delete_pipeline",
            description="Delete a pipeline from DataFlow WebUI.",
            inputSchema={
                "type": "object",
                "required": ["pipeline_id"],
                "properties": {
                    "pipeline_id": {"type": "string"},
                },
            },
        ),
        # ── Task / execution tools ─────────────────────────────────────────────
        types.Tool(
            name="execute_pipeline",
            description=(
                "Execute a pipeline by its ID. Returns the task execution result. "
                "For long pipelines use execute_pipeline_async instead."
            ),
            inputSchema={
                "type": "object",
                "required": ["pipeline_id"],
                "properties": {
                    "pipeline_id": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="execute_pipeline_async",
            description=(
                "Submit a pipeline for async execution using Ray. Returns task_id immediately. "
                "Poll with get_task_status to wait for completion."
            ),
            inputSchema={
                "type": "object",
                "required": ["pipeline_id"],
                "properties": {
                    "pipeline_id": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="get_task_status",
            description="Poll the status of a pipeline execution task (queued / running / completed / failed).",
            inputSchema={
                "type": "object",
                "required": ["task_id"],
                "properties": {
                    "task_id": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="get_task_result",
            description="Retrieve sample rows from a completed pipeline execution.",
            inputSchema={
                "type": "object",
                "required": ["task_id"],
                "properties": {
                    "task_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 5, "description": "Number of rows to return"},
                },
            },
        ),
        types.Tool(
            name="list_executions",
            description="List all past pipeline execution records.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── Serving tools ─────────────────────────────────────────────────────
        types.Tool(
            name="list_servings",
            description="List all LLM serving configurations registered in DataFlow WebUI.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── Skill tools ───────────────────────────────────────────────────────
        types.Tool(
            name="list_skills",
            description=(
                "List all available DataFlow Skills (SKILL.md files). "
                "Skills provide operator API docs, pipeline generation rules, and examples."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_skill_content",
            description=(
                "Read the content of a DataFlow Skill file. "
                "Use the 'path' from list_skills output (e.g. 'generating-dataflow-pipeline/SKILL.md')."
            ),
            inputSchema={
                "type": "object",
                "required": ["path"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path inside DataFlow-Skills, e.g. 'generating-dataflow-pipeline/SKILL.md'",
                    },
                },
            },
        ),
    ]


# ── Tool call dispatcher ────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        # ── Dataset ───────────────────────────────────────────────────────────
        if name == "list_datasets":
            data = await _get("/api/v1/datasets/")
            return _ok(data)

        if name == "get_dataset_preview":
            ds_id = arguments["dataset_id"]
            data = await _get(f"/api/v1/datasets/preview/{ds_id}")
            return _ok(data)

        # ── Operators ─────────────────────────────────────────────────────────
        if name == "list_operators":
            data = await _get("/api/v1/operators/")
            return _ok(data)

        if name == "get_operator_details":
            op_name = arguments["operator_name"]
            data = await _get(f"/api/v1/operators/details/{op_name}")
            return _ok(data)

        # ── Pipelines ─────────────────────────────────────────────────────────
        if name == "list_pipelines":
            data = await _get("/api/v1/pipelines/")
            return _ok(data)

        if name == "get_pipeline":
            data = await _get(f"/api/v1/pipelines/{arguments['pipeline_id']}")
            return _ok(data)

        if name == "create_pipeline":
            ops = arguments.get("operators", [])
            # Ensure params have init/run structure
            for op in ops:
                if "params" not in op or op["params"] is None:
                    op["params"] = {"init": [], "run": []}
                if "init" not in op["params"]:
                    op["params"]["init"] = []
                if "run" not in op["params"]:
                    op["params"]["run"] = []

            body = {
                "name": arguments["name"],
                "config": {
                    "file_path": "",
                    "input_dataset": arguments["input_dataset_id"],
                    "operators": ops,
                },
                "tags": arguments.get("tags", []),
            }
            data = await _post("/api/v1/pipelines/", body)
            return _ok(data)

        if name == "delete_pipeline":
            data = await _delete(f"/api/v1/pipelines/{arguments['pipeline_id']}")
            return _ok(data)

        # ── Tasks ─────────────────────────────────────────────────────────────
        if name == "execute_pipeline":
            data = await _post("/api/v1/tasks/execute", params={"pipeline_id": arguments["pipeline_id"]})
            return _ok(data)

        if name == "execute_pipeline_async":
            data = await _post("/api/v1/tasks/execute-async", params={"pipeline_id": arguments["pipeline_id"]})
            return _ok(data)

        if name == "get_task_status":
            data = await _get(f"/api/v1/tasks/execution/{arguments['task_id']}/status")
            return _ok(data)

        if name == "get_task_result":
            params = {"limit": arguments.get("limit", 5)}
            data = await _get(f"/api/v1/tasks/execution/{arguments['task_id']}/result", params=params)
            return _ok(data)

        if name == "list_executions":
            data = await _get("/api/v1/tasks/executions")
            return _ok(data)

        # ── Serving ───────────────────────────────────────────────────────────
        if name == "list_servings":
            data = await _get("/api/v1/serving/")
            return _ok(data)

        # ── Skills (local file reads) ──────────────────────────────────────────
        if name == "list_skills":
            return _ok(_list_skills())

        if name == "get_skill_content":
            content = _read_skill(arguments["path"])
            return [types.TextContent(type="text", text=content)]

        return _err(f"Unknown tool: {name}")

    except httpx.HTTPStatusError as e:
        return _err(f"WebUI API error {e.response.status_code}: {e.response.text}")
    except httpx.ConnectError:
        return _err(
            f"Cannot connect to DataFlow WebUI at {WEBUI_BASE_URL}. "
            "Make sure the backend is running: cd DataFlow-WebUI/backend && uvicorn app.main:app --port 8000"
        )
    except Exception as e:
        return _err(f"{type(e).__name__}: {e}")


# ── Resources (Skill content) ──────────────────────────────────────────────────

@server.list_resources()
async def list_resources() -> list[types.Resource]:
    resources = []
    for skill in _list_skills():
        resources.append(
            types.Resource(
                uri=skill["uri"],
                name=skill["name"],
                description=f"DataFlow Skill: {skill['name']}",
                mimeType="text/markdown",
            )
        )
    return resources


@server.read_resource()
async def read_resource(uri: types.AnyUrl) -> str:
    uri_str = str(uri)
    # skill://generating-dataflow-pipeline → generating-dataflow-pipeline/SKILL.md
    if uri_str.startswith("skill://"):
        rel_dir = uri_str[len("skill://"):]
        for suffix in ("SKILL.md", "SKILL_zh.md"):
            content = _read_skill(f"{rel_dir}/{suffix}")
            if not content.startswith("[File not found"):
                return content
    return f"Resource not found: {uri_str}"


# ── Entry point ────────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
