# TriggerFlow Canvas 测试指南

## 自动化测试矩阵

| 范围 | 工具 | 命令 | 覆盖内容 |
| ---- | ---- | ---- | -------- |
| 前端单测 | Vitest + Testing Library | `npm --prefix triggerflow_canvas/frontend run test:run` | 组件渲染、节点选择与拖拽交互 |
| 后端单测 | pytest | `pytest tests/triggerflow_canvas/backend` | 工作流 CRUD、执行流程与日志流接口 |
| 端到端 | Playwright | `npm --prefix triggerflow_canvas/frontend run e2e` | 节点添加、拖拽、属性配置、保存与执行全流程 |
| 代码规范 | ESLint / Ruff | `npm --prefix triggerflow_canvas/frontend run lint` / `ruff check .` | TypeScript/React 代码风格及 Python 静态检查 |
| 构建校验 | Docker | `docker build -f docker/Dockerfile .` | 镜像构建成功，确保部署入口完整 |

> 在 CI 中上述命令会按顺序执行，确保基础质量门槛。

## 手动验证步骤

以下步骤用于重大版本发布前的快速巡检：

1. **启动服务**
   - 后端：`uvicorn triggerflow_canvas.backend.main:app --reload`
   - 前端：`npm --prefix triggerflow_canvas/frontend run dev`
2. **画布交互**
   - 在节点库点击“HTTP 触发器”，确认画布出现节点并自动选中。
   - 拖动节点，确认位置更新且属性面板保持同步。
3. **属性配置**
   - 在属性面板修改 `path` 字段，确认输入被保存并在节点重新选中时回显。
4. **流程保存 / 加载**
   - 编辑名称和描述后点击“保存流程”，确认右侧列表出现新卡片。
   - 刷新页面后从列表点击“加载”，验证节点与属性恢复正确。
5. **执行与日志**
   - 点击“执行流程”，在“运行日志”区域确认出现开始与完成日志。
   - 执行结束后再次点击应重新触发日志流，无前端错误提示。
6. **清理与删除**
   - 使用“清空画布”按钮恢复初始状态。
   - 在“已保存流程”卡片点击“删除”，确认数据被移除且无残留日志。

执行过程中如遇异常，请记录浏览器控制台与后端日志，便于回归分析。
