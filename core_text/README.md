# core_text

[← Back to DataFlow-Skills](../README.md) | 中文: [README_zh.md](./README_zh.md)

Extended operator reference for [`generating-dataflow-pipeline`](../generating-dataflow-pipeline/README.md).

## What is this

Per-operator API documentation for all text processing operators used by the pipeline generator. When the 6 core primitives in `generating-dataflow-pipeline/SKILL.md` don't cover your task, consult the detailed references here.

## Available Operators

**Generate** (`generate/`)

- `prompted-generator` - Basic LLM generation
- `format-str-prompted-generator` - Template-based generation
- `chunked-prompted-generator` - Chunked text generation
- `embedding-generator` - Generate embeddings
- `retrieval-generator` - RAG generation
- `bench-answer-generator` - Generate benchmark answers
- `text2multihopqa-generator` - Multi-hop QA generation
- `random-domain-knowledge-row-generator` - Random domain knowledge generation

**Filter** (`filter/`)

- `prompted-filter` - LLM scoring and filtering
- `general-filter` - Rule-based numeric filtering
- `kcentergreedy-filter` - Diversity-based filtering

**Refine** (`refine/`)

- `prompted-refiner` - LLM-based text rewriting
- `pandas-operator` - Custom pandas operations

**Eval** (`eval/`)

- `prompted-evaluator` - LLM scoring
- `bench-dataset-evaluator` - Evaluate benchmark datasets
- `bench-dataset-evaluator-question` - Evaluate benchmark questions
- `text2qa-sample-evaluator` - Evaluate QA samples
- `unified-bench-dataset-evaluator` - Unified evaluation

## How to use

These references are consulted by `generating-dataflow-pipeline` when generating pipeline code. Each operator folder contains:

- `SKILL.md` - English skill documentation describing use cases, usage, imports, parameters, and examples
- `SKILL_zh.md` - Chinese documentation
- `examples/good.md` - Correct usage with simple single-operator pipeline, sample input and output
- `examples/bad.md` - Common mistakes
