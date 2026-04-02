# DataFlow-Skills

用于 DataFlow 工作流的可复用 Agent Skills。

English version: [README.md](./README.md)

---

## `generating-dataflow-pipeline`

视频教程: [Generate Pipeline](https://github.com/user-attachments/assets/ca1fefbf-9bf7-469f-b856-b201952fb99b)

一款基于推理引导的 pipeline 规划工具，可根据任务描述与样本数据生成标准的 DataFlow pipeline 代码。

### 功能说明

给定**目标任务**（pipeline 需实现的功能）和**样本JSONL文件**（1–5条代表性数据行），该工具将执行以下操作：
1. 读取并分析样本数据——推断字段类型、内容特征与任务属性
2. 依据强制决策表，从六大核心原语算子中选取合适算子（需要时可使用扩展算子）
3. 校验算子链路中的字段依赖关系
4. 输出两阶段结果：先输出中间算子决策（JSON格式），再生成完整可运行的Python pipeline代码

### 快速上手

#### 1. 安装 Claude Code

通过以下任一方式安装 [Claude Code](https://claude.ai/code)：

- **命令行**：`npm install -g @anthropic-ai/claude-code`
- **桌面应用**：支持 Mac 和 Windows
- **IDE 插件**：支持 VSCode 等

#### 2. 添加 Skill

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

#### 3. 准备数据

创建 JSONL 文件（每行一个 JSON 对象），包含 1–5 条代表性数据：

```jsonl
{"product_name": "笔记本电脑", "category": "电子产品"}
{"product_name": "咖啡机", "category": "家用电器"}
```

#### 4. 运行 Skill

在 Claude Code 中调用 `/generating-dataflow-pipeline` 并描述你的目标：

```
/generating-dataflow-pipeline
目标：生成商品描述并筛选优质内容
样本文件：./data/products.jsonl
预期输出字段：generated_description, quality_score
```

#### 5. 查看输出

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

用于生成自定义算子（`generate/filter/refine/eval`）。

### 这个 Skill 适合什么场景

- 你要新建一个 DataFlow 算子包，而且希望它一开始就是"可运行、可测试、可接入"的工程形态，不只是一个临时类文件。
- 你希望团队内多个算子的目录结构、CLI 入口、测试基线保持一致，减少后续维护成本。

### 一次生成后你会拿到什么

- 一个完整的算子实现骨架（`generate` / `filter` / `refine` / `eval` 之一）。
- `cli/` 下独立的命令行入口，方便直接跑批处理或联调，不用再手写胶水代码。
- `unit/registry/smoke` 三类基础测试文件，便于快速接入 CI 做最小验收。

### 实际工作流程（通常是这样）

1. 先用 spec 描述算子契约：包名、算子类型、类名/模块名、输入输出字段、是否用 LLM。
2. Skill 按 `references/` 里的约束做检查，尽量提前暴露注册、契约、命名等常见问题。
3. 先 `--dry-run` 看计划，再真正写入文件，避免误覆盖现有代码。
4. 你补充业务逻辑后，直接跑生成的测试和 CLI，快速验证端到端是否通。

### 入口方式

- 对话入口：`/dataflow-operator-builder`
- 指定 spec：`/dataflow-operator-builder --spec path/to/spec.json --output-root path/to/repo`

### 最小 spec 示例

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

### 输入字段要求

- 必填：`package_name`、`operator_type`、`operator_class_name`、`operator_module_name`、`input_key`、`output_key`、`uses_llm`。
- 常见可选：`cli_module_name`、`test_file_prefix`、`overwrite_strategy`、`validation_level`。

### 一个具体例子（自然语言）

- 比如你要加一个 `filter` 算子，在昂贵生成前先过滤低质量样本。
- 这个 Skill 能把目录、注册、CLI、测试脚手架一次搭好，你主要只需要关注过滤规则本身。
- 这样能把"工程搭建时间"压到最低，把精力放在业务逻辑上。

### 常用参数

- `--dry-run`：只展示创建/更新计划，不落盘。
- `--overwrite {ask-each,overwrite-all,skip-existing}`：控制覆盖行为，适合已有仓库渐进接入。
- `--validation-level {none,basic,full}`：选择校验严格度。

### 最小运行命令

```bash
python dataflow-operator-builder/scripts/build_operator_artifacts.py \
  --spec /tmp/operator_spec.json \
  --output-root . \
  --dry-run
```

---

## `prompt-template-builder`

用于为已有算子构建/修订 DataFlow prompt 模板或配置（按算子契约对齐类型）。

### 这个 Skill 适合什么场景

- 你已经有算子了，但 prompt 效果不稳定，或者输出经常不符合领域化预期，需要系统化改写。
- 你不只想"改一句提示词"，还希望保留清晰的决策依据，方便代码评审和回溯。

### 它和普通 prompt 改写的区别

- 会先根据算子契约判断应该用哪种模板形式（例如 `DIYPromptABC` 或 `FormatStrPrompt`），避免模板类型与算子不匹配。
- 输出分成两个阶段，先解释"为什么这么做"，再给"最终可落地内容"。

### 两阶段输出在实际协作中的价值

1. Stage 1（决策 JSON）：把模板选择原因、参数映射、输出契约、静态检查项讲清楚，便于评审。
2. Stage 2（最终产物）：给出模板/配置内容、集成片段和验收 walkthrough，便于开发和测试直接接手。

### 入口方式

- 对话入口：`/prompt-template-builder`
- 指定 spec：`/prompt-template-builder --spec path/to/prompt_spec.json`

### 最小 spec 示例

```json
{
  "Target": "生成简洁的电商商品卖点",
  "OP_NAME": "PromptedGenerator",
  "Constraints": "语气专业；中文不超过80字",
  "Arguments": ["product_name", "category"]
}
```

### 输入字段要求

- 必填：`Target`、`OP_NAME`。
- 建议补充：`Constraints`、`Expected Output`、`Arguments`、`Sample Cases`、`Tone/Style`、`Validation Focus`。

### 一个具体例子（自然语言）

- 例如你的 `PromptedGenerator` 负责生成电商卖点，但经常超字数、语气飘忽。
- 你把"目标、字数限制、语气要求、示例输入"告诉这个 Skill，它会给出契约对齐的模板方案和对应验收点。
- 这样你可以更快判断：新模板是否真的把长度和风格稳定下来，而不是靠反复手调。

### 期望输出形态

- Stage 1：决策记录（策略、映射、检查项，含 `prompt_template_type_aligned`）。
- Stage 2：实现内容（模板/配置、集成说明、验收 walkthrough）。
