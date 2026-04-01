# core_text

[← 返回 DataFlow-Skills](../README_zh.md) | English: [README.md](./README.md)

[`generating-dataflow-pipeline`](../generating-dataflow-pipeline/README_zh.md) 的扩展算子参考库。

## 这是什么

pipeline 生成器使用的所有文本处理算子的逐算子 API 文档。当 `generating-dataflow-pipeline/SKILL.md` 中的 6 个核心算子不能满足需求时，可查阅这里的详细参考。

## 有哪些算子

**生成类** (`generate/`)
- `prompted-generator` - 最基础的 LLM 生成
- `format-str-prompted-generator` - 用模板生成
- `chunked-prompted-generator` - 长文本分块生成
- `embedding-generator` - 生成向量
- `retrieval-generator` - RAG 生成
- `bench-answer-generator` - 给 benchmark 生成答案
- `text2multihopqa-generator` - 生成多跳问答
- `random-domain-knowledge-row-generator` - 随机生成领域知识

**过滤类** (`filter/`)
- `prompted-filter` - 用 LLM 打分过滤
- `general-filter` - 按数值规则过滤
- `kcentergreedy-filter` - 按多样性过滤

**精炼类** (`refine/`)
- `prompted-refiner` - 用 LLM 改写文本
- `pandas-operator` - 自定义 pandas 操作

**评估类** (`eval/`)
- `prompted-evaluator` - LLM 打分
- `bench-dataset-evaluator` - 评估 benchmark 数据集
- `bench-dataset-evaluator-question` - 评估 benchmark 问题
- `text2qa-sample-evaluator` - 评估问答样本
- `unified-bench-dataset-evaluator` - 统一评估

## 怎么用

这些参考文档供 `generating-dataflow-pipeline` 在生成 pipeline 代码时查阅。每个算子文件夹里有：

- `SKILL.md` - 英文skill文档，描述算子使用场景，算子用法，算子导入，算子参数，算子运行示例。
- `SKILL_zh.md` - 中文文档
- `examples/good.md` - 正确用法示例，含单一算子的组成的简单pipeline示例，样例输入以及相应输出
- `examples/bad.md` - 常见错误汇总