# dataflow-operator-builder

[← 返回 DataFlow-Skills](../README_zh.md) | English: [README.md](./README.md)

用于生成自定义算子（`generate/filter/refine/eval`）。

## 这个 Skill 适合什么场景

- 你要新建一个 DataFlow 算子包，而且希望它一开始就是"可运行、可测试、可接入"的工程形态，不只是一个临时类文件。
- 你希望团队内多个算子的目录结构、CLI 入口、测试基线保持一致，减少后续维护成本。

## 一次生成后你会拿到什么

- 一个完整的算子实现骨架（`generate` / `filter` / `refine` / `eval` 之一）。
- `cli/` 下独立的命令行入口，方便直接跑批处理或联调，不用再手写胶水代码。
- `unit/registry/smoke` 三类基础测试文件，便于快速接入 CI 做最小验收。

## 实际工作流程（通常是这样）

1. 先用 spec 描述算子契约：包名、算子类型、类名/模块名、输入输出字段、是否用 LLM。
2. Skill 按 `references/` 里的约束做检查，尽量提前暴露注册、契约、命名等常见问题。
3. 先 `--dry-run` 看计划，再真正写入文件，避免误覆盖现有代码。
4. 你补充业务逻辑后，直接跑生成的测试和 CLI，快速验证端到端是否通。

## 入口方式

- 对话入口：`/dataflow-operator-builder`
- 指定 spec：`/dataflow-operator-builder --spec path/to/spec.json --output-root path/to/repo`

## 最小 spec 示例

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

## 输入字段要求

- 必填：`package_name`、`operator_type`、`operator_class_name`、`operator_module_name`、`input_key`、`output_key`、`uses_llm`。
- 常见可选：`cli_module_name`、`test_file_prefix`、`overwrite_strategy`、`validation_level`。

## 一个具体例子（自然语言）

- 比如你要加一个 `filter` 算子，在昂贵生成前先过滤低质量样本。
- 这个 Skill 能把目录、注册、CLI、测试脚手架一次搭好，你主要只需要关注过滤规则本身。
- 这样能把"工程搭建时间"压到最低，把精力放在业务逻辑上。

## 常用参数

- `--dry-run`：只展示创建/更新计划，不落盘。
- `--overwrite {ask-each,overwrite-all,skip-existing}`：控制覆盖行为，适合已有仓库渐进接入。
- `--validation-level {none,basic,full}`：选择校验严格度。

## 最小运行命令

```bash
python dataflow-operator-builder/scripts/build_operator_artifacts.py \
  --spec /tmp/operator_spec.json \
  --output-root . \
  --dry-run
```
