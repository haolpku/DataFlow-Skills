---
name: dataflow-webui-dev
description: >
  DataFlow WebUI 全栈开发专家。当用户需要修改 DataFlow-WebUI（前端 Vue3 或后端 FastAPI）时触发。
  涵盖：新增页面/组件、修改 API 接口、扩展 Pinia 状态、更新路由、修复 UI 交互 bug。
  Trigger: user wants to modify DataFlow-WebUI source code, add features to the web interface,
  fix frontend/backend bugs, add new API endpoints, or extend the UI.
version: 1.0.0
---

# DataFlow WebUI 开发助手 (dataflow-webui-dev)

## 激活时必须执行的步骤

1. **加载知识库**：读取 `${SKILL_DIR}/context/knowledge_base.md`（架构概览 + 关键文件路径）
2. **加载已知问题**：读取 `${SKILL_DIR}/diagnostics/known_issues.md`
3. **确认工作目录**：
   ```bash
   ls /data/workspace/df_web_and_skills/DataFlow-WebUI/
   ```
4. 向用户简报当前上下文（1-2 行）

---

## 子命令路由

| 用户意图 | 执行流程 |
|---|---|
| 新增前端页面 / 组件 | → [前端页面开发流程](#前端页面开发流程) |
| 新增后端 API / 端点 | → [后端 API 开发流程](#后端-api-开发流程) |
| 修改现有功能 / 修复 bug | → [修改现有代码流程](#修改现有代码流程) |
| 扩展 Serving / Dataset / Pipeline 管理 | → [管理界面扩展流程](#管理界面扩展流程) |
| 报错 / 接口 500 / 前端白屏 | → [诊断流程](#诊断流程) |
| 同步 api.js / 更新接口客户端 | → [API 客户端同步流程](#api-客户端同步流程) |

---

## 前端页面开发流程

### Step 1: 读取关键文件

```
前端根: /data/workspace/df_web_and_skills/DataFlow-WebUI/frontend/src/
路由:    frontend/src/router/index.js
布局:    frontend/src/views/manage/ (各管理页面)
Store:   frontend/src/stores/dataflow.js (主 Pinia store)
API客户端: frontend/src/axios/api.js (自动生成，勿手改主体)
```

### Step 2: 遵循项目约定

**文件放置规范**：
- 新管理页面 → `frontend/src/views/manage/{feature}/index.vue`
- 新 store → `frontend/src/stores/{feature}.js`
- 公共组件 → `frontend/src/components/`

**Vue 风格**：
- 本项目混用 Options API（manage 页面）和 Composition API（stores）
- 管理页面统一使用 **Options API**（与 serving/index.vue 一致）
- 使用 VFluent3 组件库（`fv-*` 前缀），参考 `serving/index.vue` 中的组件用法
- 从 `mapState(useAppConfig, ['local'])` 获取 i18n 文本
- 从 `mapState(useTheme, ['theme', 'color', 'gradient'])` 获取主题

**API 调用规范**：
- 通过 `this.$api.{module}.{method}()` 调用（Options API 中）
- 通过 `proxy.$api.{module}.{method}()` 调用（Composition API store 中）
- 检查 `res.code === 200` 判断成功（不是 `res.success`）
- 错误时调用 `this.$barWarning(msg, { status: 'warning' })`

### Step 3: 添加路由

编辑 `frontend/src/router/index.js`，在对应父路由的 `children` 中添加：
```js
{
  path: 'feature',
  name: 'feature',
  component: () => import('@/views/manage/feature/index.vue')
}
```

### Step 4: 侧边栏导航（如需要）

查看 `frontend/src/layout/` 下的 Sidebar 组件，添加导航入口。

---

## 后端 API 开发流程

### Step 1: 了解项目结构

```
后端根:    /data/workspace/df_web_and_skills/DataFlow-WebUI/backend/
主入口:    backend/app/main.py
路由注册:  backend/app/api/v1/router.py
端点目录:  backend/app/api/v1/endpoints/{module}.py
服务层:    backend/app/services/{service}.py
数据模型:  backend/app/schemas/{module}.py
容器(DI):  backend/app/core/container.py
配置:      backend/app/core/config.py
数据存储:  backend/data/ (YAML 平文件)
```

### Step 2: 创建新端点的标准步骤

1. **定义 Schema**：在 `backend/app/schemas/{module}.py` 创建 Pydantic 模型
2. **创建服务层**（如需要）：在 `backend/app/services/` 添加业务逻辑
3. **创建端点**：在 `backend/app/api/v1/endpoints/{module}.py` 添加路由
4. **注册路由**：在 `backend/app/api/v1/router.py` 中 include router
5. **更新 api.js**：见 [API 客户端同步流程](#api-客户端同步流程)

**端点模板**（参考 `${SKILL_DIR}/templates/endpoint_template.py`）：
```python
from fastapi import APIRouter, HTTPException
from app.core.container import container
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse

router = APIRouter(tags=["feature"])

@router.get("/", response_model=ApiResponse[List[FeatureSchema]])
def list_items():
    try:
        items = container.feature_registry._get_all()
        return ok(items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**响应格式规范**：
- 成功：`return ok(data)` → `{"code": 200, "data": ..., "message": "success"}`
- 404：`raise HTTPException(status_code=404, detail="...")`
- 500：`raise HTTPException(status_code=500, detail=str(e))`

### Step 3: 数据存储约定

- 持久化数据用 YAML 平文件，存 `backend/data/{feature}.yaml`
- 格式：`{ "{uuid_hex}": { "name": "...", ...fields } }`
- ID 生成：`os.urandom(8).hex()`
- 参考 `backend/app/services/serving_registry.py` 作为 Registry 模式模板

---

## 修改现有代码流程

### Step 1: 先读文件，再修改

修改任何文件前**必须**先用 Read 工具读取完整文件，确认当前内容。

### Step 2: 关键文件一览

| 文件 | 用途 | 注意事项 |
|---|---|---|
| `backend/app/api/v1/endpoints/serving.py` | Serving CRUD | `_mask_key` 处理 api_key 脱敏 |
| `backend/app/services/serving_registry.py` | Serving 存储 | `_get()` 需 null-check，已修复 |
| `frontend/src/views/manage/serving/index.vue` | Serving UI | Options API，`checkAdd/Edit` 只检查 `required` 字段 |
| `frontend/src/stores/dataflow.js` | 全局 Pinia store | 含 `agentSyncPayload` 供 agent 桥接 |
| `frontend/src/axios/api.js` | API 客户端 | **自动生成，不要手动修改主体逻辑** |
| `backend/app/core/container.py` | 依赖注入容器 | 新服务需在此注册 |

### Step 3: DF_API_KEY 约定

- 存储：`api_key` 字段存入 serving YAML
- 注入：运行时以 `os.environ[f"DF_API_KEY_{serving_id}"]` 注入
- 测试端点：`os.environ[f"DF_API_KEY_{id}"]`（已与 engine/Ray 统一）
- **禁止**使用裸 `"DF_API_KEY"` 环境变量名

---

## 管理界面扩展流程

已有管理界面参考（均在 `frontend/src/views/manage/`）：
- `serving/index.vue` — CRUD + 折叠卡片模式
- `dataset/index.vue` — 列表 + 预览模式
- `pipeline/index.vue` — DAG 编辑器集成

新建管理界面推荐：
1. 复制 `serving/index.vue` 作为起点
2. 修改 API 调用、数据结构、字段渲染
3. 保持折叠卡片（`fv-Collapse`）风格一致

---

## 诊断流程

1. 读取报错信息，在 `diagnostics/known_issues.md` 中匹配
2. 若命中，直接给出根因 + 解决方案
3. 若未命中，结合知识库中的架构知识分析
4. **后端 500 排查**：先看 uvicorn 日志，关注 `TypeError` 和 `KeyError`
5. **前端接口不通排查**：`api.js` 方法名对应 FastAPI `operation_id`

**快速匹配表**：

| 现象 | 根因 | 解决 |
|---|---|---|
| 已有 serving 看不到 | `_get()` null-check 崩溃（旧版本）| 已修复：`_get()` 加了 null-check |
| 新建 serving 后 Confirm 按钮灰色 | `checkAdd()` 对非必填参数 falsy 误判 | 已修复：仅检查 `param.required` |
| 测试 serving 报错 / API key 无效 | `DF_API_KEY` 环境变量名不一致 | 已修复：统一为 `DF_API_KEY_{id}` |
| 前端调用 API 返回 422 | Query/Body 参数传递方式不对 | 对照 `api.js` 中 `params` vs `data` 字段 |
| 新端点在 api.js 中找不到 | openapijs 未重新生成 | 见 API 客户端同步流程 |
| `key_name_of_api_key` 被用户提交 | create 端点校验用了错误变量名（旧版本）| 已修复：`pname` 替代 `name` |

---

## API 客户端同步流程

`frontend/src/axios/api.js` 是从 OpenAPI 规范自动生成的，**不要手动修改其主体逻辑**。

当后端新增/修改接口后，需要重新生成：

1. 确保后端服务运行中（port 8000）
2. 获取 OpenAPI 规范：`curl http://localhost:8000/openapi.json > /tmp/openapi.json`
3. 使用 openapijs 工具重新生成 `api.js`（参考项目 README 或 devdocs 目录）
4. 提交生成后的 `api.js`

**临时快速修改方式**（仅在 openapijs 不可用时）：
- 可在 `api.js` 末尾类定义之外手动添加新方法
- 保持与现有方法结构一致：`static async method_name(params, ...)`

---

## 持续修改代码的工作模式

Agent 可在一次会话中持续修改代码，建议工作方式：

1. **先读后写**：每次修改前用 Read 确认文件当前状态
2. **增量修改**：优先用 Edit（diff 方式），避免全文件覆盖写入
3. **前后端分离验证**：
   - 后端改动：重启 uvicorn，用 `curl` 验证接口
   - 前端改动：Vite HMR 自动热更新，刷新浏览器即可
4. **不要跨会话保留假设**：每次会话开始重新读取关键文件
5. **避免修改自动生成文件**：`api.js` 主体逻辑由工具生成，手改会被下次生成覆盖
