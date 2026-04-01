# dataflow-operator-builder

[← Back to DataFlow-Skills](../README.md) | 中文版: [README_zh.md](./README_zh.md)

Production-grade scaffold skill for new DataFlow operators (`generate/filter/refine/eval`), including templates, CLI wrappers, and tests.

## What This Skill Is For

- Use it when you need a new operator package that is immediately runnable in a real repo, not just a single class file.
- It is especially useful when you want structure consistency across teams: same package layout, same CLI style, and same baseline tests.

## What You Get After One Run

- A complete operator implementation for one type: `generate`, `filter`, `refine`, or `eval`.
- A separate CLI module under `cli/`, so the operator can be run in batch jobs without writing extra glue code.
- Baseline test files (`unit`, `registry`, `smoke`) so the operator is easier to validate in CI from day one.

## How It Works in Practice

1. You describe the operator contract through a spec (package name, operator type, class/module names, input/output keys, and whether it uses LLM).
2. The skill validates the spec and applies template rules from `references/` to avoid common contract and registration mistakes.
3. It renders files into your target repo and can run in preview mode first (`--dry-run`) so you can inspect changes before writing.
4. You fill in business logic details where needed, then run the generated tests and CLI for a quick end-to-end check.

## Typical Usage

- Chat entry: `/dataflow-operator-builder`
- Direct spec entry: `/dataflow-operator-builder --spec path/to/spec.json --output-root path/to/repo`

## Minimal Spec Example

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

## Input Expectations

- Required: `package_name`, `operator_type`, `operator_class_name`, `operator_module_name`, `input_key`, `output_key`, `uses_llm`.
- Optional but common in real projects: `cli_module_name`, `test_file_prefix`, `overwrite_strategy`, `validation_level`.

## A Concrete Scenario

- Suppose you need a `filter` operator that removes low-quality records before expensive generation.
- With this skill, you can quickly scaffold a consistent package, plug in your filtering rules, and immediately run registry/smoke tests.
- This reduces the usual setup time (folder layout, imports, registration, CLI wiring, test skeletons) and lets you focus on operator logic.

## Helpful Flags

- `--dry-run`: preview create/update plan without modifying files.
- `--overwrite {ask-each,overwrite-all,skip-existing}`: control overwrite behavior safely in existing repos.
- `--validation-level {none,basic,full}`: choose how strict pre-write checks should be.

## Minimal Run Command

```bash
python dataflow-operator-builder/scripts/build_operator_artifacts.py \
  --spec /tmp/operator_spec.json \
  --output-root . \
  --dry-run
```
