---
name: generating-dataflow-pipeline
description: |
  Complete DataFlow pipeline construction skill for code agents (v2, designed from observed agent behavior).
  Trigger when the user asks to: build / design / create / optimize a DataFlow pipeline from a dataset and a natural-language target.
  Covers: operator discovery via MCP, operator selection, field dependency, serving configuration, pipeline schema, think-first protocol, output format.
version: 2.0.0
---

# DataFlow Pipeline Construction Skill

You help the user build a DataFlow pipeline. The input is (1) a JSONL sample path, (2) a natural-language target describing what the pipeline should produce. The output is a **stored pipeline object** visible in the WebUI DAG editor, runnable via the WebUI Run button.

## TL;DR protocol

```
1. list_servings                       — pick one serving id; if empty, stop and tell user
2. list_operator_categories            — cheap overview
3. Use the Category Cheat Sheet below to decide which categories to browse
4. list_operators(category=X)          — max 2 categories; never empty-arg
5. get_operator_detail_by_name(op)     — for each shortlisted candidate
6. Emit the `plan` JSON (think-first, see below)
7. create_pipeline(...)                — exactly once per user turn
8. render_pipeline_in_editor(pipeline_id)
9. STOP. Do not call execute_pipeline. The user runs via the WebUI.
```

---

## 1. Hard rules (always apply)

### R1. Dataset id is assigned by the backend

Never invent an `input_dataset.id`. The id is either (a) supplied in the user's instructions (use it verbatim), or (b) returned by `register_dataset` (use the `id` field, not the `name`).

### R2. LLM operators require a real `llm_serving` id

Before configuring any operator whose class starts with `Prompted`, `FormatStr`, `LLM`, `Text2`, `KBC`, `Retrieval`, `Embedding`, `Chunked`, or `BenchAnswer`:

1. Call `list_servings`.
2. If a serving exists, pass `llm_serving=<that id>` as an init param.
3. If `list_servings` returns empty, do **not** create the pipeline. Reply to the user: "Please register an LLM serving first via Settings → Serving, then try again."

### R3. `prompt_template` init arg is a class name or `None`, not a dict

For `PromptedGenerator`, `FormatStrPromptedGenerator`, `PromptedRefiner`, `PromptedEvaluator`, `PromptedFilter`:

- Preferred: set `system_prompt` (+ optional `user_prompt`) as plain strings; leave `prompt_template` unset (default None).
- Only set `prompt_template` if you are intentionally reusing a `DIYPromptABC` subclass (class name as string, e.g. `"AlpagasusPrompt"`).
- **Never** set `prompt_template = {"template": "..."}` — the backend does not accept dict-form prompt templates and the pipeline will fail at operator init.

### R4. Never reference a field before it exists

For each operator in order, every `input_key` / `input_keys` must either be present in the input sample or be an `output_key` of an earlier operator in the same pipeline.

### R5. Think-first, one create per turn

Emit the `plan` JSON below **before** any `create_pipeline` call. Call `create_pipeline` at most once; to refine, use `update_pipeline` on the same `pipeline_id`. After each create/update, call `render_pipeline_in_editor` exactly once.

```json
{
  "ops": ["OpA (core_text/generate)", "OpB (general_text/refine)", "OpC (core_text/filter)"],
  "field_flow": "sample_field -> produced_by_A -> produced_by_B -> filter_key",
  "serving_id": "<from list_servings, or null if task is deterministic>",
  "reason": "one paragraph: why this chain, why these operators, why deterministic-vs-LLM choice"
}
```

### R6. Do NOT execute

`execute_pipeline` and `execute_pipeline_async` are reserved for the user. The user clicks the Run button after visually inspecting the DAG. Only call them if the user explicitly says "run it now" in the current turn.

---

## 2. Operator discovery: mandatory three-step hierarchy

- `list_operator_categories` — first, cheap.
- `list_operators(category=<name>)` — **always with `category` argument**. Never with empty args (payload is ~90 KB and will overflow context). Do this for **at most 2 categories per turn**. If the Category Cheat Sheet below tells you which category to look at, go there directly.
- `get_operator_detail_by_name(op_name=<name>)` — for each candidate operator before writing pipeline code.

---

## 3. Category Cheat Sheet (use this to decide WHERE to look)

DataFlow has 14 top-level categories. For pipeline building tasks you will only need a few:

| If the task involves ... | Go to these categories (in order) |
| --- | --- |
| Generate new fields from text with an LLM (QA, summaries, classifications, explanations, scoring, rewriting) | **`core_text/generate`** first, then `core_text/refine` for LLM rewriting |
| Filter rows by an LLM judgment | **`core_text/filter`** |
| Filter rows by a deterministic rule on existing fields | **`core_text/filter`** (GeneralFilter) |
| Evaluate QA pairs specifically (nested qa_pairs field) | **`core_text/eval`** (Text2QASampleEvaluator) |
| Language detection / deduplication / toxicity / length / lexical-diversity filters | **`general_text/filter`** |
| Deterministic text cleaning: emoji, URL, HTML, punctuation, whitespace, lowercasing | **`general_text/refine`** |
| Field rename / flatten / derive deterministically (no LLM) | **`core_text/refine`** (PandasOperator) |
| PDF / URL → cleaned chunks for knowledge-base building | **`knowledge_cleaning`** (KBC* operators, requires `chonkie` and `trafilatura`) |
| Instruction-tuning / SFT data quality (Alpagasus, Deita) | `text_sft` |
| Math / code reasoning | `reasoning`, `code` |
| Conversation formatting | `conversations` |

Explicit anti-mappings (common agent mistakes from observed data):

- **QA generation from text chunks is NOT a text_sft task.** Do not look in `text_sft` for QA generation — it is in `core_text/generate` (`Text2MultiHopQAGenerator`, `Text2QAGenerator`).
- **Sentiment / classification is NOT a text_sft task.** It is `core_text/generate` with a `PromptedGenerator`.
- **Schema normalization (rename, flatten) is NOT an LLM task.** It is `core_text/refine` with `PandasOperator`.
- **"Normalization / clean text" when the task clearly describes deterministic patterns (emoji, URL, whitespace, HTML)** should go to `general_text/refine` first, not `core_text/refine/PromptedRefiner`. Only use `PromptedRefiner` when the cleaning needs understanding (paraphrase, style rewrite, semantic repair).

---

## 4. Operator selection patterns (reference table)

Each row: task pattern → first-choice operator → fallback → anti-pattern.

### 4.1 Generation

| Task | First choice | Fallback | Anti-pattern |
| --- | --- | --- | --- |
| Generate new content from ONE field | `PromptedGenerator` (core_text/generate) | — | Using FormatStrPromptedGenerator for a single field just to be fancy |
| Generate new content from MULTIPLE fields | `FormatStrPromptedGenerator` (core_text/generate) | Multiple `PromptedGenerator` steps with string concat (worse) | Chaining 3 PromptedGenerators when one FormatStr handles it |
| Generate multi-hop QA pairs from a text field | `Text2MultiHopQAGenerator` (core_text/generate) | `Text2QAGenerator` (single-hop) | `PromptedGenerator` with a QA prompt; `SFTGeneratorSeed` (wrong category) |
| Process very long text that exceeds LLM context | `ChunkedPromptedGenerator` (core_text/generate) | — | Passing the full doc into `PromptedGenerator` |
| Embedding generation | `EmbeddingGenerator` (core_text/generate) | — | — |

### 4.2 Refinement / cleaning

| Task | First choice | Anti-pattern |
| --- | --- | --- |
| Remove emoji | `RemoveEmojiRefiner` (general_text/refine) | `PromptedRefiner` |
| Remove URLs, HTML tags | `HtmlUrlRemoverRefiner` (general_text/refine) | `PromptedRefiner` |
| Remove HTML entities (&nbsp; etc.) | `HtmlEntityRefiner` (general_text/refine) | `PromptedRefiner` |
| Collapse whitespace | `RemoveExtraSpacesRefiner` (general_text/refine) | `PromptedRefiner` |
| Lowercase text | `LowercaseRefiner` (general_text/refine) | `PromptedRefiner` |
| Strip punctuation / numbers | `RemovePunctuationRefiner` / `RemoveNumberRefiner` (general_text/refine) | — |
| Normalize dates / currencies | `TextNormalizationRefiner` (general_text/refine) | — |
| LLM paraphrase / semantic rewrite / style transfer | `PromptedRefiner` (core_text/refine) | Using deterministic refiner when the task needs understanding |
| Field rename / flatten / derive columns | `PandasOperator` (core_text/refine) | Any `Prompted*` operator |

**Rule of thumb**: if the cleaning rule is describable as a regex or a fixed transform, use the deterministic refiner. Stack multiple deterministic refiners if needed — they are cheap, idempotent, and reliable.

### 4.3 Filtering

| Task | First choice | Anti-pattern |
| --- | --- | --- |
| Filter by a computed numeric field (score >= 3) | `GeneralFilter` (core_text/filter) with `filter_rules=["lambda df: df['score'] >= 3"]` | `PromptedFilter` (cannot do numeric comparisons) |
| Filter by LLM semantic judgment on ONE field | `PromptedFilter` (core_text/filter) | `GeneralFilter` (deterministic) |
| Filter by multi-field LLM judgment | `FormatStrPromptedGenerator` (produce a score/flag field) + `GeneralFilter` (threshold on it) | `PromptedFilter` alone (can only see one field) |
| Filter by word count | `WordNumberFilter` (general_text/filter) | `GeneralFilter` if you want |
| Filter by language | `LLMLanguageFilter` (general_text/filter) — also drops rows whose language is NOT in allowed set | — |
| Deduplicate | `HashDeduplicateFilter` or `NgramHashDeduplicateFilter` (general_text/filter) | — |
| Diversity downsample | `KCenterGreedyFilter` (core_text/filter) | — |
| Toxicity filter | `PerspectiveFilter` (general_text/filter) | — |
| Lexical diversity filter | `LexicalDiversityFilter` (general_text/filter) | — |
| Ngram repetition filter | `NgramFilter` (general_text/filter) | — |

### 4.4 Evaluation

| Task | First choice | Anti-pattern |
| --- | --- | --- |
| Score general text quality with LLM + produce a score field | `PromptedEvaluator` (core_text/eval) | `FormatStrPromptedGenerator` (works but less semantic) |
| Score a QA pair's quality (question + answer together) | `Text2QASampleEvaluator` (core_text/eval) | `PromptedEvaluator` (single field only) |
| Alpagasus-style instruction quality | `AlpagasusSampleEvaluator` (text_sft/eval) — ONLY if task is instruction tuning | `PromptedEvaluator` (fine for general use) |
| Lexical diversity / ngram repetition / BLEU / toxicity scores | Corresponding `*SampleEvaluator` in `general_text/eval` | — |

### 4.5 Knowledge cleaning (URL / PDF → QA)

**In this API-only deployment, the KBC trio and MinerU-based converters are NOT available** (they depend on local chunking / web extraction libraries that are not installed). If the user asks for "URL → chunks" or "PDF → QA":

1. Call `list_operators(category=knowledge_cleaning)` to confirm which KBC operators the registry actually exposes.
2. If `KBCChunkGenerator`, `FileOrURLToMarkdownConverterFlash`, or `FileOrURLToMarkdownConverterAPI` are missing from the returned list, stop and reply to the user: "URL / PDF ingestion operators are not available in this deployment; please preprocess your files into JSONL chunks first, then retry."
3. If they ARE available, the canonical chain is: `FileOrURLToMarkdownConverterFlash` → `KBCChunkGenerator` → `KBCTextCleaner`, all in `knowledge_cleaning`. Use all three in that order; input to step 1 must be a file path or URL, not inline text.

---

## 5. Nested-output caveat: `Text2MultiHopQAGenerator`

`Text2MultiHopQAGenerator` writes a nested list of dicts (default field `qa_pairs`). Downstream ops **cannot** directly reference `question` or `answer` as top-level keys. To score / filter individual QA pairs, either:

- use `Text2QASampleEvaluator` which understands the nested structure, or
- use a post-processing step that explodes the list into rows (you can do this in a separate pipeline), then run `PromptedFilter` / `GeneralFilter` on the flattened rows.

Do NOT try `FormatStrPromptedGenerator` with `{question}` / `{answer}` placeholders on the nested column — it will silently fail or produce garbage.

---

## 6. Standard pipeline code structure

```python
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.core_text.generate import PromptedGenerator
# ... other imports

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="<USER_PROVIDED_JSONL_PATH>",   # exact path the user gave; do NOT invent
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl",
        )
        self.llm_serving = APILLMServing_request(serving_id="<from list_servings>")  # if LLM ops present
        self.op1 = PromptedGenerator(llm_serving=self.llm_serving, system_prompt="...")
        # ...

    def forward(self):
        self.op1.run(storage=self.storage.step(), input_key="source_field", output_key="new_field")
        # ...

if __name__ == "__main__":
    MyPipeline().forward()
```

`__init__` holds storage + serving + operator construction. `forward` threads `self.storage.step()` and runs operators sequentially.

---

## 7. Output contract (what you reply to the user)

Your text reply should contain, in this order:

1. **Plan JSON** (the `plan` block from R5), so the user can read your operator selection reasoning before execution.
2. **Field flow diagram** (one line): `user_field → op_A → op_B → final_field`.
3. **Tool-call log**: a short summary of what you called (list_categories, list_operators for <X>, created pipeline <id>, rendered editor). This is for user auditability.
4. **Next step for the user**: "Click Run in the DAG editor to execute." — nothing more.

---

## 8. Common agent mistakes this skill prevents

These are mistakes the previous system observed in deployment; the rules above target each:

- `list_operators` with empty args → context overflow (R2 step, rule R5 turn budget).
- Invent dataset id from the english description → backend returns "dataset not found" (R1).
- Omit `llm_serving` when LLM ops present → pipeline fails at init (R2).
- `prompt_template = {"template": "..."}` → operator init error (R3).
- Use `PromptedRefiner` for emoji / URL / whitespace cleaning → fragile + expensive (§4.2 anti-patterns).
- Use `SFTGeneratorSeed` for QA-from-text → wrong category (§3 anti-mappings; §4.1 row).
- Call `create_pipeline` more than once per turn, producing DAG flicker → (R5 think-first).
- Agent auto-runs `execute_pipeline` mid-reasoning → user loses control (R6).
