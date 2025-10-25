# TriggerFlow Canvas 迭代记录

## 版本概览
- **发布日期**：2025-10-25
- **范围**：本次迭代聚焦本地开发体验、离线调试能力与文档可操作性，解决体验报告中列出的高优先级问题。
- **结论**：所有阻塞项已解除，TriggerFlow Canvas 可在无 Docker 的受限环境下完成调试与回归测试。

## 关键改进
1. **环境预检 CLI**：新增 `python -m triggerflow_canvas.connector.preflight`，一次性检查 Poetry、Node.js、npm、Docker 安装状态，并输出友好提示。
2. **节点调试器与日志增强**：`TriggerFlowConnector` 支持节点级调试覆盖与 `NodeDebugger` 事件时间线，便于在缺失真实模型时验证流程。
3. **文档更新**：用户指南补充锁文件修复、npm 镜像配置、调试样例和新的调试日志截图；测试手册加入预检与离线调试步骤；评估报告新增优先级清单与任务链接。
4. **发布资产**：新增 `docs/product/triggerflow-canvas/backlog.md` 追踪任务，以及调试日志 SVG 截图用于对外展示。

## 测试与验证
- 自动化：`PYTHONPATH=. pytest tests/triggerflow_canvas/backend/test_connector_debug.py tests/triggerflow_canvas/backend/test_preflight.py`；同时执行 `python -m triggerflow_canvas.connector.preflight` 验证 CLI 输出。
- 手动：按照测试指南执行环境预检、前后端启动、画布交互与离线调试流程，确认日志输出符合预期。

## 后续展望
- 根据业务需求接入真实 LLM 服务，实现调试模式与线上推理的无缝切换。
- 在 CI 中集成预检脚本，提前暴露依赖缺失问题。
