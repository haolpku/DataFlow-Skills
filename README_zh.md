# DataFlow-Skills

用于 DataFlow 工作流的可复用 Agent Skills。

English version: [README.md](./README.md)

## 前置条件：安装 Claude Code

### 三种使用方式对比

| 方式 | 适合人群 | 优点 | 缺点 |
|------|----------|------|------|
| Web 端 | 完全新手 | 无需安装，打开就用 | 功能相对有限 |
| CLI（命令行） | 有一定基础的开发者 | 功能完整，集成度高 | 需要熟悉命令行 |
| 编辑器集成（VS Code / Cursor 等） | 日常开发 | 无缝融入工作流 | 依赖插件和环境配置 |

**建议：**
- 完全新手 → 先用 Web 端 [https://claude.ai/](https://claude.ai/) 试试手感
- 想用于开发 → 直接学 CLI（命令行）
- 已经熟练使用 → 考虑编辑器集成

本教程以 **CLI** 为主。

---

### 安装 Claude Code CLI

#### 1. 前置准备

- 需要一个 Claude 账号，访问 [claude.ai](https://claude.ai) 注册（如使用国内大模型可跳过）
- 确保电脑有命令行工具：
  - Mac / Linux：打开 Terminal（终端）
  - Windows：打开 PowerShell 或安装 WSL

#### 2. 使用官方脚本安装（推荐）

**macOS / Linux / WSL：**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell：**
```powershell
irm https://claude.ai/install.ps1 | iex
```

**Windows CMD：**
```cmd
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

安装完成后验证：
```bash
claude --version
```
显示版本号即安装成功。

#### 3. 使用 npm 安装

前置条件：已安装 Node.js（验证：`node --version`，若未安装请至 [nodejs.org](https://nodejs.org) 下载）

```bash
npm install -g @anthropic-ai/claude-code
```

网络较慢时可使用国内镜像：
```bash
npm install -g @anthropic-ai/claude-code --registry=https://registry.npmmirror.com
```

#### 4. 更新

手动更新：
```bash
claude update
```

Claude Code 启动时会自动检查更新，后台下载后下次启动生效。可在 `settings.json` 中配置更新行为：

```json
{
  "autoUpdatesChannel": "stable"
}
```

禁用自动更新：
```json
{
  "env": {
    "DISABLE_AUTOUPDATER": "1"
  }
}
```

> **注意：** 通过 Homebrew 或 WinGet 安装时不支持自动更新，需手动执行：
> ```bash
> brew upgrade claude-code      # macOS
> winget upgrade Anthropic.ClaudeCode  # Windows
> ```

#### 5. 常见安装问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `npm command not found` | 未安装 Node.js | 至 [nodejs.org](https://nodejs.org) 下载安装 |
| `permission denied` | 无管理员权限 | Mac/Linux：命令前加 `sudo`；Windows：以管理员身份运行 PowerShell |
| 安装缓慢或卡住 | 网络问题 | 使用国内镜像：`--registry=https://registry.npmmirror.com` |

#### 终端推荐

- [WezTerm](https://wezterm.org/)（跨平台）
- [Alacritty](https://alacritty.org/)（跨平台）
- [Ghostty](https://ghostty.org/)（Linux / macOS）
- [Kitty](https://github.com/kovidgoyal/kitty)（Linux / macOS）

---

## `generating-dataflow-pipeline`

视频教程: [生成DataFlow Pipeline](https://github.com/user-attachments/assets/ca1fefbf-9bf7-469f-b856-b201952fb99b)

一款基于推理引导的 pipeline 规划工具，可根据任务描述与样本数据生成标准的 DataFlow pipeline 代码。

### 功能说明

给定**目标任务**（pipeline 需实现的功能）和**样本JSONL文件**（1–5条代表性数据行），该工具将执行以下操作：
1. 读取并分析样本数据——推断字段类型、内容特征与任务属性
2. 依据强制决策表，从六大核心原语算子中选取合适算子（需要时可使用扩展算子）
3. 校验算子链路中的字段依赖关系
4. 输出两阶段结果：先输出中间算子决策（JSON格式），再生成完整可运行的Python pipeline代码

### 快速上手

#### 1. 添加 Skill

克隆本仓库，并将 skill 目录复制到 Claude Code 的 skills 文件夹中：

```bash
git clone https://github.com/haolpku/DataFlow-Skills.git

# 项目级（仅当前项目可用）
cp -r DataFlow-Skills/generating-dataflow-pipeline .claude/skills/generating-dataflow-pipeline
cp -r DataFlow-Skills/core_text .claude/skills/core_text

# 或个人级（所有项目可用）
cp -r DataFlow-Skills/generating-dataflow-pipeline ~/.claude/skills/generating-dataflow-pipeline
cp -r DataFlow-Skills/core_text ~/.claude/skills/core_text
```

Claude Code 从 `.claude/skills/<skill-name>/SKILL.md` 自动发现 skills。`SKILL.md` frontmatter 中的 `name` 字段即为 `/斜杠命令` 名称。更多详情请参阅 [官方 skills 文档](https://code.claude.com/docs/zh-CN/skills)。

#### 2. 准备数据

创建 JSONL 文件（每行一个 JSON 对象），包含 1–5 条代表性数据：

```jsonl
{"product_name": "笔记本电脑", "category": "电子产品"}
{"product_name": "咖啡机", "category": "家用电器"}
```

#### 3. 运行 Skill

在 Claude Code 中调用 `/generating-dataflow-pipeline` 并描述你的目标：

```
/generating-dataflow-pipeline
目标：生成商品描述并筛选优质内容
样本文件：./data/products.jsonl
预期输出字段：generated_description, quality_score
```

#### 4. 查看输出

Skill 输出两阶段结果：

1. **中间算子决策**——包含算子链路、字段流转逻辑与推理依据的 JSON 数据
2. **字段映射**——区分已有字段与需生成字段
3. **有序算子列表**——按执行顺序排列的算子及选用理由
4. **推理总结**——说明该设计为何能满足目标任务
5. **完整 pipeline 代码**——遵循标准结构的可执行 Python 全量代码
6. **可调参数/注意事项**——可配置参数与调试技巧

### 六大核心算子

| 算子名称 | 用途 | 是否依赖大语言模型（LLM） |
|----------|------|--------------------------|
| `PromptedGenerator` | 单字段大模型生成 | 是 |
| `FormatStrPromptedGenerator` | 多字段模板式生成 | 是 |
| `Text2MultiHopQAGenerator` | 从文本构建多跳问答对 | 是 |
| `PromptedFilter` | 基于大模型的质量评分与筛选 | 是 |
| `GeneralFilter` | 基于规则的确定性过滤 | 否 |
| **KBC三算子组**（3个算子，需按固定顺序组合使用） | 文件/链接→Markdown→分块→清洗文本 | 部分依赖 |

### 生成的 pipeline 结构

所有生成的 pipeline 均遵循统一标准结构：
```python
from dataflow.operators.core_text import PromptedGenerator, PromptedFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",  # 用户提供的路径
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )
        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )
        # 算子实例化...

    def forward(self):
        # 按顺序执行operator.run()，每步通过storage.step()做断点持久化
        ...

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

核心规则：
- `first_entry_file_name` 严格设置为用户提供的JSONL文件路径
- 每个`operator.run()`调用均使用`storage=self.storage.step()`实现断点持久化
- 字段向前传递：字段必须存在于样本数据中，或由前置步骤生成，方可被后续算子使用

### 扩展算子

除六大核心原语外，DataFlow 还提供更多扩展算子。详见 [`core_text`](#core_text) 部分的完整算子参考。

### 新增算子

前置条件：新算子的工具定义文件已完成（包含`SKILL.md`、`examples/good.md`、`examples/bad.md`等）。

#### 作为扩展算子添加

需要两步：

**第 1 步.** 在合适目录下创建算子文件夹并编写工具定义（如`core_text/<分类>/`，或独立工具包）：
```
<工具目录>/<自定义算子名称>/
├── SKILL.md          # 接口文档（构造函数、run()方法签名、执行逻辑、约束条件）
├── SKILL_zh.md       # 中文翻译（可选）
└── examples/
    ├── good.md       # 最佳实践示例
    └── bad.md        # 常见错误示例
```

**第 2 步.** 在 `SKILL.md` 的 **Extended Operator Reference** section 中注册该算子。在对应类别表格（Generate / Filter / Refine / Eval）中添加一行，填写算子名、子目录路径和功能描述。不添加此条目，pipeline generator 无法感知该算子的存在。

#### 升级为核心原语算子（可选）

若某算子使用频率极高，需纳入优先选用范围，可通过修改`SKILL.md`完成升级：
1. **优选算子策略**——添加至核心原语列表
2. **算子选用优先级规则**——新增决策表条目（明确适用/不适用场景）
3. **算子参数签名规则**——补充完整构造函数与`run()`方法签名
4. **正确导入路径**——添加算子导入路径
5. **输入文件内容分析规则**——若支持新数据类型，补充输入模式匹配规则
6. **扩展算子参考表**——更新或移除扩展表中的对应条目，避免与核心原语重复
7. **使用示例**——在`examples/`目录添加完整示例（推荐）

---

## `core_text`

[`generating-dataflow-pipeline`](#generating-dataflow-pipeline) 的扩展算子参考库。

pipeline 生成器使用的所有文本处理算子的逐算子 API 文档。当 `generating-dataflow-pipeline/SKILL.md` 中的 6 个核心算子不能满足需求时，可查阅这里的详细参考。

### 有哪些算子

**生成类** (`core_text/generate/`)
- `prompted-generator` - 最基础的 LLM 生成
- `format-str-prompted-generator` - 用模板生成
- `chunked-prompted-generator` - 长文本分块生成
- `embedding-generator` - 生成向量
- `retrieval-generator` - RAG 生成
- `bench-answer-generator` - 给 benchmark 生成答案
- `text2multihopqa-generator` - 生成多跳问答
- `random-domain-knowledge-row-generator` - 随机生成领域知识

**过滤类** (`core_text/filter/`)
- `prompted-filter` - 用 LLM 打分过滤
- `general-filter` - 按数值规则过滤
- `kcentergreedy-filter` - 按多样性过滤

**精炼类** (`core_text/refine/`)
- `prompted-refiner` - 用 LLM 改写文本
- `pandas-operator` - 自定义 pandas 操作

**评估类** (`core_text/eval/`)
- `prompted-evaluator` - LLM 打分
- `bench-dataset-evaluator` - 评估 benchmark 数据集
- `bench-dataset-evaluator-question` - 评估 benchmark 问题
- `text2qa-sample-evaluator` - 评估问答样本
- `unified-bench-dataset-evaluator` - 统一评估

### 目录结构

每个算子文件夹里有：

- `SKILL.md` - 英文skill文档，描述算子使用场景，算子用法，算子导入，算子参数，算子运行示例。
- `SKILL_zh.md` - 中文文档
- `examples/good.md` - 正确用法示例，含单一算子的组成的简单pipeline示例，样例输入以及相应输出
- `examples/bad.md` - 常见错误汇总

---

## `dataflow-operator-builder`

视频教程: [构建 DataFlow 算子](https://files.catbox.moe/uzk3ag.mp4)

用于生成生产级 DataFlow 自定义算子脚手架（`generate/filter/refine/eval`），包含算子实现骨架、CLI 入口和测试文件。

### 功能说明

给定**算子 spec**（包名、算子类型、输入输出字段等），该工具将执行以下操作：
1. 校验 spec 并依据 `references/` 中的约束规则做静态检查，提前暴露注册、契约、命名等常见问题
2. 生成完整算子实现骨架（`generate` / `filter` / `refine` / `eval` 之一）
3. 在 `cli/` 下生成独立命令行入口，便于批处理和联调，无需手写胶水代码
4. 输出两阶段结果：先 `--dry-run` 展示创建/更新计划，确认无误后再真正写入文件

### 快速上手

#### 1. 添加 Skill

克隆本仓库，并将 skill 目录复制到 Claude Code 的 skills 文件夹中：

```bash
git clone https://github.com/haolpku/DataFlow-Skills.git

# 项目级（仅当前项目可用）
cp -r DataFlow-Skills/dataflow-operator-builder .claude/skills/dataflow-operator-builder

# 或个人级（所有项目可用）
cp -r DataFlow-Skills/dataflow-operator-builder ~/.claude/skills/dataflow-operator-builder
```

Claude Code 从 `.claude/skills/<skill-name>/SKILL.md` 自动发现 skills。

#### 2. 运行 Skill

**方式 A（默认）：交互式采访**

直接调用 skill，Agent 会通过两轮批量提问采集所有必要信息，无需提前准备任何文件：

```
/dataflow-operator-builder
```

- 第 1 轮：结构字段（包名、算子类型、输入/输出字段等）
- 第 2 轮：实现细节（是否使用 LLM、CLI 模块名、测试前缀等）

每个问题均附带推荐选项与理由，填写后自动进入生成流程。

**方式 B：直接指定 Spec（已有配置时使用）**

若已准备好算子 spec 文件（JSON 格式），可跳过采访直接执行：

```
/dataflow-operator-builder --spec path/to/spec.json --output-root path/to/repo
```

spec 示例：

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

必填字段：`package_name`、`operator_type`、`operator_class_name`、`operator_module_name`、`input_key`、`output_key`、`uses_llm`。常见可选：`cli_module_name`、`test_file_prefix`、`overwrite_strategy`、`validation_level`。

#### 4. 查看输出

Skill 输出两阶段结果：

1. **创建/更新计划**——`--dry-run` 展示将生成的文件清单，无文件落盘
2. **算子实现骨架**——含类定义、`run()` 方法签名与注册入口
3. **CLI 入口**——`cli/` 下可直接执行的批处理脚本
4. **测试文件**——`unit/registry/smoke` 三类基础测试，便于接入 CI 做最小验收

### 常用参数

- `--dry-run`：只展示计划，不落盘
- `--overwrite {ask-each,overwrite-all,skip-existing}`：控制覆盖行为，适合已有仓库渐进接入
- `--validation-level {none,basic,full}`：选择校验严格度

### 生成物一览

| 生成物 | 路径 | 说明 |
|--------|------|------|
| 算子实现 | `<package>/<module_name>.py` | 含类定义、`run()` 方法签名与注册入口 |
| CLI 入口 | `cli/<cli_module_name>.py` | 独立命令行批处理脚本 |
| 单元测试 | `tests/unit/test_<prefix>.py` | 基础单元测试 |
| 注册测试 | `tests/registry/test_<prefix>_registry.py` | 验证算子是否正确注册 |
| 冒烟测试 | `tests/smoke/test_<prefix>_smoke.py` | 端到端最小验收 |

### 生成的算子骨架

所有生成的算子均遵循统一结构：

```python
from dataflow.operators.base import BaseOperator
from dataflow.utils.storage import FileStorage

class DemoQualityFilter(BaseOperator):
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def run(self, storage: FileStorage) -> FileStorage:
        # 在此实现过滤逻辑
        ...
        return storage

# 注册入口（由 Skill 自动生成）
OPERATOR_REGISTRY.register("DemoQualityFilter", DemoQualityFilter)
```

核心规则：
- 必须继承 `BaseOperator` 并实现 `run()` 方法
- `run()` 接受并返回 `FileStorage` 实例，保持链式传递
- 必须通过 `OPERATOR_REGISTRY` 完成注册，方可被 pipeline 发现
- CLI 入口通过 `--input-file` / `--output-file` 参数直接调用 `run()`，不依赖 pipeline 上下文

---

## `prompt-template-builder`

视频教程: [DataFlow 提示词模板生成](https://files.catbox.moe/d1pdr9.mp4)

用于为已有算子构建/修订 DataFlow prompt 模板，按算子契约对齐模板类型，输出两阶段可审计结果。

### 功能说明

给定**目标算子**（算子名称、约束条件、输入参数等），该工具将执行以下操作：
1. 根据算子契约判断应使用哪种模板类型（如 `DIYPromptABC` 或 `FormatStrPrompt`），避免模板与算子不匹配
2. 输出 Stage 1 决策 JSON：包含模板选型原因、参数映射、输出契约与静态检查项，便于评审与回溯
3. 输出 Stage 2 最终产物：模板/配置内容、集成代码片段和验收 walkthrough，便于开发和测试直接接手

### 快速上手

#### 1. 添加 Skill

克隆本仓库，并将 skill 目录复制到 Claude Code 的 skills 文件夹中：

```bash
git clone https://github.com/haolpku/DataFlow-Skills.git

# 项目级（仅当前项目可用）
cp -r DataFlow-Skills/prompt-template-builder .claude/skills/prompt-template-builder

# 或个人级（所有项目可用）
cp -r DataFlow-Skills/prompt-template-builder ~/.claude/skills/prompt-template-builder
```

Claude Code 从 `.claude/skills/<skill-name>/SKILL.md` 自动发现 skills。

#### 2. 运行 Skill

**方式 A（默认）：交互式采访**

直接调用 skill，Agent 会通过两轮批量提问采集所有必要信息，无需提前准备任何文件：

```
/prompt-template-builder
```

- 第 1 轮：结构层（目标场景、目标算子、输出契约、约束条件）
- 第 2 轮：实现层（参数签名、边界样例、验收偏好）

每个问题均附带推荐选项与理由，填写后自动进入两阶段生成流程。

**方式 B：直接指定 Spec（已有配置时使用）**

若已准备好 prompt spec 文件（JSON 格式），可跳过采访直接执行：

```
/prompt-template-builder --spec path/to/prompt_spec.json
```

spec 示例：

```json
{
  "Target": "生成简洁的电商商品卖点",
  "OP_NAME": "PromptedGenerator",
  "Constraints": "语气专业；中文不超过80字",
  "Arguments": ["product_name", "category"]
}
```

必填字段：`Target`、`OP_NAME`。建议补充：`Constraints`、`Expected Output`、`Arguments`、`Sample Cases`、`Tone/Style`、`Validation Focus`。

#### 4. 查看输出

Skill 输出两阶段结果：

1. **Stage 1（决策 JSON）**——模板选型原因、参数映射、输出契约、静态检查项（含 `prompt_template_type_aligned`）
2. **Stage 2（最终产物）**——模板/配置内容、集成代码片段、验收 walkthrough

### 支持的模板类型

| 模板类型 | 适用算子 | 说明 |
|----------|----------|------|
| `DIYPromptABC` | `PromptedGenerator`、`PromptedFilter`、`PromptedRefiner` 等 | 完全自定义 system/user prompt，支持字段插值 |
| `FormatStrPrompt` | `FormatStrPromptedGenerator` | 使用 Python f-string 风格的多字段模板 |

### Stage 1 决策 JSON 格式

```json
{
  "prompt_template_type_aligned": "DIYPromptABC",
  "strategy": "单字段生成，使用 system+user 双层提示词",
  "argument_mapping": {
    "product_name": "商品名",
    "category": "品类"
  },
  "output_contract": "中文，不超过 80 字，以卖点句式结尾",
  "static_checks": [
    "无多余占位符",
    "语气符合专业定义",
    "字数约束可在 Stage 2 walkthrough 中核验"
  ]
}
```

核心规则：
- `prompt_template_type_aligned` 必须与目标算子的契约匹配，不可混用
- `static_checks` 中每一项必须在 Stage 2 验收 walkthrough 中一一核验
- 参数映射需与 `Arguments` 字段完全对应，不可遗漏

---

## `dataflow-dev`

DataFlow 开发专家技能，加载完整架构知识并路由到七个专项工作流——涵盖新建算子/Pipeline/Prompt、诊断报错、代码规范审查，以及在上游仓库发生变更时同步知识库。

### 功能说明

在 DataFlow 仓库中调用 `/dataflow-dev` 后，该技能将：

1. 加载 `context/knowledge_base.md`——架构说明、API 参考、所有已注册算子
2. 加载 `context/dev_notes.md`——开发规范、最佳实践、LLM 响应容错模板
3. 加载 `diagnostics/known_issues.md`——结构化"症状 → 根因 → 修复"诊断数据库
4. 探测本地仓库状态（`git branch`、`git log`、`git diff`）
5. 输出 1–3 行上下文摘要，然后路由到对应工作流

### 快速上手

#### 1. 添加 Skill

```bash
git clone https://github.com/haolpku/DataFlow-Skills.git

# 项目级（仅当前项目可用）
cp -r DataFlow-Skills/dataflow-dev .claude/skills/dataflow-dev

# 或个人级（所有项目可用）
cp -r DataFlow-Skills/dataflow-dev ~/.claude/skills/dataflow-dev
```

#### 2. 打开 DataFlow 仓库

```bash
cd /path/to/DataFlow    # 必须是仓库根目录
claude                  # 启动 Claude Code
```

#### 3. 调用 Skill

```
/dataflow-dev
我需要一个新的 filter 算子，过滤掉词数少于 N 的文本。
```

技能会自动识别意图、检查是否有重复算子、一轮询问规格细节，然后生成完全符合规范的代码。

### 七个子命令工作流

| 意图关键词 | 工作流 |
|---|---|
| 新建算子 / new operator / create operator | 算子创建（重复性检查 → 规格确认 → 代码生成 → 注册提醒） |
| 新建 Pipeline / new pipeline | Pipeline 创建（算子选择 → 按 `storage.step()` 模式生成代码） |
| 新建 Prompt / new prompt | Prompt 创建（PromptABC 或 DIYPromptABC、注册装饰器、`@prompt_restrict` 位置） |
| 报错 / error / KeyError / AttributeError / Warning | 诊断（匹配 known_issues.md → 根因 + 修复示例代码） |
| 审查 / review / check / 规范检查 | 代码审查（算子与 Pipeline 双 checklist，共 14 项校验） |
| 更新知识库 / sync / check updates / 仓库有新算子 | 知识库更新（检测新算子文件、与 knowledge_base.md 对比、给出更新步骤） |

### 算子创建硬性规范 Checklist

每次生成算子代码前，系统会逐项验证以下规范：

```
✓ 继承 OperatorABC，调用 super().__init__()
✓ 类上方有 @OPERATOR_REGISTRY.register() 装饰器
✓ run() 参数命名：input_* / output_* / storage
✓ run() 返回输出 key 列表
✓ storage.read() 和 storage.write() 都存在
✓ LLM 驱动算子：成员变量必须命名为 self.llm_serving
✓ 对每条 LLM 返回值单独 try/except，失败有合理默认值
✓ CoT 模型输出：在不需要保留推理链的字段中剥离 <think> 标签
✓ @staticmethod get_desc(lang: str = "zh")，支持 zh/en
✓ __init__.py 的 TYPE_CHECKING 块已注册
```

### 诊断速查表

| 报错关键词 | 对应 Issue |
|---|---|
| `Unexpected key 'xxx' in operator` | #001 — 配置参数命名（仅警告，非报错） |
| `No object named 'Xxx' found in 'operators' registry` | #002 — `__init__.py` TYPE_CHECKING 块缺少声明 |
| `Key Matching Error` / `does not match any output keys` | #003 — Pipeline key 不一致 |
| `You must call storage.step() before` | #004 — 缺少 `storage.step()` 调用 |
| `DummyStorage` + `AttributeError` | #005 — DummyStorage API 限制 |
| `AttributeError: 'NoneType'` + `re.split` | #006 — `re.split()` pattern 中使用了捕获组 |
| `@prompt_restrict` 不生效 | #007 — 装饰器必须紧贴类定义上方 |

完整根因分析与修复示例见 `diagnostics/known_issues.md`。

### 知识库更新流程

当上游仓库（`OpenDCAI/DataFlow`）合入新算子 PR 时：

```bash
# 查看上游最近合并的 PR
gh pr list --repo OpenDCAI/DataFlow --state merged --limit 20

# 检测本地仓库新增的算子文件（最近 30 次提交）
git log --oneline --diff-filter=A -- 'dataflow/operators/**/*.py' | head -30

# 或者直接运行内置辅助脚本
bash .claude/skills/dataflow-dev/scripts/check_updates.sh /path/to/DataFlow
```

脚本输出：新增算子文件、所有已注册算子名、未在 `knowledge_base.md` 中出现的算子，以及上游最近 PR/Issue——并附带分步更新指引。

### 文件结构

```
dataflow-dev/
├── SKILL.md                        # Skill 定义与子命令路由
├── context/
│   ├── knowledge_base.md           # 架构、API 参考、所有算子（只读参考）
│   └── dev_notes.md                # 开发规范、最佳实践（可追加）
├── diagnostics/
│   └── known_issues.md             # 结构化 Issue 数据库 #001–#008
├── templates/
│   ├── operator_template.py        # 算子骨架模板
│   ├── pipeline_template.py        # Pipeline 骨架模板
│   └── prompt_template.py          # Prompt 骨架模板
└── scripts/
    └── check_updates.sh            # 仓库变更感知与知识库差异检测脚本
```

### 上游仓库

本技能中的所有知识对齐自 **[OpenDCAI/DataFlow](https://github.com/OpenDCAI/DataFlow)**（`main` 分支，v1.0.10）。
