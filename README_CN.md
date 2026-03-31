# DataFlow-Skills

用于 DataFlow 工作流的可复用 Agent Skills。

English version: [README.md](./README.md)

## Skills

- `generating-dataflow-pipeline`
  - 基于推理引导的流水线规划 Skill，可生成标准 DataFlow pipeline 代码。
- `dataflow-operator-builder`
  - 用于生成自定义算子（`generate/filter/refine/eval`）。
- `prompt-template-builder`
  - 用于为已有算子构建/修订 DataFlow prompt 模板或配置（按算子契约对齐类型）。

## 使用方式

### `dataflow-operator-builder`

这个 Skill 适合什么场景：
- 你要新建一个 DataFlow 算子包，而且希望它一开始就是“可运行、可测试、可接入”的工程形态，不只是一个临时类文件。
- 你希望团队内多个算子的目录结构、CLI 入口、测试基线保持一致，减少后续维护成本。

一次生成后你会拿到什么：
- 一个完整的算子实现骨架（`generate` / `filter` / `refine` / `eval` 之一）。
- `cli/` 下独立的命令行入口，方便直接跑批处理或联调，不用再手写胶水代码。
- `unit/registry/smoke` 三类基础测试文件，便于快速接入 CI 做最小验收。

实际工作流程（通常是这样）：
1. 先用 spec 描述算子契约：包名、算子类型、类名/模块名、输入输出字段、是否用 LLM。
2. Skill 按 `references/` 里的约束做检查，尽量提前暴露注册、契约、命名等常见问题。
3. 先 `--dry-run` 看计划，再真正写入文件，避免误覆盖现有代码。
4. 你补充业务逻辑后，直接跑生成的测试和 CLI，快速验证端到端是否通。

入口方式：
- 对话入口：`/dataflow-operator-builder`
- 指定 spec：`/dataflow-operator-builder --spec path/to/spec.json --output-root path/to/repo`

最小 spec 示例：

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

输入字段要求：
- 必填：`package_name`、`operator_type`、`operator_class_name`、`operator_module_name`、`input_key`、`output_key`、`uses_llm`。
- 常见可选：`cli_module_name`、`test_file_prefix`、`overwrite_strategy`、`validation_level`。

一个具体例子（自然语言）：
- 比如你要加一个 `filter` 算子，在昂贵生成前先过滤低质量样本。
- 这个 Skill 能把目录、注册、CLI、测试脚手架一次搭好，你主要只需要关注过滤规则本身。
- 这样能把“工程搭建时间”压到最低，把精力放在业务逻辑上。

常用参数：
- `--dry-run`：只展示创建/更新计划，不落盘。
- `--overwrite {ask-each,overwrite-all,skip-existing}`：控制覆盖行为，适合已有仓库渐进接入。
- `--validation-level {none,basic,full}`：选择校验严格度。

最小运行命令：

```bash
python dataflow-operator-builder/scripts/build_operator_artifacts.py \
  --spec /tmp/operator_spec.json \
  --output-root . \
  --dry-run
```

### `prompt-template-builder`

这个 Skill 适合什么场景：
- 你已经有算子了，但 prompt 效果不稳定，或者输出经常不符合领域化预期，需要系统化改写。
- 你不只想“改一句提示词”，还希望保留清晰的决策依据，方便代码评审和回溯。

它和普通 prompt 改写的区别：
- 会先根据算子契约判断应该用哪种模板形式（例如 `DIYPromptABC` 或 `FormatStrPrompt`），避免模板类型与算子不匹配。
- 输出分成两个阶段，先解释“为什么这么做”，再给“最终可落地内容”。

两阶段输出在实际协作中的价值：
1. Stage 1（决策 JSON）：把模板选择原因、参数映射、输出契约、静态检查项讲清楚，便于评审。
2. Stage 2（最终产物）：给出模板/配置内容、集成片段和验收 walkthrough，便于开发和测试直接接手。

入口方式：
- 对话入口：`/prompt-template-builder`
- 指定 spec：`/prompt-template-builder --spec path/to/prompt_spec.json`

最小 spec 示例：

```json
{
  "Target": "生成简洁的电商商品卖点",
  "OP_NAME": "PromptedGenerator",
  "Constraints": "语气专业；中文不超过80字",
  "Arguments": ["product_name", "category"]
}
```

输入字段要求：
- 必填：`Target`、`OP_NAME`。
- 建议补充：`Constraints`、`Expected Output`、`Arguments`、`Sample Cases`、`Tone/Style`、`Validation Focus`。

一个具体例子（自然语言）：
- 例如你的 `PromptedGenerator` 负责生成电商卖点，但经常超字数、语气飘忽。
- 你把“目标、字数限制、语气要求、示例输入”告诉这个 Skill，它会给出契约对齐的模板方案和对应验收点。
- 这样你可以更快判断：新模板是否真的把长度和风格稳定下来，而不是靠反复手调。

期望输出形态：
- Stage 1：决策记录（策略、映射、检查项，含 `prompt_template_type_aligned`）。
- Stage 2：实现内容（模板/配置、集成说明、验收 walkthrough）。

## 文件结构

```text
DataFlow-Skills/
├── README.md                                        # 仓库总览与快速导航（英文）
├── README_CN.md                                     # 仓库总览与快速导航（中文）
├── generating-dataflow-pipeline/                    # Skill：根据需求生成 DataFlow pipeline 代码
│   ├── SKILL.md                                     # Skill 主说明与执行流程
│   ├── examples/                                    # 端到端规划/输出示例
│   │   ├── basic_generate_and_filter.md             # 基础两阶段 generate+filter 示例
│   │   ├── kbc_pdf_to_qa.md                         # KBC 场景的 PDF-to-QA 流水线示例
│   │   ├── multi_stage_pipeline.md                  # 多阶段流水线编排示例
│   │   └── multifield_scoring.md                    # 多字段评分逻辑示例
│   └── templates/
│       └── pipeline_template.py                     # 该 Skill 输出的基础 Python pipeline 模板
├── dataflow-operator-builder/                       # Skill：生成生产级 DataFlow Operator 脚手架
│   ├── SKILL.md                                     # Operator 生成主流程说明
│   ├── assets/
│   │   └── templates/                               # 渲染生成 Operator 产物的代码模板集合
│   │       ├── cli/
│   │       │   └── operator_cli.py.tmpl            # 生成 Operator 的 CLI 入口模板
│   │       ├── operators/
│   │       │   ├── eval_operator.py.tmpl            # eval operator 实现模板
│   │       │   ├── filter_operator.py.tmpl          # filter operator 实现模板
│   │       │   ├── generate_operator.py.tmpl        # generate operator 实现模板
│   │       │   └── refine_operator.py.tmpl          # refine operator 实现模板
│   │       ├── package/
│   │       │   ├── cli_init.py.tmpl                 # CLI 模块的包初始化模板
│   │       │   ├── operator_pkg_init.py.tmpl        # operator 包初始化模板
│   │       │   ├── operators_root_init.py.tmpl      # operators 根包初始化模板
│   │       │   └── package_init.py.tmpl             # 顶层包初始化模板
│   │       └── tests/
│   │           ├── test_operator_registry.py.tmpl   # Operator 注册测试模板
│   │           ├── test_operator_smoke.py.tmpl      # 基础运行冒烟测试模板
│   │           └── test_operator_unit.py.tmpl       # Operator 行为单测模板
│   ├── references/                                  # 约束、契约和验收参考文档
│   │   ├── acceptance-checklist.md                  # 生成 Operator 的最终验收清单
│   │   ├── askuserquestion-rounds.md                # AskUserQuestion 协议与轮次结构
│   │   ├── cli-shell-guidelines.md                  # CLI 设计与 Shell 交互规范
│   │   ├── gotchas.md                               # 常见陷阱与实现注意事项
│   │   ├── operator-contract.md                     # Operator 接口与行为契约
│   │   ├── output-checklist.md                      # 输出完整性与质量检查清单
│   │   └── registration-rules.md                    # Operator 注册与发现规则
│   └── scripts/
│       ├── build_operator_artifacts.py              # Operator 产物模板渲染/构建脚本
│       └── example_spec.json                        # 构建脚本使用的输入规格示例
└── prompt-template-builder/                         # Skill：构建/修订 DataFlow prompt 模板或配置
    ├── SKILL.md                                     # 模板生成主流程与约束
    ├── examples/
    │   ├── filter_rewrite_finance.md                # 金融领域 filter/rewrite prompt 示例
    │   ├── multifield_scoring_prompt.md             # 多字段评分 prompt 示例
    │   └── single_field_generation.md               # 单字段生成 prompt 示例
    ├── references/
    │   ├── acceptance-checklist.md                  # prompt_template 输出验收标准
    │   ├── askuserquestion-rounds.md                # 本 Skill 的 AskUserQuestion 轮次协议
    │   ├── gotchas.md                               # 常见错误与边界情况
    │   ├── input-schema.md                          # 输入 schema 定义
    │   └── output-contract.md                       # 输出契约与格式要求
    └── templates/
        ├── decision_json_template.md                # 决策 JSON 输出模板
        ├── final_response_template.md               # 最终自然语言响应模板
        └── prompt_class_template.py.tmpl            # Python DIYPromptABC 类骨架（适用于兼容算子）
```
