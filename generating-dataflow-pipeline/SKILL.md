---
name: generating-dataflow-pipeline
description: Reasoning-guided pipeline planner that generates standard DataFlow pipeline code
version: 1.0.0
---

# DataFlow Pipeline Code Generator

## Goal

This skill is used when users provide:
- **Target**: What the pipeline should achieve
- **Sample Data File**: Path to a JSONL file containing 1-5 representative data samples

The skill must:
1. **Read and analyze the JSONL file** at the provided path
2. Infer data structure, field types, and content characteristics
3. Determine task type based on file content (document processing, text transformation, multi-field composition)
4. Select appropriate operators from preferred primitives
5. Validate field dependencies
6. Output intermediate operator decision summary
7. Generate standard DataFlow pipeline code with `first_entry_file_name` set to the user-provided file path

## User Input Format

Users provide:
```
Target: [Clear task description]
Sample file: [Path to JSONL file, e.g., ./data/input.jsonl]
Expected outputs: [Optional field list]
```

**Important**: The sample file is a JSONL file (one JSON object per line), not a JSON array.

## Preferred Operator Strategy

**Six Core Primitives** (high-coverage operators for most data science tasks):
1. `PromptedGenerator` - Single-field LLM generation
2. `FormatStrPromptedGenerator` - Multi-field template generation
3. `Text2MultiHopQAGenerator` - Multi-hop QA pair construction
4. `PromptedFilter` - LLM-based quality filtering
5. `GeneralFilter` - Rule-based filtering
6. KBC trio (always used together in order): `FileOrURLToMarkdownConverterFlash` → `KBCChunkGenerator` → `KBCTextCleaner`

These are **preferred primitives**, not fixed workflows. They can be used repeatedly and combined flexibly.

## Operator Selection Priority Rule (MANDATORY)

When a specialized operator exists for the task, it MUST be used over generic operators. Do NOT use `PromptedGenerator` to replicate functionality that a dedicated operator already provides.

**Decision table** (check in order, use the first match):

| Task / Scenario | Required Operator | Do NOT use |
|---|---|---|
| Generate QA pairs from text | `Text2MultiHopQAGenerator` | `PromptedGenerator` with QA prompt |
| Convert file path / URL to text | KBC trio (`FileOrURLToMarkdownConverterFlash` → `KBCChunkGenerator` → `KBCTextCleaner`) | `PromptedGenerator` to summarize files |
| Score / evaluate using multiple fields | `FormatStrPromptedGenerator` + `GeneralFilter` | `PromptedFilter` (single input_key only) |
| Filter by deterministic rule on existing fields | `GeneralFilter` | `PromptedFilter` |
| Generate new content from a single field | `PromptedGenerator` | — |
| Generate new content from multiple fields | `FormatStrPromptedGenerator` | Multiple `PromptedGenerator` steps |

**Key principle**: `PromptedGenerator` is the fallback for generic single-field generation. If the target mentions "QA", "question-answer", "问答" — always reach for `Text2MultiHopQAGenerator` first.

## Field Dependency Rules (MANDATORY)

1. **Inspect sample first**: Identify all available fields in user's sample data
2. **Field existence check**: If step N needs field X, then X must exist in original sample OR be output by step M where M < N
3. **Generate missing fields**: Use `PromptedGenerator` or `FormatStrPromptedGenerator` to create missing semantic fields
4. **Never reference before creation**: Cannot consume a field before it exists
5. **Avoid overwriting**: Do not overwrite original user fields unless explicitly requested

```
✗ WRONG: Filter by "quality_score" before generating it
✓ CORRECT: Generate "quality_score" first, then filter by it
```

## Prompted Operator Usage Policy (MANDATORY)

- Don't mechanically create one prompted operator per tiny requirement. If one operator can handle multiple related transformations, prefer that over splitting.
- Multiple prompted operators are allowed when the task genuinely requires distinct semantic transformations. If using multiple, justify each step's role, input field, and output field.

## KBC Usage Constraint (MANDATORY)

The KBC trio must always be used in this exact order:
1. `FileOrURLToMarkdownConverterFlash` — converts file path / URL → Markdown text (field: `text_path`)
2. `KBCChunkGenerator` — splits Markdown into chunks (field: `raw_chunk`)
3. `KBCTextCleaner` — LLM-cleans each chunk (field: `cleaned_chunk`)

Rules:
- All three steps are required; never skip one.
- Input to step 1 must be a file path or URL, never plain text content.
- Each step's `output_key` becomes the next step's `input_key`.
- Use the default field names (`text_path`, `raw_chunk`, `cleaned_chunk`) unless explicitly requested otherwise.

## GeneralFilter Field Safety Rule (MANDATORY)

`GeneralFilter` lambda rules must ONLY reference fields that exist in sample data or are produced by upstream steps.

## Multi-Field Filtering Pattern (MANDATORY)

`PromptedFilter` only accepts a single `input_key`. For multi-field evaluation (e.g., scoring QA pairs), use `FormatStrPromptedGenerator` to score + `GeneralFilter` to filter.

**Important caveat for `Text2MultiHopQAGenerator` output**: The `QA_pairs` column is a nested list of dicts, not separate `question`/`answer` columns. You **cannot** directly pass `question` or `answer` as kwargs to `FormatStrPromptedGenerator` after `Text2MultiHopQAGenerator`. To score or filter individual QA pairs, use **post-processing** (explode the list into rows, then optionally score/filter in a second pipeline or in Python code).

## Output Contract (MANDATORY)

**Two-stage output required**:

### Stage 1: Intermediate Operator Decision (JSON)
Output this first:
```json
{
  "ops": ["OperatorA", "OperatorB", "OperatorC"],
  "field_flow": "field_a -> field_b -> field_c",
  "reason": "Why this ordered operator chain satisfies the target, how field dependencies are satisfied, and why prompted operators are or are not used."
}
```

### Stage 2: Complete Response (5 sections)
1. **Field Mapping**: Map sample fields to semantic roles, identify fields to generate
2. **Ordered Operator List**: List operators in execution order with justification
3. **Reasoning Summary**: Explain operator selection, field flow, why this design
4. **Complete Standard Pipeline Code**: Full executable Python following repository style
5. **Adjustable Parameters / Caveats**: Tunable parameters, fallback strategies, debugging tips

## Standard Code Generation Rule (MANDATORY)

**All generated Python code must follow the standard pipeline organization shown in the `examples/` folder of this skill package.**

**Input Data Format**:
- `first_entry_file_name` MUST be set to the **user-provided file path** (the JSONL sample file)
- File extension must be `.jsonl` (one JSON object per line, NOT an array)
- **DO NOT create new file paths** - use the exact path the user provided

**Required structure**: `__init__` (storage + llm_serving + operators) → `forward` (sequential `operator.run(storage=self.storage.step(), ...)`) → `if __name__ == "__main__"` entry point.

**DO NOT**: generate custom runtime executors, `forward(plan)` style frameworks, or dynamic dispatch engines.

## Operator Parameter Signature Rule (MANDATORY)

Use repository-valid constructor/run signatures only. Never invent parameter names.

### Base Components

**`FileStorage`**
```python
FileStorage(
  first_entry_file_name="...jsonl",
  cache_path="./cache",
  file_name_prefix="dataflow_cache_step",
  cache_type="jsonl"
)
```

**`APILLMServing_request`**
```python
APILLMServing_request(
  api_url="...",
  key_name_of_api_key="DF_API_KEY",  # defaults to DF_API_KEY; set to e.g. "OPENAI_API_KEY" if needed
  model_name="gpt-4o",
  max_workers=10
)
```

### Six Core Operators: Signatures + Key Requirements

**1) `PromptedGenerator`**
- Constructor: `PromptedGenerator(llm_serving, system_prompt="You are a helpful agent.", user_prompt="", json_schema=None)`
- Run: `run(storage=self.storage.step(), input_key="raw_content", output_key="generated_content")`
- `input_key` column must exist. Generated rows written to `output_key`.

**2) `FormatStrPromptedGenerator`**
- Constructor: `FormatStrPromptedGenerator(llm_serving, system_prompt="You are a helpful agent.", prompt_template=FormatStrPrompt(...), json_schema=None)`
- Run: `run(storage=self.storage.step(), output_key="generated_content", **input_keys)`
- `**input_keys`: each kwarg maps a **template variable name** (key) to a **dataframe column name** (value). Internally does `row[input_keys[key]]` per row, then `prompt_template.build_prompt(need_fields, **key_dict)`.
- Kwarg keys must match `{placeholder}` names in `FormatStrPrompt.f_str_template`. Kwarg values must be existing dataframe columns.
- `prompt_template` cannot be `None` (raises `ValueError`). Must pass an instantiated `FormatStrPrompt(f_str_template="...")`.
- Import: `from dataflow.prompts.core_text import FormatStrPrompt`

**3) `Text2MultiHopQAGenerator`**
- Constructor: `Text2MultiHopQAGenerator(llm_serving=self.llm_serving, seed=0, lang="en", prompt_template=None, num_q=5)`
  - `llm_serving` — LLM serving instance (required)
  - `seed` (int, default `0`) — random seed for reproducibility
  - `lang` (str, default `"en"`) — language for generation prompt; controls sentence splitting (`"."` for `"en"`, `"。"` for `"zh"`)
  - `prompt_template` — custom `DIYPromptABC` instance; pass `None` to use default `Text2MultiHopQAGeneratorPrompt`
  - `num_q` (int, default `5`) — **maximum** number of QA pairs to **keep** per input row (truncates the generated list; actual generation count depends on sentence triples in the text)
- Run: `run(storage, input_key="cleaned_chunk", output_key="QA_pairs", output_meta_key="QA_metadata")`
  - `input_key` must exist (cleaned text chunk column)
  - `output_key` — column containing a **nested list** of QA dicts per row. Each dict has keys: `question` (str), `reasoning_steps` (list of `{step: str}`), `answer` (str), `supporting_facts` (list of str), `type` (str)
  - `output_meta_key` — column containing metadata dict per row with keys: `source`, `timestamp`, `complexity`
  - Output column named by `output_key` / `output_meta_key` must NOT pre-exist.
- Each input row produces **one row** with a nested list in the `output_key` column. The list items are dicts — `question`, `answer`, etc. are **NOT** separate dataframe columns. Downstream operators like `FormatStrPromptedGenerator` cannot directly reference `question` or `answer` as column names. To use individual QA pairs downstream, you must **post-process** (explode the list into separate rows) outside the operator chain.
- **Input text constraints** (texts failing these checks produce empty `qa_pairs: []`):
  - Length: 100–200,000 characters
  - Must contain at least 2 sentences (2+ `.` or 2+ `。`)
  - Special character ratio must be ≤ 30%

**4) `PromptedFilter`**
- Constructor: `PromptedFilter(llm_serving, system_prompt="...", min_score=1, max_score=5)`
- Run: `run(storage=self.storage.step(), input_key="raw_content", output_key="eval")`
- `input_key` must exist. `output_key` is numeric score column; rows outside `[min_score, max_score]` are filtered out.

**5) `GeneralFilter`**
- Constructor: `GeneralFilter([lambda df: df["score"] >= 4, ...])`
- Run: `run(storage=self.storage.step())`
- Each rule must return boolean `pd.Series`. Referenced fields must already exist.

**6) KBC Trio (always used in this order)**

**Step 1 — `FileOrURLToMarkdownConverterFlash`**
- Constructor: `FileOrURLToMarkdownConverterFlash(intermediate_dir="../example_data/KBCleaningPipeline/flash/", mineru_model_path="opendatalab/MinerU2.5-2509-1.2B", batch_size=4, replicas=1, num_gpus_per_replica=1.0, engine_gpu_util_rate_to_ray_cap=0.9)`
- **Does NOT take `llm_serving`** — this operator has no LLM dependency.
- `mineru_model_path` is **required** — passing `None` raises `ValueError`. Use a HuggingFace model ID or local path.
- Run: `run(storage=self.storage.step(), input_key="source", output_key="text_path")`
- Input must be a file path or URL (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.html`, `.xml`, `.txt`, `.md`).

**Step 2 — `KBCChunkGenerator`**
- Constructor: `KBCChunkGenerator(chunk_size=512, chunk_overlap=50, split_method="token", min_tokens_per_chunk=100, tokenizer_name="bert-base-uncased")`
- Run: `run(storage=self.storage.step(), input_key="text_path", output_key="raw_chunk")`
- `split_method` options: `"token"`, `"sentence"`, `"semantic"`, `"recursive"`.

**Step 3 — `KBCTextCleaner`**
- Constructor: `KBCTextCleaner(llm_serving, lang="en")`
- Run: `run(storage=self.storage.step(), input_key="raw_chunk", output_key="cleaned_chunk")`
- LLM-cleans each chunk; output is ready for downstream QA generation.

### Correct Import Paths (MANDATORY)

```python
# Base components
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request

# Operators
from dataflow.operators.core_text import PromptedGenerator, FormatStrPromptedGenerator, Text2MultiHopQAGenerator, PromptedFilter, GeneralFilter
from dataflow.operators.knowledge_cleaning import FileOrURLToMarkdownConverterFlash, KBCChunkGenerator, KBCTextCleaner
```

## Input File Content Analysis Rule (MANDATORY)

Analyze sample data content to determine task nature:

**File path fields** (e.g., `pdf_path`, `image_path`, `doc_path`):
- → KBC trio in order: `FileOrURLToMarkdownConverterFlash` → `KBCChunkGenerator` → `KBCTextCleaner` (supports `.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.html`, `.xml`, `.txt`, `.md`)
- → Document/file processing workflow

**Plain text fields** (e.g., `text`, `content`, `review_text`):
- → Use `PromptedGenerator`, `PromptedFilter`, `Text2MultiHopQAGenerator`, `FormatStrPromptedGenerator`, `GeneralFilter`
- → Do NOT use KBC

**Multiple semantic fields** (e.g., `instruction`, `output`, `question`, `answer`):
- → Use `FormatStrPromptedGenerator` for combining fields
- → Use `GeneralFilter` for field-based rules

## Examples

See `examples/` folder for complete workflows:

1. **`examples/basic_generate_and_filter.md`** — `PromptedGenerator` + `PromptedFilter` (simplest pattern)
2. **`examples/multifield_scoring.md`** — `FormatStrPromptedGenerator` with multi-field scoring
3. **`examples/multi_stage_pipeline.md`** — Multiple `PromptedGenerator` stages + `GeneralFilter`
4. **`examples/kbc_pdf_to_qa.md`** — KBC trio (`FileOrURLToMarkdownConverterFlash` + `KBCChunkGenerator` + `KBCTextCleaner`) + `Text2MultiHopQAGenerator` + `PromptedFilter` (scores nested QA_pairs column per chunk)

These are strategy guidance, not templates to copy blindly. Generated code must follow standard pipeline structure.
