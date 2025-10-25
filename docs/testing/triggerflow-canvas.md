# TriggerFlow Canvas 测试指南

## 自动化测试矩阵

| 范围 | 工具 | 命令 | 覆盖内容 |
| ---- | ---- | ---- | -------- |
| 前端单测 | Vitest + Testing Library | `npm --prefix triggerflow_canvas/frontend run test:run` | 组件渲染、节点选择与拖拽交互 |
| 后端单测 | pytest | `pytest tests/triggerflow_canvas/backend` | 工作流 CRUD、执行流程与日志流接口 |
| 端到端 | Playwright | `npm --prefix triggerflow_canvas/frontend run e2e` | 节点添加、拖拽、属性配置、保存与执行全流程 |
| 代码规范 | ESLint / Ruff | `npm --prefix triggerflow_canvas/frontend run lint` / `ruff check .` | TypeScript/React 代码风格及 Python 静态检查 |
| 构建校验 | Docker | `docker build -f docker/Dockerfile .` | 镜像构建成功，确保部署入口完整 |
| 环境预检 | Python | `python -m triggerflow_canvas.connector.preflight` | 检测 Poetry/Node/npm/Docker 是否安装 |

> 在 CI 中上述命令会按顺序执行，确保基础质量门槛。

## 手动验证步骤

以下步骤用于重大版本发布前的快速巡检：

1. **运行环境预检**
   - 执行 `python -m triggerflow_canvas.connector.preflight`，确认所有必需工具可用；如缺失可根据输出提示安装或配置镜像。
2. **启动服务**
   - 后端：`uvicorn triggerflow_canvas.backend.main:app --reload`
   - 前端：`npm --prefix triggerflow_canvas/frontend run dev`
3. **画布交互**
   - 在节点库点击“HTTP 触发器”，确认画布出现节点并自动选中。
   - 拖动节点，确认位置更新且属性面板保持同步。
4. **属性配置**
   - 在属性面板修改 `path` 字段，确认输入被保存并在节点重新选中时回显。
5. **流程保存 / 加载**
   - 编辑名称和描述后点击“保存流程”，确认右侧列表出现新卡片。
   - 刷新页面后从列表点击“加载”，验证节点与属性恢复正确。
6. **执行与日志**
   - 点击“执行流程”，在“运行日志”区域确认出现开始与完成日志。
   - 执行结束后再次点击应重新触发日志流，无前端错误提示。
7. **离线调试验证**
   - 使用以下 Python 片段运行离线流程，确认 `NodeDebugger` 能捕获调试日志：
     ```python
     import asyncio
     from triggerflow_canvas.connector import NodeDebugger, run_workflow

     workflow = {
         "nodes": [
             {"id": "n1", "type": "llm", "label": "LLM", "configuration": {"model": "stub"}}
         ],
         "debug": {"nodes": {"n1": {"outputs": ["stub response"], "notes": "离线测试"}}}
     }

     async def main():
         debugger = NodeDebugger()
         async for message in run_workflow(workflow, debugger=debugger):
             print(message)
         print(debugger.as_dict())

     asyncio.run(main())
     ```
   - 确认终端输出包含“调试输出”和 `NodeDebugger` 事件。
8. **清理与删除**
   - 使用“清空画布”按钮恢复初始状态。
   - 在“已保存流程”卡片点击“删除”，确认数据被移除且无残留日志。

执行过程中如遇异常，请记录浏览器控制台与后端日志，便于回归分析。
