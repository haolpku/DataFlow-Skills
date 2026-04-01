# DataFlow-Skills

Reusable agent skills for DataFlow workflows.

中文文档: [README_zh.md](./README_zh.md)

## Skills

### [`generating-dataflow-pipeline`](./generating-dataflow-pipeline/README.md)

Reasoning-guided pipeline planner that generates standard DataFlow pipeline code. Given a business target and a JSONL sample file, it selects from six core operator primitives, validates field dependencies, and outputs a complete executable Python pipeline.

Entry: `/generating-dataflow-pipeline`

### [`dataflow-operator-builder`](./dataflow-operator-builder/README.md)

Production-grade scaffold skill for new DataFlow operators (`generate/filter/refine/eval`). Generates a complete operator implementation, CLI wrapper, and baseline tests (`unit/registry/smoke`) from a JSON spec, so you can focus on business logic instead of boilerplate.

Entry: `/dataflow-operator-builder`

### [`prompt-template-builder`](./prompt-template-builder/README.md)

Production-oriented skill for building/revising DataFlow prompt templates for existing operators. Checks operator compatibility, picks the right template style (`DIYPromptABC` / `FormatStrPrompt`), and returns auditable two-stage outputs (decision JSON + final deliverable).

Entry: `/prompt-template-builder`

### [`core_text`](./core_text/README.md)

Extended operator reference for [`generating-dataflow-pipeline`](./generating-dataflow-pipeline/README.md). Documents all 18 text processing operators across four categories: **generate** (8), **filter** (3), **refine** (2), **eval** (5). The pipeline generator consults these references when it needs operator details beyond the 6 core primitives.
