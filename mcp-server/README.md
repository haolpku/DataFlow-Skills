# DataFlow WebUI MCP Server

An MCP (Model Context Protocol) server that connects **Claude Code**, **Cursor**, and other MCP-compatible AI editors to **DataFlow WebUI**, enabling agents to:

- Discover available datasets, operators, and pipelines
- Create and execute DataFlow pipelines directly from AI conversations
- Access DataFlow Skill documentation as MCP resources

---

## Quick Start

### 1. Install dependencies

```bash
cd DataFlow-Skills/mcp-server
pip install -r requirements.txt
```

### 2. Start DataFlow WebUI backend

```bash
cd DataFlow-WebUI/backend
uvicorn app.main:app --reload --port 8000
```

### 3. Register MCP Server

**For Claude Code (global):**
```bash
python install.py --target claude
```

**For Cursor:**
```bash
python install.py --target cursor
```

**For both:**
```bash
python install.py --target both
```

**Custom WebUI URL:**
```bash
python install.py --target both --webui-url http://192.168.1.100:8000
```

### 4. Restart your editor

Restart Claude Code or Cursor to pick up the new MCP server configuration.

---

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `list_datasets` | List all registered datasets |
| `get_dataset_preview` | Preview sample rows from a dataset |
| `list_operators` | List all available DataFlow operators |
| `get_operator_details` | Get parameter schema for a specific operator |
| `list_pipelines` | List all saved pipelines |
| `get_pipeline` | Get full pipeline configuration |
| `create_pipeline` | Create a new pipeline in WebUI |
| `delete_pipeline` | Delete a pipeline |
| `execute_pipeline` | Execute a pipeline (synchronous) |
| `execute_pipeline_async` | Submit a pipeline for async execution |
| `get_task_status` | Poll execution status |
| `get_task_result` | Get sample results from completed task |
| `list_executions` | List all past executions |
| `list_servings` | List LLM serving configurations |
| `list_skills` | List available DataFlow Skills |
| `get_skill_content` | Read a specific Skill file |

## Available MCP Resources

Each DataFlow Skill is exposed as an MCP resource:

```
skill://generating-dataflow-pipeline     → SKILL.md
skill://dataflow-operator-builder        → SKILL.md
skill://prompt-template-builder          → SKILL.md
skill://dataflow-dev                     → SKILL.md
skill://core_text/generate/prompted-generator → SKILL.md
... (all 22 skills)
```

---

## End-to-End Agent Workflow (Claude Code)

With the MCP server registered and Skills installed, Claude Code can run full DataFlow workflows:

```
/generating-dataflow-pipeline
Target: Generate product descriptions and filter by quality score ≥ 4
Sample file: ./data/products.jsonl
```

After generating the pipeline code, the agent can:

```
[Claude Code continues]
> Use create_pipeline to save this to WebUI with dataset "products_ds_001"
> Use execute_pipeline to run it
> Use get_task_result to preview the output
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATAFLOW_WEBUI_URL` | `http://localhost:8000` | WebUI backend URL |
| `DATAFLOW_SKILLS_PATH` | Parent directory of `mcp-server/` | Path to DataFlow-Skills root |

---

## Manual MCP Configuration

If the install script doesn't work, add this to your config manually:

**Claude Code** (`~/.claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "dataflow-webui": {
      "command": "python",
      "args": ["/absolute/path/to/DataFlow-Skills/mcp-server/server.py"],
      "env": {
        "DATAFLOW_WEBUI_URL": "http://localhost:8000",
        "DATAFLOW_SKILLS_PATH": "/absolute/path/to/DataFlow-Skills"
      }
    }
  }
}
```

**Cursor** (`settings.json`):
```json
{
  "mcp": {
    "servers": {
      "dataflow-webui": {
        "command": "python",
        "args": ["/absolute/path/to/DataFlow-Skills/mcp-server/server.py"],
        "env": {
          "DATAFLOW_WEBUI_URL": "http://localhost:8000",
          "DATAFLOW_SKILLS_PATH": "/absolute/path/to/DataFlow-Skills"
        }
      }
    }
  }
}
```
