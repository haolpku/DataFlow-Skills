# DataFlow-Skills（分支 `v2`）

> **分支范围**：本分支只包含**一个 skill**，`dataflow-pipeline-v2/`，它是 EMNLP 评测中 `DF-Agent (v2)` 配置实际加载的构造期 skill。完整的多模块 suite（operator-builder / prompt-template-builder / dataflow-dev / dataflow-webui-dev / mcp-server / core_text 等）保留在 `main` 分支。
>
> English version: [README.md](./README.md)

## 这个 skill 干什么

`dataflow-pipeline-v2` 引导一个 code agent（Claude Code、Cursor 等），从以下两个输入构造一条 **DataFlow pipeline**：

1. 一个 JSONL 样本路径，
2. 一个自然语言目标（"清洗并打分这批评论"、"从这些 chunk 生成多跳 QA" 等）。

输出是一个**已存储的 pipeline 对象**，会出现在 DataFlow-WebUI 的 DAG 编辑器里，由用户在 WebUI 里点 Run 按钮执行。Agent 自己不执行 pipeline。

## 为什么要重写一版 v2

`main` 分支上的 v1 是"推理引导"风格——告诉 agent "从首选算子里挑合适的"，列了六个 core 算子做出发点。在我们的实验里观察到 8 类反复发生的失败模式：

1. agent 不带 `category` 参数裸调 `list_operators`，一次返回 ~145 个算子，把 context 撑爆；
2. agent 把 `PromptedGenerator` 当万金油首选，错路由那些其实有专用算子的任务（例如多跳 QA 应该走 `Text2MultiHopQAGenerator`）；
3. v1 的 "KBC 三连必须按序使用" 规则在 API-only 环境也会触发，可那个环境里 KBC 算子没有安装；
4. agent 选 `SFTGeneratorSeed` 来生成新 QA（这个种子生成器要求**已有** SFT 样本作输入）；
5. agent 边推理边调 `create_pipeline`，一个 turn 里把好几个不兼容的草稿都推进编辑器；
6. agent 把 `llm_serving` 写成 `{"id": "..."}`（dict）而不是 bare string id；
7. agent 把 `prompt_template` 写成 `{"template": "..."}`（dict），后端拒收；
8. 用户数据字段名是 `chunk` 时，agent 没把算子的 `input_key` 从默认 `cleaned_chunk` 改过来。

v2 用 **硬规则 + Category Cheat Sheet + 反例（anti-pattern）** 取代推理引导风格，并加入 think-first 协议——`create_pipeline` 之前必须先输出一份结构化的 `plan` JSON。skill 配套使用 DataFlow-WebUI 一侧的 server 改动：操作类别端点会返回每个 category 的 `use_for` / `not_for` / `examples`，让反例知识住在工具响应里，而不是只在 skill 文档里。

## 怎么用

把 `dataflow-pipeline-v2/` 拷到 agent 的 skills 目录下：

```
~/.claude/skills/dataflow-pipeline-v2/
或者
<project_root>/.claude/skills/dataflow-pipeline-v2/
```

当用户的请求匹配 trigger 描述（build / design / create / optimize a DataFlow pipeline）时，skill 会自动加载。

需要：
- 一个跑着的 DataFlow-WebUI 后端（默认 `http://localhost:8000`），并应用了对应的 MCP guard 改动（`list_operators` 强制 `category` 参数；categories 端点返回 `use_for`/`not_for` 指引）；
- 一个 MCP config，白名单包含 `mcp__dataflow__*` 工具族。

## 实验数字

| Method                              |  n   | Time | Succ.    | Op.\,err |
|-------------------------------------|-----:|-----:|---------:|---------:|
| Direct Claude Code（无 MCP、无 skill）| 68 |    — |  0.0 \%  | 1.82     |
| MCP-only（无 skill，MCP guard 已开）| 36   | 1.4  | 36.1 \%  | 0.25     |
| DF-Agent (dev-only，加错 skill)     | 30   | 2.0  | 26.7 \%  | 1.77     |
| DF-Agent (slim skill)               | 36   | 1.3  | 30.6 \%  | 0.25     |
| **DF-Agent（本 skill，v2）**        | 36   | 1.4  | **47.2 \%** | **0.22** |
| DF-Agent（legacy 多 skill suite）   | 36   | 1.4  | 25.0 \%  | 0.25     |

12 个任务 × 3 reps per condition。Time 是从 agent 第一次工具调用到第一次有效 pipeline render 的中位 wall-clock 分钟。Succ. 是 pipeline 跑出来且至少有一条记录通过 acceptance schema 的比例。Op.\,err 是平均算子选择错误数。

最大的提升来自 MCP server 端的 guard（不加任何 skill，从 0% 直接跳到 36%）。本 skill 在那基础上再加 11 个百分点，主要靠字段流规则和 think-first 协议——而不是靠算子识别（那部分 MCP 已经搞定）。

## 安装 / 依赖

skill 本身没有依赖。运行时需要的改动在 DataFlow-WebUI 那边：
- categories 端点暴露 `use_for` / `not_for` / `examples`
- `list_operators` 强制要 `category` 参数
- 引擎能丢弃 unsupported run/init 参数，并把 `llm_serving={"id": ...}` dict 解包成 scalar id

对应后端在 `HeRunming/DataFlow-WebUI` 的 `skills-agent-emnlp` 分支。
