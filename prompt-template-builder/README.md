# prompt-template-builder

[← Back to DataFlow-Skills](../README.md) | 中文版: [README_zh.md](./README_zh.md)

Production-oriented skill for building/revising DataFlow prompt templates/configs for existing operators, with two-round AskUserQuestion intake, two-stage auditable outputs, and static acceptance walkthrough.

## What This Skill Is For

- Use it when an existing operator needs a new prompt template, or when an old template starts failing on quality, format stability, or business constraints.
- It is built for production updates where you need clear reasoning and traceability, not just a rewritten prompt string.

## What Makes It Different

- It first checks operator compatibility and picks the right template style (for example `DIYPromptABC` or `FormatStrPrompt`) so your final output matches operator expectations.
- It returns auditable two-stage outputs, which helps reviewers understand both the decision process and the final artifact.

## How the Two Stages Help Review

1. Stage 1 (decision JSON): explains why a specific template/config strategy was chosen, how arguments are mapped, what output contract is enforced, and which static checks must pass.
2. Stage 2 (final deliverable): provides the final template/config, integration snippet, and a checklist-style walkthrough that can be copied into code review or QA notes.

## Typical Usage

- Chat entry: `/prompt-template-builder`
- Direct spec entry: `/prompt-template-builder --spec path/to/prompt_spec.json`

## Minimal Spec Example

```json
{
  "Target": "Generate concise e-commerce selling points",
  "OP_NAME": "PromptedGenerator",
  "Constraints": "Professional tone; <= 80 Chinese chars",
  "Arguments": ["product_name", "category"]
}
```

## Input Expectations

- Required: `Target`, `OP_NAME`.
- Optional but strongly recommended: `Constraints`, `Expected Output`, `Arguments`, `Sample Cases`, `Tone/Style`, `Validation Focus`.

## A Concrete Scenario

- You have a `PromptedGenerator` that should generate short e-commerce selling points, but outputs are too long and style is inconsistent.
- You can provide the business target, length/style constraints, and sample inputs.
- The skill then produces a type-aligned prompt solution plus validation notes, so you can quickly test whether output length and tone are now stable.

## Expected Output Shape

- A Stage 1 decision record (strategy, mapping, checks such as `prompt_template_type_aligned`).
- A Stage 2 implementation package (template/config content, integration guidance, and acceptance walkthrough).
