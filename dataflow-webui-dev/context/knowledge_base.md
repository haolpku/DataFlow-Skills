# DataFlow WebUI 知识库

## 一、项目总体结构

```
DataFlow-WebUI/
├── frontend/                    # Vue 3 + Vite 前端
│   └── src/
│       ├── axios/api.js         # 自动生成的 API 客户端（勿手改）
│       ├── stores/
│       │   ├── dataflow.js      # 主 Pinia store（operators/serving/pipeline/tasks）
│       │   ├── appConfig.js     # i18n 本地化
│       │   └── theme.js         # 主题（dark/light）
│       ├── views/manage/        # 各管理页面
│       │   ├── serving/         # Serving 管理
│       │   ├── dataset/         # Dataset 管理
│       │   ├── pipeline/        # Pipeline DAG 编辑器
│       │   ├── task/            # 任务执行监控
│       │   └── analysis/        # 分析 Dashboard
│       ├── router/index.js      # Vue Router 路由
│       └── components/          # 公共组件
└── backend/                     # FastAPI 后端
    └── app/
        ├── main.py              # 应用入口，CORS/挂载 MCP
        ├── api/v1/
        │   ├── router.py        # 路由聚合
        │   └── endpoints/       # 各功能端点
        │       ├── serving.py
        │       ├── datasets.py
        │       ├── pipelines.py
        │       ├── tasks.py
        │       ├── operators.py
        │       └── prompts.py
        ├── services/            # 业务服务层
        │   ├── serving_registry.py
        │   ├── dataflow_engine.py
        │   └── ray_pipeline_executor.py
        ├── schemas/             # Pydantic 数据模型
        └── core/
            ├── config.py        # 配置（BASE_DIR, YAML 路径等）
            └── container.py     # 依赖注入容器
```

## 二、API 响应格式

所有 API 统一用 `ok()` 包装返回：
```json
{ "code": 200, "data": <payload>, "message": "success" }
```

前端判断：`if (res.code === 200)` 或 `if (res.data)`（部分旧代码）。

## 三、Serving 模块详解

### 后端关键逻辑

- **Registry YAML 路径**：`backend/data/serving_registry.yaml`
- **格式**：`{ "<8字节hex ID>": { "name": "...", "cls_name": "...", "params": [...] } }`
- **`_get()` 方法**：需 null-check（已修复）
- **`_update()` 方法**：按参数名合并，不替换整个 params 数组

### api_key 安全处理

- 展示时：`api_key` 值被脱敏为 `"abc****xyz"`，附加 `masked: true`
- 编辑时：前端发送含 `****` 的值，后端跳过该参数（不覆盖已存储的真实值）
- 运行时：`os.environ[f"DF_API_KEY_{serving_id}"] = api_key_val`

### 前端展示逻辑

- `checkAdd()`：只对 `param.required === true` 且值为空时阻止提交
- `checkEdit()`：同上，且跳过 `param.masked === true` 的参数
- `resetEditParams(item, overide=true)`：首次加载时以当前值为默认值基准

## 四、Pipeline 执行模块

- Ray 分布式执行：`RayPipelineExecutor`
- `max_concurrency = 1`（限制同时运行 1 个 pipeline）
- 状态轮询：`GET /api/v1/tasks/{task_id}`
- operators_detail 格式：`{ "<op_name>": { "index": N, "status": "pending|running|completed|failed" } }`

## 五、Pinia Store 核心字段

```js
// useDataflow store
operators          // 算子列表（从 /api/v1/operators 加载）
groupOperators     // 按 level_1 分组的算子
servingList        // Serving 实例列表（已注入 key/text 字段）
currentServing     // 当前选中的 Serving
datasets           // Dataset 列表
pipelines          // Pipeline 列表
tasks              // 任务执行记录
execution          // 当前执行详情
executionStep      // 当前执行步骤索引
agentSyncPayload   // Agent→DAG 编辑器桥接 payload
```

## 六、VFluent3 常用组件

| 组件 | 用途 | 示例属性 |
|---|---|---|
| `fv-Collapse` | 折叠面板 | `:title`, `:content`, `:max-height` |
| `fv-button` | 按钮 | `:theme`, `:background`, `:disabled`, `border-radius` |
| `fv-text-box` | 输入框 | `v-model`, `:disabled`, `:reveal-border` |
| `fv-combobox` | 下拉选择 | `v-model`, `:options`（需含 `key`/`text` 字段） |
| `fv-list-view` | 列表 | `v-model`, `:options` |

## 七、环境变量与配置

| 变量 | 说明 |
|---|---|
| `DF_API_KEY_{serving_id}` | API LLM Serving 的 key（正确格式） |
| `BASE_DIR` | backend 目录的父目录 |
| `SERVING_REGISTRY` | serving_registry.yaml 路径 |
| `DEFAULT_SERVING_FILLING` | True = 自动填充 serving 配置默认值 |

## 八、已知修复记录（本次会话）

1. `serving_registry.py _get()` — 添加 null-check，防止 `TypeError: 'NoneType' object`
2. `serving_registry.py _update()` — 修复 `name` 变量遮蔽（改为 `pname`）
3. `serving.py create_serving_instance()` — 校验使用 `pname` 替代 `name`
4. `serving.py test_serving_instance()` — `key_name_var` 统一为 `f"DF_API_KEY_{id}"`
5. `serving/index.vue checkAdd/checkEdit()` — 只对 `param.required` 字段验空
