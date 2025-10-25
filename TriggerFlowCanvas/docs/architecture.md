# TriggerFlow Canvas 架构设计

## 1. 总览
TriggerFlow Canvas 由前端画布、标准库 HTTP 服务后端和 TriggerFlow 引擎适配层三部分构成：

```
┌─────────────────────────┐      ┌────────────────────┐      ┌────────────────────┐
│  Canvas 前端 (React)    │─────▶│  HTTP 服务 REST    │─────▶│  TriggerFlow Builder│
└─────────────────────────┘      └────────────────────┘      └────────────────────┘
          ▲                           │                            │
          │                           ▼                            ▼
          │                 Flow JSON / Persist              TriggerFlow Runtime
          │                           │                            │
          └───────────────◀──────────┴───────────────◀────────────┘
```

- 前端：基于 React + ReactFlow 的单页应用，实现节点拖拽、连接、配置以及执行触发。
- 后端：基于 `http.server` 的轻量服务，负责静态资源托管、流程保存/加载接口以及执行接口。
- 引擎适配层：`FlowBuilder` 负责把 JSON 定义映射为 TriggerFlow 可执行对象。

## 2. 模块划分
- `frontend/`：React + Vite 项目，包含基于 ReactFlow 的画布组件、节点库、Inspector 等。
- `backend/main.py`：标准库 HTTP 入口，定义 API 处理逻辑以及启动时的默认流程初始化。
- `backend/flow_builder.py`：把线性流程数据转成 TriggerFlow 链式调用，并提供内置节点工厂。
- `backend/schemas.py`：所有前后端交互结构的 Pydantic 定义，保证数据有效性。
- `backend/storage.py`：基于文件的流程持久化实现。
- `data/default_flow.json`：默认加载的示例流程；`data/flow.json`：运行时保存的用户流程。

## 3. 数据流与执行流程
1. 页面加载时，前端通过 `GET /api/flow` 获取当前流程并渲染。
2. 用户拖拽、配置并点击保存，前端将流程对象 `POST /api/flow`，后端通过 `FlowStorage` 写入磁盘。
3. 用户点击运行，前端 `POST /api/execute`，携带当前流程与用户输入。
4. 后端使用 `FlowBuilder` 校验流程合法性并构建 TriggerFlow：
   - 校验仅存在一个起始节点。
   - 校验无孤立节点、无分支。
   - 根据节点类型创建异步处理函数，拼接成链式 TriggerFlow。
5. 通过 TriggerFlow 执行并等待结果，返回最终输出与耗时统计。

## 4. 核心设计取舍
- **线性流程限制**：为了保证交互与后端适配的复杂度可控，本版本仅支持单链路流程。未来可通过扩展 `FlowBuilder` 与前端连线规则实现分支/并行。
- **React 前端实现**：选用 React + ReactFlow 提升画布交互体验，并通过 Vite 构建生成静态资源供 Python 服务托管。
- **文件持久化**：满足单机部署需求，后续可替换为数据库或云存储实现。

## 5. 安全与稳定性
- 前端仅允许创建限定类型节点，避免任意代码执行。
- 后端在 `FlowBuilder` 中对节点可达性、循环、非法节点类型进行校验，防止无效流程导致运行时异常。
- API 层对异常统一返回 400/500，并通过测试覆盖常见错误路径。

## 6. 扩展点
- 在 `create_builtin_registry` 中新增节点工厂即可扩展可选节点类型。
- `FlowStorage` 可替换为数据库实现；`FlowDefinition` 可加入版本、作者等字段实现协作。
- 可在后端服务中新增 WebSocket 路径以支持流式执行反馈。

