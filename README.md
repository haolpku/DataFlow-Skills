# DataFlow-Skills

Reusable [Claude Code skills](https://code.claude.com/docs/en/skills) for working with the [DataFlow](https://github.com/OpenDCAI/DataFlow) data-processing framework.

中文文档：[README_zh.md](./README_zh.md)

---

## What's in here

Three skills, each loaded by Claude Code from `~/.claude/skills/<name>/SKILL.md`:

| Skill | What it does | Invoke with |
|---|---|---|
| **`generating-dataflow-pipeline`** | From a target description + a sample JSONL file, plan the operator chain and emit a runnable DataFlow pipeline. | `/generating-dataflow-pipeline` |
| **`dataflow-dev`** | DataFlow developer assistant. Loads architecture knowledge, routes intents (new operator / new pipeline / new prompt / diagnose error / code review / KB sync) into the right workflow. Run inside a DataFlow repo. | `/dataflow-dev` |
| **`core_text`** | Per-operator API reference (8 generators, 3 filters, 2 refiners, 5 evaluators) consulted by the pipeline skill when it needs operators beyond the 6 core primitives. **No direct invocation** — it's documentation the other skills read. | _(not directly invoked)_ |

---

## Install

**Prerequisite:** Claude Code CLI on your `PATH`. If not yet installed, see [docs/install-claude-code.md](./docs/install-claude-code.md).

```bash
git clone https://github.com/haolpku/DataFlow-Skills.git
cd DataFlow-Skills
./install.sh
```

That copies all three skills into `~/.claude/skills/` (user-level — available in every project). Then in any Claude Code session:

```
/generating-dataflow-pipeline
```

If the slash command shows up in completion, you're done.

### Install options

```bash
./install.sh --project                       # install into ./.claude/skills/ instead of ~/.claude/skills/
./install.sh dataflow-dev                    # install only the named skill(s)
./install.sh --force                         # overwrite existing skills (default: skip)
./install.sh --help
```

### Update

```bash
cd DataFlow-Skills
git pull
./install.sh --force
```

---

## Quick tour

### `generating-dataflow-pipeline`

Video: [Generate DataFlow Pipeline](https://github.com/user-attachments/assets/ca1fefbf-9bf7-469f-b856-b201952fb99b)

Give it a target and 1–5 sample rows; it returns an operator decision (JSON) followed by a complete pipeline `.py`.

```text
/generating-dataflow-pipeline
Target: Generate product descriptions and filter high-quality ones
Sample file: ./data/products.jsonl
Expected outputs: generated_description, quality_score
```

The 6 core primitives it picks from: `PromptedGenerator`, `FormatStrPromptedGenerator`, `Text2MultiHopQAGenerator`, `PromptedFilter`, `GeneralFilter`, and the **KBC trio** (`FileOrURLToMarkdownConverterFlash` → `KBCChunkGenerator` → `KBCTextCleaner`). When these aren't enough it cross-references the `core_text` skill for extended operators. Full rules and the generated pipeline schema live in [`generating-dataflow-pipeline/SKILL.md`](./generating-dataflow-pipeline/SKILL.md).

### `dataflow-dev`

Run it inside a clone of the DataFlow repo. It loads the knowledge base, probes git state, and routes by intent:

| Say something like… | Workflow |
|---|---|
| "new filter operator that…" | Operator creation (duplicate check → spec → code + registration reminder) |
| "new pipeline that…" | Pipeline creation with the standard `storage.step()` pattern |
| "new prompt for X" | Prompt creation (`PromptABC` / `DIYPromptABC`, `@prompt_restrict` placement) |
| "I'm getting `KeyError: …`" | Diagnose against `diagnostics/known_issues.md` (#001–#008) |
| "review this operator" | 14-point checklist (registry, `run()` signature, `get_desc`, etc.) |
| "the upstream repo has new operators" | Compare local files to `knowledge_base.md`, emit update steps |

Details: [`dataflow-dev/SKILL.md`](./dataflow-dev/SKILL.md). Aligned to [OpenDCAI/DataFlow](https://github.com/OpenDCAI/DataFlow) `main` (v1.0.10).

### `core_text`

Reference docs only — `SKILL.md`, `SKILL_zh.md`, `examples/good.md`, `examples/bad.md` per operator. Browse: [`core_text/`](./core_text/).

---

## Adding your own operator skill

1. Drop a `core_text/<category>/<your-operator>/` directory with `SKILL.md` + `examples/{good,bad}.md`.
2. Register it in the appropriate table inside [`generating-dataflow-pipeline/SKILL.md`](./generating-dataflow-pipeline/SKILL.md) under "Extended Operator Reference" — without that row the pipeline planner can't see it.

If the operator becomes a high-frequency primitive, promote it by editing the same file's "Operator Selection Priority Rule", "Operator Parameter Signature Rule", "Correct Import Paths", and (if it handles a new data type) "Input File Content Analysis Rule" sections.

---

## Repository layout

```
DataFlow-Skills/
├── install.sh                       # one-shot installer (cp -r into ~/.claude/skills/)
├── docs/
│   └── install-claude-code.md       # CC CLI install guide
├── generating-dataflow-pipeline/    # pipeline planner skill
├── dataflow-dev/                    # DataFlow dev assistant skill
└── core_text/                       # extended operator reference
    ├── generate/
    ├── filter/
    ├── refine/
    └── eval/
```

---

## Upstream

All knowledge bases in this repo are aligned to **[OpenDCAI/DataFlow](https://github.com/OpenDCAI/DataFlow)** `main` (v1.0.10).
