# TriggerFlow Canvas Architecture

TriggerFlow Canvas 提供一个以 TriggerFlow Runtime 为核心的可视化流程编辑与执行体验。本章描述当前实现的真实架构、核心组件、数据流与扩展能力，帮助开发者快速理解系统边界并进行二次开发。

## 组件总览

| 组件 | 说明 | 主要技术栈 |
| --- | --- | --- |
| Canvas Web App | 负责节点拖拽、连线、属性编辑以及运行日志展示。 | React 18、Vite、React Flow、自定义样式 |
| Canvas API | 暴露流程 CRUD、执行、日志流接口，同时承载 TriggerFlow Runtime。 | FastAPI、SQLModel、SQLite、Server-Sent Events |
| TriggerFlow Connector | 将画布定义转换为 TriggerFlow 的 Python 流程，并在 Runtime 内顺序执行节点。 | `agently.core.TriggerFlow`, `TriggerFlowConnector` 自定义执行器 |
| Persistence Layer | 持久化画布蓝图与执行历史。 | SQLModel + SQLite（可扩展为 PostgreSQL） |

> 与早期方案相比，当前架构已将 TriggerFlow Runtime 内嵌到 API 服务中，不再依赖独立的“核心”容器或消息队列。

## 运行时集成

`TriggerFlowConnector` 的职责：

1. 校验画布 JSON：确保存在且仅存在一个入口节点、图结构为单链路、所有连线引用合法节点。
2. 为每个节点生成 `TriggerFlowChunk`，并根据连线顺序组装为 `TriggerFlow` 链式流程。
3. 通过 `TriggerFlowExecution` 的运行时流（runtime stream）推送日志，每个节点起止、产出结果均会写入 SSE 日志。
4. 在终止节点调用 `async_stop_stream()`，保证日志流能够正常结束。

目前内置节点类型：

- `trigger.http`：模拟 HTTP 请求触发，写入运行时数据并返回请求上下文。
- `action.chat_completion`：根据输入 prompt 生成可重复的演示响应，同时维护会话历史。
- `action.http_request`：返回模拟的 HTTP 请求响应，方便在无外部依赖的环境下验证流程。

扩展节点时，可在 `_execute_node` 中添加新的分支，并在前端模板里暴露配置字段。

## 数据流

1. **流程保存**：前端调用 `POST /api/workflows`（或 `PUT /api/workflows/{id}`），API 将节点与连线信息存入 `workflow_records` 表。
2. **触发执行**：`POST /api/workflows/{id}/execute` 会加载最新流程，交给 `RunManager` 创建运行记录。
3. **编译并执行**：`TriggerFlowConnector.compile` 构建运行计划；`execute` 则启动 TriggerFlow Runtime 并持续读取 runtime stream。
4. **日志推送**：`GET /api/runs/{run_id}/logs` 通过 SSE 将日志推送给前端，包括节点开始/结束、输出摘要、最终结果等。
5. **结果归档**：运行完成后，RunManager 更新 `run_records` 状态与累计日志，便于后续回放。

下图展示了主要调用链路：

```
+-------------+        REST         +-------------------+        Python API        +------------------+
|  Canvas UI  | ------------------> |   Canvas API      | ----------------------> | TriggerFlow Core |
| (React)     |    保存/执行请求    | (FastAPI + SQLite)|   构建并运行流程        |   (agently)      |
+-------------+ <------------------ +-------------------+ <---------------------- +------------------+
      ^                 SSE 日志               |                                   |
      |                                         | 运行记录 (SQLModel)              |
      +-----------------------------------------+----------------------------------+
```

## API 契约与事件

- `GET /api/workflows`：返回已保存的流程列表。
- `POST /api/workflows`：保存流程蓝图。
- `PUT /api/workflows/{id}`：更新流程。
- `DELETE /api/workflows/{id}`：删除流程。
- `POST /api/workflows/{id}/execute`：启动运行，返回 `runId`。
- `GET /api/runs/{runId}/logs`：SSE 日志流，JSON payload `{"message": "..."}`。

日志按时间顺序输出，包括：

1. `开始执行工作流...`
2. 每个节点的 `开始执行` 与 `输出` 日志。
3. `工作流执行结果`（汇总最终输出）。
4. `工作流执行完成。`

## 部署拓扑

开发与演示环境可直接使用仓库提供的 Docker Compose：

- `backend` 服务使用 `docker/Dockerfile` 构建镜像，包含 FastAPI、TriggerFlow Runtime 以及项目源代码。
- `frontend` 服务基于官方 Node 镜像运行 Vite 开发服务器，热更新画布界面。
- 两个服务通过共享卷访问源代码，便于本地调试；生产环境建议改为只读镜像并执行 `npm run build` 生成静态资源。

## 限制与扩展建议

- 仅支持单入口、顺序流程。未来若需要并行、条件分支，可在 `TriggerFlowConnector` 中利用 `TriggerFlowProcess.batch`、`side_branch` 等能力扩展。
- 目前未接入真实模型或外部 HTTP 服务，默认逻辑适合流程原型设计。接入真实服务时需考虑超时、错误处理与密钥管理。
- `NodeDebugger` 可在 Python 测试中捕获节点时间线；如需前端可视化，可在 SSE 数据中附带结构化信息供 UI 渲染。
- 若部署到生产，可将 SQLite 替换为 PostgreSQL，并在 `RunManager` 中引入持久队列以支持长时间运行的流程。

## 参考资料

- [TriggerFlow Canvas 用户指南](../user-guide/triggerflow-canvas.md)
- `triggerflow_canvas/backend/run_manager.py`：运行调度与日志管理实现。
- `triggerflow_canvas/connector/engine.py`：画布与 TriggerFlow 之间的适配层。
