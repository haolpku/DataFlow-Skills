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
3. `Text2QAGenerator` - QA pair construction
4. `PromptedFilter` - LLM-based quality filtering
5. `GeneralFilter` - Rule-based filtering
6. `KBCCompositeCleaningFlashOperator` - PDF→Markdown→Chunks→Cleaned

These are **preferred primitives**, not fixed workflows. They can be used repeatedly and combined flexibly.

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

`KBCCompositeCleaningFlashOperator` input must be a file path or URL. Do NOT use it on plain text content.

## GeneralFilter Field Safety Rule (MANDATORY)

`GeneralFilter` lambda rules must ONLY reference fields that exist in sample data or are produced by upstream steps.

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

**3) `Text2QAGenerator`**
- Constructor: `Text2QAGenerator(llm_serving=self.llm_serving)` (only parameter)
- Run: `run(storage, input_key="text", input_question_num=1, output_prompt_key="generated_prompt", output_question_key="generated_question", output_answer_key="generated_answer")`
- `input_key` must exist; columns named by `output_question_key` / `output_answer_key` must NOT pre-exist (raises `ValueError`).
- Performs two LLM calls internally. Each input row expands into `min(input_question_num, actual_prompt_count)` rows.

**4) `PromptedFilter`**
- Constructor: `PromptedFilter(llm_serving, system_prompt="...", min_score=1, max_score=5)`
- Run: `run(storage=self.storage.step(), input_key="raw_content", output_key="eval")`
- `input_key` must exist. `output_key` is numeric score column; rows outside `[min_score, max_score]` are filtered out.

**5) `GeneralFilter`**
- Constructor: `GeneralFilter([lambda df: df["score"] >= 4, ...])`
- Run: `run(storage=self.storage.step())`
- Each rule must return boolean `pd.Series`. Referenced fields must already exist.

**6) `KBCCompositeCleaningFlashOperator`**
- Constructor: `KBCCompositeCleaningFlashOperator(llm_serving, intermediate_dir="...", mineru_model_path=None, chunk_size=512, chunk_overlap=50, lang="en")`
- Run: `run(storage=self.storage.step(), input_key="source", output_key="cleaned_chunk")`
- Internal chain: input_key → `text_path` → `raw_chunk` → `output_key`. Input must be file path/URL.

### Correct Import Paths (MANDATORY)

```python
from dataflow.operators.core_text import PromptedGenerator, FormatStrPromptedGenerator, Text2QAGenerator, PromptedFilter, GeneralFilter
from dataflow.operators.knowledge_cleaning import KBCCompositeCleaningFlashOperator
```

## Input File Content Analysis Rule (MANDATORY)

Analyze sample data content to determine task nature:

**File path fields** (e.g., `pdf_path`, `image_path`, `doc_path`):
- → `KBCCompositeCleaningFlashOperator` (supports `.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.html`, `.xml`, `.txt`, `.md`)
- → Document/file processing workflow

**Plain text fields** (e.g., `text`, `content`, `review_text`):
- → Use `PromptedGenerator`, `PromptedFilter`, `Text2QAGenerator`, `FormatStrPromptedGenerator`, `GeneralFilter`
- → Do NOT use KBC

**Multiple semantic fields** (e.g., `instruction`, `output`, `question`, `answer`):
- → Use `FormatStrPromptedGenerator` for combining fields
- → Use `GeneralFilter` for field-based rules

## Examples

See `examples/` folder for complete workflows:

1. **`examples/basic_generate_and_filter.md`** — `PromptedGenerator` + `PromptedFilter` (simplest pattern)
2. **`examples/multifield_scoring.md`** — `FormatStrPromptedGenerator` with multi-field scoring
3. **`examples/multi_stage_pipeline.md`** — Multiple `PromptedGenerator` stages + `GeneralFilter`
4. **`examples/kbc_pdf_to_qa.md`** — `KBCCompositeCleaningFlashOperator` + `Text2QAGenerator` + `PromptedFilter`

These are strategy guidance, not templates to copy blindly. Generated code must follow standard pipeline structure.
