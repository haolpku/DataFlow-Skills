# prompt-template-builder

[← 返回 DataFlow-Skills](../README_zh.md) | English: [README.md](./README.md)

用于为已有算子构建/修订 DataFlow prompt 模板或配置（按算子契约对齐类型）。

## 这个 Skill 适合什么场景

- 你已经有算子了，但 prompt 效果不稳定，或者输出经常不符合领域化预期，需要系统化改写。
- 你不只想"改一句提示词"，还希望保留清晰的决策依据，方便代码评审和回溯。

## 它和普通 prompt 改写的区别

- 会先根据算子契约判断应该用哪种模板形式（例如 `DIYPromptABC` 或 `FormatStrPrompt`），避免模板类型与算子不匹配。
- 输出分成两个阶段，先解释"为什么这么做"，再给"最终可落地内容"。

## 两阶段输出在实际协作中的价值

1. Stage 1（决策 JSON）：把模板选择原因、参数映射、输出契约、静态检查项讲清楚，便于评审。
2. Stage 2（最终产物）：给出模板/配置内容、集成片段和验收 walkthrough，便于开发和测试直接接手。

## 入口方式

- 对话入口：`/prompt-template-builder`
- 指定 spec：`/prompt-template-builder --spec path/to/prompt_spec.json`

## 最小 spec 示例

```json
{
  "Target": "生成简洁的电商商品卖点",
  "OP_NAME": "PromptedGenerator",
  "Constraints": "语气专业；中文不超过80字",
  "Arguments": ["product_name", "category"]
}
```

## 输入字段要求

- 必填：`Target`、`OP_NAME`。
- 建议补充：`Constraints`、`Expected Output`、`Arguments`、`Sample Cases`、`Tone/Style`、`Validation Focus`。

## 一个具体例子（自然语言）

- 例如你的 `PromptedGenerator` 负责生成电商卖点，但经常超字数、语气飘忽。
- 你把"目标、字数限制、语气要求、示例输入"告诉这个 Skill，它会给出契约对齐的模板方案和对应验收点。
- 这样你可以更快判断：新模板是否真的把长度和风格稳定下来，而不是靠反复手调。

## 期望输出形态

- Stage 1：决策记录（策略、映射、检查项，含 `prompt_template_type_aligned`）。
- Stage 2：实现内容（模板/配置、集成说明、验收 walkthrough）。
