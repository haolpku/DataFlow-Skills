# DataFlow-Skills

Reusable agent skills for DataFlow workflows.

中文文档: [README_CN.md](./README_CN.md)

## Skills

- `generating-dataflow-pipeline`
  - Reasoning-guided pipeline planner that generates standard DataFlow pipeline code.
- `dataflow-operator-builder`
  - Production-grade scaffold skill for new DataFlow operators (`generate/filter/refine/eval`), including templates, CLI wrappers, and tests.
- `prompt-template-builder`
  - Production-oriented skill for building/revising DataFlow prompt templates/configs for existing operators, with two-round AskUserQuestion intake, two-stage auditable outputs, and static acceptance walkthrough.

## How To Use

### Prerequisites

Use the project conda environment before running Python commands:

```bash
conda activate dataflow
```

### `dataflow-operator-builder`

What this skill is for:
- Use it when you need a new operator package that is immediately runnable in a real repo, not just a single class file.
- It is especially useful when you want structure consistency across teams: same package layout, same CLI style, and same baseline tests.

What you get after one run:
- A complete operator implementation for one type: `generate`, `filter`, `refine`, or `eval`.
- A separate CLI module under `cli/`, so the operator can be run in batch jobs without writing extra glue code.
- Baseline test files (`unit`, `registry`, `smoke`) so the operator is easier to validate in CI from day one.

How it works in practice:
1. You describe the operator contract through a spec (package name, operator type, class/module names, input/output keys, and whether it uses LLM).
2. The skill validates the spec and applies template rules from `references/` to avoid common contract and registration mistakes.
3. It renders files into your target repo and can run in preview mode first (`--dry-run`) so you can inspect changes before writing.
4. You fill in business logic details where needed, then run the generated tests and CLI for a quick end-to-end check.

Typical usage:
- Chat entry: `/dataflow-operator-builder`
- Direct spec entry: `/dataflow-operator-builder --spec path/to/spec.json --output-root path/to/repo`

Minimal spec example:

```json
{
  "package_name": "dataflow_ext_demo",
  "operator_type": "filter",
  "operator_class_name": "DemoQualityFilter",
  "operator_module_name": "demo_quality_filter",
  "input_key": "raw_text",
  "output_key": "is_valid",
  "uses_llm": false
}
```

Input expectations:
- Required: `package_name`, `operator_type`, `operator_class_name`, `operator_module_name`, `input_key`, `output_key`, `uses_llm`.
- Optional but common in real projects: `cli_module_name`, `test_file_prefix`, `overwrite_strategy`, `validation_level`.

A concrete scenario:
- Suppose you need a `filter` operator that removes low-quality records before expensive generation.
- With this skill, you can quickly scaffold a consistent package, plug in your filtering rules, and immediately run registry/smoke tests.
- This reduces the usual setup time (folder layout, imports, registration, CLI wiring, test skeletons) and lets you focus on operator logic.

Helpful flags:
- `--dry-run`: preview create/update plan without modifying files.
- `--overwrite {ask-each,overwrite-all,skip-existing}`: control overwrite behavior safely in existing repos.
- `--validation-level {none,basic,full}`: choose how strict pre-write checks should be.

Minimal run command:

```bash
python dataflow-operator-builder/scripts/build_operator_artifacts.py \
  --spec /tmp/operator_spec.json \
  --output-root . \
  --dry-run
```

### `prompt-template-builder`

What this skill is for:
- Use it when an existing operator needs a new prompt template, or when an old template starts failing on quality, format stability, or business constraints.
- It is built for production updates where you need clear reasoning and traceability, not just a rewritten prompt string.

What makes it different:
- It first checks operator compatibility and picks the right template style (for example `DIYPromptABC` or `FormatStrPrompt`) so your final output matches operator expectations.
- It returns auditable two-stage outputs, which helps reviewers understand both the decision process and the final artifact.

How the two stages help review:
1. Stage 1 (decision JSON): explains why a specific template/config strategy was chosen, how arguments are mapped, what output contract is enforced, and which static checks must pass.
2. Stage 2 (final deliverable): provides the final template/config, integration snippet, and a checklist-style walkthrough that can be copied into code review or QA notes.

Typical usage:
- Chat entry: `/prompt-template-builder`
- Direct spec entry: `/prompt-template-builder --spec path/to/prompt_spec.json`

Minimal spec example:

```json
{
  "Target": "Generate concise e-commerce selling points",
  "OP_NAME": "PromptedGenerator",
  "Constraints": "Professional tone; <= 80 Chinese chars",
  "Arguments": ["product_name", "category"]
}
```

Input expectations:
- Required: `Target`, `OP_NAME`.
- Optional but strongly recommended: `Constraints`, `Expected Output`, `Arguments`, `Sample Cases`, `Tone/Style`, `Validation Focus`.

A concrete scenario:
- You have a `PromptedGenerator` that should generate short e-commerce selling points, but outputs are too long and style is inconsistent.
- You can provide the business target, length/style constraints, and sample inputs.
- The skill then produces a type-aligned prompt solution plus validation notes, so you can quickly test whether output length and tone are now stable.

Expected output shape:
- A Stage 1 decision record (strategy, mapping, checks such as `prompt_template_type_aligned`).
- A Stage 2 implementation package (template/config content, integration guidance, and acceptance walkthrough).

## File Structure

```text
DataFlow-Skills/
├── README.md                                        # Repository overview and quick navigation
├── README_CN.md                                     # Chinese version of this overview
├── generating-dataflow-pipeline/                    # Skill: generate DataFlow pipeline code from requirements
│   ├── SKILL.md                                     # Main skill instructions and execution flow
│   ├── examples/                                    # End-to-end planning/output examples
│   │   ├── basic_generate_and_filter.md             # Basic two-stage generate+filter pipeline example
│   │   ├── kbc_pdf_to_qa.md                         # PDF-to-QA pipeline for KBC-style content
│   │   ├── multi_stage_pipeline.md                  # Multi-stage pipeline orchestration example
│   │   └── multifield_scoring.md                    # Example with multi-field scoring logic
│   └── templates/
│       └── pipeline_template.py                     # Base Python pipeline template emitted by the skill
├── dataflow-operator-builder/                       # Skill: scaffold production-grade DataFlow operators
│   ├── SKILL.md                                     # Main workflow for operator generation
│   ├── assets/
│   │   └── templates/                               # Code templates rendered into operator artifacts
│   │       ├── cli/
│   │       │   └── operator_cli.py.tmpl            # CLI entrypoint template for generated operators
│   │       ├── operators/
│   │       │   ├── eval_operator.py.tmpl            # Template for eval operator implementation
│   │       │   ├── filter_operator.py.tmpl          # Template for filter operator implementation
│   │       │   ├── generate_operator.py.tmpl        # Template for generate operator implementation
│   │       │   └── refine_operator.py.tmpl          # Template for refine operator implementation
│   │       ├── package/
│   │       │   ├── cli_init.py.tmpl                 # Package init for CLI module
│   │       │   ├── operator_pkg_init.py.tmpl        # Package init for operator package
│   │       │   ├── operators_root_init.py.tmpl      # Root operators package init template
│   │       │   └── package_init.py.tmpl             # Top-level package init template
│   │       └── tests/
│   │           ├── test_operator_registry.py.tmpl   # Registry test template for operator registration
│   │           ├── test_operator_smoke.py.tmpl      # Smoke test template for basic runtime checks
│   │           └── test_operator_unit.py.tmpl       # Unit test template for operator behavior
│   ├── references/                                  # Constraints, contracts, and acceptance references
│   │   ├── acceptance-checklist.md                  # Final acceptance checklist for generated operators
│   │   ├── askuserquestion-rounds.md                # AskUserQuestion protocol and round structure
│   │   ├── cli-shell-guidelines.md                  # CLI design and shell interaction guidelines
│   │   ├── gotchas.md                               # Known pitfalls and implementation caveats
│   │   ├── operator-contract.md                     # Required operator interface and behavior contract
│   │   ├── output-checklist.md                      # Output completeness and quality checklist
│   │   └── registration-rules.md                    # Rules for operator registration and discovery
│   └── scripts/
│       ├── build_operator_artifacts.py              # Template rendering/build script for operator artifacts
│       └── example_spec.json                        # Example input spec consumed by build script
└── prompt-template-builder/                         # Skill: build/revise DataFlow prompt templates/configs
    ├── SKILL.md                                     # Main workflow and constraints for template generation
    ├── examples/
    │   ├── filter_rewrite_finance.md                # Finance-domain filter/rewrite prompt example
    │   ├── multifield_scoring_prompt.md             # Multi-field scoring prompt template example
    │   └── single_field_generation.md               # Single-field generation prompt example
    ├── references/
    │   ├── acceptance-checklist.md                  # Acceptance criteria for prompt_template outputs
    │   ├── askuserquestion-rounds.md                # AskUserQuestion round protocol for this skill
    │   ├── gotchas.md                               # Common mistakes and edge cases
    │   ├── input-schema.md                          # Required input schema definition
    │   └── output-contract.md                       # Expected output contract and formatting rules
    └── templates/
        ├── decision_json_template.md                # Decision JSON output template
        ├── final_response_template.md               # Final natural-language response template
        └── prompt_class_template.py.tmpl            # Python DIYPromptABC class skeleton (for compatible operators)
```
