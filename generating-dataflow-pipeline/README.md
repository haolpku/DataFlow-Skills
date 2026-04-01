# generating-dataflow-pipeline

[← Back to DataFlow-Skills](../README.md) | 中文版: [README_zh.md](./README_zh.md)

Reasoning-guided pipeline planner that generates standard DataFlow pipeline code from a task description and sample data.

## What It Does

Given a **target** (what the pipeline should achieve) and a **sample JSONL file** (1-5 representative rows), this skill:

1. Reads and analyzes the sample data — infers field types, content characteristics, and task nature
2. Selects operators from six core primitives using a mandatory decision table
3. Validates field dependencies across the operator chain
4. Outputs a two-stage result: an intermediate operator decision (JSON) followed by a complete, runnable Python pipeline

## Quick Start

Provide your request in this format:

```
Target: Generate product descriptions and filter high-quality ones
Sample file: ./data/products.jsonl
Expected outputs: generated_description, quality_score
```

The sample file must be **JSONL** (one JSON object per line), not a JSON array:

```jsonl
{"product_name": "Laptop", "category": "Electronics"}
{"product_name": "Coffee Maker", "category": "Appliances"}
```

The skill returns:

1. **Intermediate Operator Decision** — JSON with operator chain, field flow, and reasoning
2. **Field Mapping** — which fields exist vs. need to be generated
3. **Ordered Operator List** — operators in execution order with justification
4. **Reasoning Summary** — why this design satisfies the target
5. **Complete Pipeline Code** — full executable Python following standard structure
6. **Adjustable Parameters / Caveats** — tunable knobs and debugging tips

## Six Core Operators

| Operator | Purpose | LLM? |
|----------|---------|------|
| `PromptedGenerator` | Single-field LLM generation | Yes |
| `FormatStrPromptedGenerator` | Multi-field template-based generation | Yes |
| `Text2MultiHopQAGenerator` | Multi-hop QA pair construction from text | Yes |
| `PromptedFilter` | LLM-based quality scoring & filtering | Yes |
| `GeneralFilter` | Rule-based deterministic filtering | No |
| **KBC Trio** (3 operators, always together in order) | File/URL -> Markdown -> chunks -> clean text | Partial |

### Operator Selection Priority

The skill follows a mandatory decision table — specialized operators always override generic ones:

- **QA pairs from text** -> `Text2MultiHopQAGenerator` (not `PromptedGenerator` with a QA prompt)
- **File path / URL to text** -> KBC trio (not `PromptedGenerator` to summarize files)
- **Score using multiple fields** -> `FormatStrPromptedGenerator` + `GeneralFilter` (not `PromptedFilter`, which only takes a single `input_key`)
- **Deterministic rule filtering** -> `GeneralFilter` (not `PromptedFilter`)
- **Generate from multiple fields** -> `FormatStrPromptedGenerator` (not multiple `PromptedGenerator` steps)

## Generated Pipeline Structure

All generated pipelines follow the same standard structure:

```python
from dataflow.operators.core_text import PromptedGenerator, PromptedFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",  # User-provided path
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )
        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )
        # Operator instances ...

    def forward(self):
        # Sequential operator.run() calls, each with storage.step()
        ...

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

Key rules:
- `first_entry_file_name` is set to the exact user-provided JSONL path
- Each `operator.run()` call uses `storage=self.storage.step()` for checkpointing
- Fields propagate forward: a field must exist in the sample or be output by a prior step before it can be consumed

## Examples

See the [`examples/`](./examples/) folder for complete workflows:

| Example | Pattern | Operators Used |
|---------|---------|----------------|
| [`basic_generate_and_filter.md`](./examples/basic_generate_and_filter.md) | Generate + quality filter | `PromptedGenerator` + `PromptedFilter` |
| [`multifield_scoring.md`](./examples/multifield_scoring.md) | Multi-field scoring | `FormatStrPromptedGenerator` + `GeneralFilter` |
| [`multi_stage_pipeline.md`](./examples/multi_stage_pipeline.md) | Multi-stage generation + filtering | Multiple `PromptedGenerator` + `GeneralFilter` |
| [`kbc_pdf_to_qa.md`](./examples/kbc_pdf_to_qa.md) | Document processing + QA extraction | KBC trio + `Text2MultiHopQAGenerator` + `PromptedFilter` |

## Extended Operators (core_text)

Beyond the 6 core primitives, DataFlow provides additional operators documented in the sibling [`core_text/`](../core_text/) skill. When the core primitives don't cover your task, consult these references:

**Generate** (`core_text/generate/`) — 8 operators:

| Operator | Description |
|----------|-------------|
| `PromptedGenerator` | Single-field LLM generation |
| `FormatStrPromptedGenerator` | Multi-field template generation |
| `Text2MultiHopQAGenerator` | Multi-hop QA pair extraction |
| `BenchAnswerGenerator` | Benchmark answer generation (`eval_type` variants) |
| `ChunkedPromptedGenerator` | Long document chunk-by-chunk processing |
| `EmbeddingGenerator` | Text vectorization (`/v1/embeddings`) |
| `RandomDomainKnowledgeRowGenerator` | Domain-specific synthetic row generation |
| `RetrievalGenerator` | Async RAG generation (`await run()`) |

**Filter** (`core_text/filter/`) — 3 operators:

| Operator | Description |
|----------|-------------|
| `GeneralFilter` | Rule-based row filtering (lambda conditions) |
| `KCenterGreedyFilter` | Diversity-based downsampling (requires embeddings) |
| `PromptedFilter` | LLM semantic scoring + filtering |

**Eval** (`core_text/eval/`) — 5 operators:

| Operator | Description |
|----------|-------------|
| `BenchDatasetEvaluator` | Benchmark answer comparison (`match` / `semantic`) |
| `BenchDatasetEvaluatorQuestion` | Extended benchmark evaluator with question context |
| `PromptedEvaluator` | LLM-based row scoring (writes score, no row removal) |
| `Text2QASampleEvaluator` | QA quality evaluation (4 dimensions, 8 output columns) |
| `UnifiedBenchDatasetEvaluator` | Unified benchmark evaluation (6 `eval_type` variants) |

**Refine** (`core_text/refine/`) — 2 operators:

| Operator | Description |
|----------|-------------|
| `PandasOperator` | Custom DataFrame transformation (no LLM) |
| `PromptedRefiner` | LLM text refinement (overwrites original column) |

Each operator directory contains `SKILL.md` (English API reference), `SKILL_zh.md` (Chinese), `examples/good.md` and `examples/bad.md`.

## Adding a New Operator

Prerequisite: the new operator's skill definition already exists (with `SKILL.md`, `examples/good.md`, `examples/bad.md`, etc.).

### As an Extended Operator

Two steps are required:

**Step 1.** Create an operator directory with its skill definition under any appropriate location (e.g., `core_text/<category>/`, or a separate skill package):

```
<skill-directory>/<your-operator-name>/
├── SKILL.md          # API reference (constructor, run() signature, execution logic, constraints)
├── SKILL_zh.md       # Chinese translation (optional)
└── examples/
    ├── good.md       # Best-practice example
    └── bad.md        # Common mistakes
```

**Step 2.** Register the operator in `SKILL.md`'s **Extended Operator Reference** section. Add a row to the corresponding category table (Generate / Filter / Refine / Eval) with the operator name, subdirectory path, and description. Without this entry, the pipeline generator will not know the operator exists.

### Promoting to a Core Primitive (Optional)

If the operator is used frequently enough to warrant priority selection, promote it by modifying `SKILL.md`:

1. **Preferred Operator Strategy** — Add to the core primitives list
2. **Operator Selection Priority Rule** — Add a decision table row (when to use / when not to use)
3. **Operator Parameter Signature Rule** — Add full constructor and `run()` signatures
4. **Correct Import Paths** — Add the import path
5. **Input File Content Analysis Rule** — Add input pattern matching if it handles a new data type
6. **Examples** — Add a complete example in `examples/` (recommended)

## Key Constraints

- **JSONL only**: Input must be `.jsonl` format, one JSON object per line
- **KBC trio is all-or-nothing**: All three steps (`FileOrURLToMarkdownConverterFlash` -> `KBCChunkGenerator` -> `KBCTextCleaner`) must be used in exact order; never skip one
- **`Text2MultiHopQAGenerator` outputs nested lists**: The `QA_pairs` column contains a list of dicts per row, not separate columns — downstream operators cannot directly reference `question` or `answer` as column names
- **`PromptedFilter` is single-field**: For multi-field evaluation, use `FormatStrPromptedGenerator` to score + `GeneralFilter` to filter
- **Field safety**: `GeneralFilter` lambdas must only reference fields that already exist
