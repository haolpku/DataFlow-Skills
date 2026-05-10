# DataFlow-Skills

为 [DataFlow](https://github.com/OpenDCAI/DataFlow) 数据处理框架准备的可复用 [Claude Code Skills](https://code.claude.com/docs/zh-CN/skills)。

English version: [README.md](./README.md)

---

## 仓库内容

三个 skill，Claude Code 从 `~/.claude/skills/<名字>/SKILL.md` 自动加载：

| Skill | 干什么 | 调用方式 |
|---|---|---|
| **`generating-dataflow-pipeline`** | 给一个任务目标 + 一个 JSONL 样本文件，规划算子链并生成可运行的 DataFlow pipeline 代码。 | `/generating-dataflow-pipeline` |
| **`dataflow-dev`** | DataFlow 开发助手。加载架构知识库，按意图路由（新建算子 / 新建 pipeline / 新建 prompt / 诊断报错 / 规范审查 / 知识库同步）。在 DataFlow 仓库里使用。 | `/dataflow-dev` |
| **`core_text`** | 算子级 API 参考（8 个 generator、3 个 filter、2 个 refiner、5 个 evaluator）。当 pipeline skill 需要超出 6 个核心算子之外的扩展算子时会查阅它。**不直接调用**，是供其他 skill 阅读的资料。 | _（不直接调用）_ |

---

## 安装

**前置条件：** Claude Code CLI 已安装并在 `PATH` 中。如果还没装，参见 [docs/install-claude-code_zh.md](./docs/install-claude-code_zh.md)。

```bash
git clone https://github.com/haolpku/DataFlow-Skills.git
cd DataFlow-Skills
./install.sh
```

脚本会把三个 skill 都拷到 `~/.claude/skills/`（用户级——所有项目都能用）。然后在任意 Claude Code 会话里：

```
/generating-dataflow-pipeline
```

补全里能看到这个斜杠命令就装好了。

### 安装选项

```bash
./install.sh --project                       # 装到当前项目的 ./.claude/skills/，而不是 ~/.claude/skills/
./install.sh dataflow-dev                    # 只装指定的 skill
./install.sh --force                         # 覆盖已存在的 skill（默认是跳过）
./install.sh --help
```

### 更新

```bash
cd DataFlow-Skills
git pull
./install.sh --force
```

---

## 三个 skill 速览

### `generating-dataflow-pipeline`

视频教程：[生成 DataFlow Pipeline](https://github.com/user-attachments/assets/ca1fefbf-9bf7-469f-b856-b201952fb99b)

给它一个目标和 1–5 行样本数据，它先返回算子决策 JSON，再生成完整的 pipeline `.py`。

```text
/generating-dataflow-pipeline
目标：生成商品描述并筛选优质内容
样本文件：./data/products.jsonl
预期输出字段：generated_description, quality_score
```

它优先从 6 个核心算子里选：`PromptedGenerator`、`FormatStrPromptedGenerator`、`Text2MultiHopQAGenerator`、`PromptedFilter`、`GeneralFilter`，以及 **KBC 三件套**（`FileOrURLToMarkdownConverterFlash` → `KBCChunkGenerator` → `KBCTextCleaner`）。这些不够用时会查 `core_text` skill 里的扩展算子。完整决策规则、生成 pipeline 的标准结构见 [`generating-dataflow-pipeline/SKILL.md`](./generating-dataflow-pipeline/SKILL.md)。

### `dataflow-dev`

在 clone 出来的 DataFlow 仓库里运行。它先加载知识库，探测 git 状态，然后按你的意图路由：

| 你说类似这样的话…… | 走哪个流程 |
|---|---|
| "新建一个 filter 算子……" | 算子创建（重复检查 → 规格确认 → 生成代码 + 注册提醒） |
| "新建一个 pipeline……" | Pipeline 创建（标准 `storage.step()` 模式） |
| "给 X 写个 prompt" | Prompt 创建（`PromptABC` / `DIYPromptABC`，`@prompt_restrict` 位置） |
| "我遇到 `KeyError: …`" | 诊断：匹配 `diagnostics/known_issues.md` 中的 #001–#008 |
| "审查这个算子" | 14 项检查清单（注册、`run()` 签名、`get_desc` 等） |
| "上游仓库有新算子了" | 对照 `knowledge_base.md` 找差异，输出更新步骤 |

详情：[`dataflow-dev/SKILL.md`](./dataflow-dev/SKILL.md)。对齐 [OpenDCAI/DataFlow](https://github.com/OpenDCAI/DataFlow) `main`（v1.0.10）。

### `core_text`

纯文档型 skill —— 每个算子目录下有 `SKILL.md`、`SKILL_zh.md`、`examples/good.md`、`examples/bad.md`。直接浏览：[`core_text/`](./core_text/)。

---

## 加自己的算子 skill

1. 在 `core_text/<分类>/<你的算子>/` 下放 `SKILL.md` + `examples/{good,bad}.md`。
2. 在 [`generating-dataflow-pipeline/SKILL.md`](./generating-dataflow-pipeline/SKILL.md) 的 "Extended Operator Reference" 对应分类表格里加一行。**不加这行 pipeline 规划器就发现不了你的算子**。

如果这个算子高频到该升为核心原语，再去同一份 SKILL.md 的 "Operator Selection Priority Rule"、"Operator Parameter Signature Rule"、"Correct Import Paths"、（如涉及新数据类型）"Input File Content Analysis Rule" 几节里补上对应条目。

---

## 仓库结构

```
DataFlow-Skills/
├── install.sh                       # 一键安装脚本（cp -r 到 ~/.claude/skills/）
├── docs/
│   └── install-claude-code_zh.md    # Claude Code CLI 安装指南
├── generating-dataflow-pipeline/    # Pipeline 规划器 skill
├── dataflow-dev/                    # DataFlow 开发助手 skill
└── core_text/                       # 扩展算子参考
    ├── generate/
    ├── filter/
    ├── refine/
    └── eval/
```

---

## 上游仓库

所有知识库均对齐 **[OpenDCAI/DataFlow](https://github.com/OpenDCAI/DataFlow)** `main`（v1.0.10）。
