# TriggerFlow Canvas v1.0.0

## 发布亮点
- 后端 API 删除流程接口改用无内容响应并显式返回 `204`，修复了 FastAPI 对返回体的校验错误，确保流程删除请求能够正常注册。 
- `RunRepository` 现支持按需创建数据库会话，后台执行流程会自动获取新会话写入日志；同时工作流查询改为使用 `scalars()`，避免 SQLModel 返回行对象带来的字段访问异常。
- 工作流与运行记录的 JSON 字段改用 `MutableDict`/`MutableList`，日志追加和流程定义更新将立即持久化并正确反映在事件流中。
- 测试夹具升级为异步 `pytest_asyncio` fixture，使用共享的内存 SQLite 引擎复刻生产生命周期，覆盖完整的流程 CRUD、执行与日志流式验证。
- 模块导出 `triggerflow_canvas.__version__ = "1.0.0"`，新增 `rich` 依赖并将 `uvicorn[standard]` 升级到 `0.38.x`，为终端渲染与最新 MCP 客户端提供支撑，同时启用 `pytest asyncio` 自动模式以精简异步测试配置。

## 兼容性
- 新增运行时依赖：`rich>=13.9.0,<14.0.0`。
- ASGI 服务依赖调整为 `uvicorn[standard]>=0.38.0,<0.39.0`，需确认部署环境允许升级。
- 触发流数据库字段依赖 `sqlalchemy.ext.mutable`，确保镜像/环境包含对应包（随 SQLAlchemy 一并提供）。

## 测试结果
- ✅ `pytest tests/triggerflow_canvas -q`
- ❌ `pytest`（7 项失败：未配置 DeepSeek 环境变量导致的 ModelRequester 用例、MCP 服务器连接失败、Prompt 生成器断言差异）

## 已知问题
- 全量测试中的 OpenAI-Compatible/DeepSeek 相关用例需要 `DEEPSEEK_BASE_URL/DEEPSEEK_API_KEY/DEEPSEEK_DEFAULT_MODEL` 等环境变量，当前环境缺失导致失败。
- MCP 功能测试依赖本地 `./cal_mcp_server.py` 及外部模型服务，在 CI/沙箱中会因网络不可达而失败。
- Prompt 生成器断言与实际输出存在额外 `options` 字段差异，需后续与产品确认预期结构。
- 容器内缺少 Docker 引擎，无法在当前环境执行 `docker build`。若需产出镜像，请在具备 Docker 的构建机重复上述命令。
