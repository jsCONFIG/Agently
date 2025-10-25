# TriggerFlow Canvas

TriggerFlow Canvas 是一个基于 Python 标准库 HTTP 服务与 React 可视化前端的工作流搭建项目，用于演示和体验 [Agently TriggerFlow](../agently/core/TriggerFlow) 引擎。通过拖拽节点、编辑配置并点击运行，用户可以在浏览器中快速构建线性工作流并即时执行。

## 功能特性
- 可视化画布：基于 React + ReactFlow 的拖拽连接体验，实时展示流程结构。
- 节点库：内置 Start、Echo、Uppercase、LLM（模拟）、Output 等常用节点类型，可扩展。
- 与 TriggerFlow 引擎对接：后端根据画布 JSON 动态构建并运行 TriggerFlow。
- 文件持久化：流程保存到 `TriggerFlowCanvas/data/flow.json`，刷新后自动恢复。
- Docker 支持：提供 Dockerfile 方便一键打包部署。

## 本地运行
1. 安装 Python 依赖（根目录）：

   ```bash
   pip install -e .[dev]
   ```

2. 安装前端依赖并构建静态资源：

   ```bash
   cd TriggerFlowCanvas/frontend
   npm install
   npm run build
   cd ../..
   ```

   > 如果希望联机调试前端，可运行 `npm run dev` 启动 Vite，本地 UI 会通过代理访问后端接口。

3. 启动内置 HTTP 服务：

   ```bash
   python -m TriggerFlowCanvas.backend.main
   ```

4. 浏览器访问 `http://127.0.0.1:8000/`，即可体验画布、保存及运行能力。

> **提示**：首次启动时会将 `data/default_flow.json` 复制为运行时流程。后续保存会覆盖 `data/flow.json`。

## 运行测试

```bash
pytest tests/triggerflow_canvas -vv
```

## Docker 打包

```bash
docker build -f TriggerFlowCanvas/Dockerfile -t triggerflow-canvas .
docker run -p 8000:8000 triggerflow-canvas
```

容器启动后同样访问 `http://127.0.0.1:8000/`。

## 目录结构
```
TriggerFlowCanvas/
├── backend/          # 基于标准库的服务与工具模块
├── data/             # 默认流程 & 持久化数据
├── docs/             # 产品、架构、测试文档
├── frontend/         # React + ReactFlow 前端项目（Vite 构建）
├── Dockerfile        # 统一镜像构建配置
└── README.md         # 使用说明
```

## 扩展建议
- 在 `backend/flow_builder.py` 中新增节点工厂扩展能力。
- 将 `FlowStorage` 替换为数据库，以支持多用户协作。
- 新增 WebSocket 接口实现执行过程流式反馈。

