# DataFlow-Skills

用于 DataFlow 工作流的可复用 Agent Skills。

English version: [README.md](./README.md)

## Skills

### [`generating-dataflow-pipeline`](./generating-dataflow-pipeline/README_zh.md)

基于推理引导的流水线规划 Skill，可生成标准 DataFlow pipeline 代码。给定业务目标和 JSONL 样本文件，从六大核心算子中选取合适算子，校验字段依赖，输出完整可执行的 Python pipeline。

入口：`/generating-dataflow-pipeline`

### [`dataflow-operator-builder`](./dataflow-operator-builder/README_zh.md)

用于生成自定义 DataFlow 算子（`generate/filter/refine/eval`）的脚手架 Skill。从 JSON spec 一次生成完整算子实现、CLI 封装和基线测试（`unit/registry/smoke`），让你专注于业务逻辑而非样板代码。

入口：`/dataflow-operator-builder`

### [`prompt-template-builder`](./prompt-template-builder/README_zh.md)

用于为已有算子构建/修订 DataFlow prompt 模板的 Skill。先检查算子兼容性，选择正确的模板形式（`DIYPromptABC` / `FormatStrPrompt`），返回可审计的两阶段输出（决策 JSON + 最终产物）。

入口：`/prompt-template-builder`

### [`core_text`](./core_text/README_zh.md)

[`generating-dataflow-pipeline`](./generating-dataflow-pipeline/README_zh.md) 的扩展算子参考库。记录了全部 18 个文本处理算子，涵盖四大类别：**生成类**（8 个）、**过滤类**（3 个）、**精炼类**（2 个）、**评估类**（5 个）。当 pipeline 生成器需要六大核心算子之外的算子细节时，会参考这些文档。
