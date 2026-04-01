# 生成 dataflow pipeline

[← 返回 DataFlow-Skills](../README_zh.md) | English: [README.md](./README.md)

一款基于推理引导的 pipeline 规划工具，可根据任务描述与样本数据生成标准的 DataFlow pipeline 代码。

## 功能说明
给定**目标任务**（pipeline 需实现的功能）和**样本JSONL文件**（1–5条代表性数据行），该工具将执行以下操作：
1. 读取并分析样本数据——推断字段类型、内容特征与任务属性
2. 依据强制决策表，从六大核心原语算子中选取合适算子
3. 校验算子链路中的字段依赖关系
4. 输出两阶段结果：先输出中间算子决策（JSON格式），再生成完整可运行的Python pipeline代码

## 快速上手
按以下格式提交需求：
```
目标：生成商品描述并筛选优质内容
样本文件：./data/products.jsonl
预期输出字段：generated_description, quality_score
```

样本文件必须为**JSONL格式**（每行一个JSON对象），而非JSON数组：
```jsonl
{"product_name": "笔记本电脑", "category": "电子产品"}
{"product_name": "咖啡机", "category": "家用电器"}
```

工具将返回以下内容：
1. **中间算子决策**——包含算子链路、字段流转逻辑与推理依据的JSON数据
2. **字段映射**——区分已有字段与需生成字段
3. **有序算子列表**——按执行顺序排列的算子及选用理由
4. **推理总结**——说明该设计为何能满足目标任务
5. **完整 pipeline 代码**——遵循标准结构的可执行Python全量代码
6. **可调参数/注意事项**——可配置参数与调试技巧

## 六大核心算子

| 算子名称 | 用途 | 是否依赖大语言模型（LLM） |
|----------|------|--------------------------|
| `PromptedGenerator` | 单字段大模型生成 | 是 |
| `FormatStrPromptedGenerator` | 多字段模板式生成 | 是 |
| `Text2MultiHopQAGenerator` | 从文本构建多跳问答对 | 是 |
| `PromptedFilter` | 基于大模型的质量评分与筛选 | 是 |
| `GeneralFilter` | 基于规则的确定性过滤 | 否 |
| **KBC三算子组**（3个算子，需按固定顺序组合使用） | 文件/链接→Markdown→分块→清洗文本 | 部分依赖 |

### 算子选用优先级
工具遵循强制决策表规则——专用算子优先级始终高于通用算子：
- **从文本生成问答对**→选用`Text2MultiHopQAGenerator`（而非用`PromptedGenerator`搭配问答提示词）
- **文件路径/链接转文本**→选用KBC三算子组（而非用`PromptedGenerator`总结文件）
- **基于多字段评分**→选用`FormatStrPromptedGenerator`+`GeneralFilter`（而非仅支持单个`input_key`的`PromptedFilter`）
- **确定性规则过滤**→选用`GeneralFilter`（而非`PromptedFilter`）
- **基于多字段生成内容**→选用`FormatStrPromptedGenerator`（而非多个`PromptedGenerator`分步执行）

## 生成的 pipeline 结构
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

## 使用示例
完整工作流示例详见 [`examples/`](./examples/) 目录：

| 示例文件 | 实现模式 | 所用算子 |
|----------|----------|----------|
| [`basic_generate_and_filter.md`](./examples/basic_generate_and_filter.md) | 内容生成+质量筛选 | `PromptedGenerator` + `PromptedFilter` |
| [`multifield_scoring.md`](./examples/multifield_scoring.md) | 多字段评分 | `FormatStrPromptedGenerator` + `GeneralFilter` |
| [`multi_stage_pipeline.md`](./examples/multi_stage_pipeline.md) | 多阶段生成+筛选 | 多个`PromptedGenerator` + `GeneralFilter` |
| [`kbc_pdf_to_qa.md`](./examples/kbc_pdf_to_qa.md) | 文档处理+问答抽取 | KBC三算子组 + `Text2MultiHopQAGenerator` + `PromptedFilter` |

## 扩展算子（core_text模块）
除六大核心原语外，DataFlow还提供更多扩展算子，相关文档位于同级 [`core_text/`](../core_text/) 工具目录中。若核心算子无法满足任务需求，可参考以下文档：

**生成类算子**（`core_text/generate/`）——共8个：

| 算子名称 | 功能说明 |
|----------|----------|
| `PromptedGenerator` | 单字段大模型生成 |
| `FormatStrPromptedGenerator` | 多字段模板式生成 |
| `Text2MultiHopQAGenerator` | 多跳问答对抽取 |
| `BenchAnswerGenerator` | 基准测试答案生成（支持多种`eval_type`） |
| `ChunkedPromptedGenerator` | 长文档逐分块处理 |
| `EmbeddingGenerator` | 文本向量化（调用`/v1/embeddings`接口） |
| `RandomDomainKnowledgeRowGenerator` | 领域专属合成数据行生成 |
| `RetrievalGenerator` | 异步检索增强生成（RAG，需`await run()`） |

**过滤类算子**（`core_text/filter/`）——共3个：

| 算子名称 | 功能说明 |
|----------|----------|
| `GeneralFilter` | 基于规则的数据行过滤（lambda条件） |
| `KCenterGreedyFilter` | 基于多样性的下采样（需嵌入向量） |
| `PromptedFilter` | 大模型语义评分+数据筛选 |

**评估类算子**（`core_text/eval/`）——共5个：

| 算子名称 | 功能说明 |
|----------|----------|
| `BenchDatasetEvaluator` | 基准答案对比评估（精确匹配/语义匹配） |
| `BenchDatasetEvaluatorQuestion` | 带问题上下文的扩展基准评估 |
| `PromptedEvaluator` | 基于大模型的数据行评分（仅写入分数，不删除数据） |
| `Text2QASampleEvaluator` | 问答质量评估（4个维度，输出8列结果） |
| `UnifiedBenchDatasetEvaluator` | 统一基准评估（支持6种`eval_type`） |

**优化类算子**（`core_text/refine/`）——共2个：

| 算子名称 | 功能说明 |
|----------|----------|
| `PandasOperator` | 自定义DataFrame转换（不依赖大模型） |
| `PromptedRefiner` | 大模型文本优化（覆盖原字段） |

每个算子目录均包含`SKILL.md`（英文接口文档）、`SKILL_zh.md`（中文接口文档）、`examples/good.md`（最佳实践示例）与`examples/bad.md`（常见错误示例）。

## 新增算子
前置条件：新算子的工具定义文件已完成（包含`SKILL.md`、`examples/good.md`、`examples/bad.md`等）。

### 作为扩展算子添加

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

### 升级为核心原语算子（可选）
若某算子使用频率极高，需纳入优先选用范围，可通过修改`SKILL.md`完成升级：
1. **优选算子策略**——添加至核心原语列表
2. **算子选用优先级规则**——新增决策表条目（明确适用/不适用场景）
3. **算子参数签名规则**——补充完整构造函数与`run()`方法签名
4. **正确导入路径**——添加算子导入路径
5. **输入文件内容分析规则**——若支持新数据类型，补充输入模式匹配规则
6. **使用示例**——在`examples/`目录添加完整示例（推荐）

## 核心约束
- **仅支持JSONL格式**：输入必须为`.jsonl`文件，每行一个JSON对象
- **KBC三算子组必须完整使用**：三个步骤（`FileOrURLToMarkdownConverterFlash`→`KBCChunkGenerator`→`KBCTextCleaner`）需按固定顺序执行，不可跳过任一环节
- **`Text2MultiHopQAGenerator`输出嵌套列表**：`QA_pairs`字段每行存储字典列表，而非独立字段——下游算子无法直接引用`question`或`answer`作为字段名
- **`PromptedFilter`仅支持单字段**：多字段评估需先用`FormatStrPromptedGenerator`评分，再用`GeneralFilter`过滤
- **字段安全性**：`GeneralFilter`的lambda表达式仅可引用已存在的字段
