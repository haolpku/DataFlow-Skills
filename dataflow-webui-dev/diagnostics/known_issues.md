# DataFlow WebUI 已知问题与诊断

## Issue #W001 — 已有 Serving 实例无法显示

**现象**：添加 Serving 后刷新页面看不到已有实例，或 list API 返回 500

**根因**：`serving_registry._get()` 在找不到 ID 时直接执行 `item['id'] = id`，
对 `None` 赋值触发 `TypeError: 'NoneType' object does not support item assignment`

**状态**：✅ 已修复（`serving_registry.py`，添加 null-check）

---

## Issue #W002 — Serving 编辑/新建 Confirm 按钮始终灰色

**现象**：参数都填了，但 Confirm 按钮还是不可点击

**根因**：`checkAdd()` / `checkEdit()` 对所有参数做 `if (!param.value)` 检查，
空字符串 `''` 和 `0`、`false` 都会返回 falsy，阻止提交

**状态**：✅ 已修复（`serving/index.vue`，只检查 `param.required === true` 的字段）

---

## Issue #W003 — Serving 测试返回 API Key 无效

**现象**：测试端点调用 LLM 时报 `Authentication failed` 或 key 不存在

**根因**：测试端点使用 `key_name_var = "DF_API_KEY"`（无 ID 后缀），
与 engine/Ray 使用的 `f"DF_API_KEY_{serving_id}"` 不一致，设置的是不同环境变量

**状态**：✅ 已修复（`serving.py`，改为 `f"DF_API_KEY_{id}"`）

---

## Issue #W004 — create_serving_instance 中 key_name_of_api_key 校验失效

**现象**：用户可以通过前端提交 `key_name_of_api_key` 参数，污染 serving 配置

**根因**：校验条件写为 `name == 'key_name_of_api_key'`，
`name` 在此作用域是外部函数参数（serving 实例名称），永远不等于该字符串

**状态**：✅ 已修复（`serving.py`，改为检查循环变量 `pname`）

---

## Issue #W005 — _update() 方法 name 变量遮蔽

**现象**：调试时发现 `_update(id, name=...)` 传入的 name 在某些情况下行为异常

**根因**：params 循环中 `name = new_p.get('name')` 覆盖了外层函数参数 `name`，
虽然 `if name: data[id]["name"] = name` 在循环前已执行，但代码易误导

**状态**：✅ 已修复（`serving_registry.py`，循环内改为 `pname`）

---

## Issue #W006 — api.js 与后端接口不同步

**现象**：前端调用某接口报 404 或方法不存在

**根因**：`api.js` 是从 OpenAPI 规范自动生成的，后端接口更新后 `api.js` 未重新生成

**解决**：
1. 确保后端运行中
2. `curl http://localhost:8000/openapi.json` 获取最新规范
3. 用 openapijs 重新生成 `api.js`，或手动在类末尾追加新方法

---

## Issue #W007 — 前端 422 Unprocessable Entity

**现象**：调用 POST/PUT 接口时 FastAPI 返回 422

**根因**：FastAPI 的参数来源（Query string vs Request Body）与 api.js 中 `params` vs `data` 字段不匹配

**排查步骤**：
1. 检查 FastAPI 端点参数是否用了 `Body(...)` 还是直接 query 参数
2. 对照 `api.js` 对应方法的 `params` 和 `data` 字段
3. 若端点参数需要改，同步修改 `api.js` 或后端接口
