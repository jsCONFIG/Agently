# TriggerFlow Canvas 迭代任务清单

| 编号 | 优先级 | 任务 | 描述 | 交付物 | 状态 |
| ---- | ------ | ---- | ---- | ------ | ---- |
| TF-P0-001 | P0 | 修复 Poetry 锁文件失效 | 当 `poetry install` 与锁文件不一致时给出更新指引，并在预检脚本中提示。 | 用户指南章节 + 预检脚本输出 | ✅ 完成 |
| TF-P0-002 | P0 | npm 受限网络处理方案 | 在文档中补充镜像/代理配置，并在预检脚本中检测 npm 可用性。 | 用户指南章节 | ✅ 完成 |
| TF-P1-003 | P1 | 环境预检 CLI | 提供 `python -m triggerflow_canvas.connector.preflight` 命令检查 Poetry/Node/npm/Docker。 | CLI 工具 + 测试 | ✅ 完成 |
| TF-P1-004 | P1 | 节点调试器 | 在 `TriggerFlowConnector` 中支持节点调试覆盖、日志增强，并暴露 `NodeDebugger`。 | 代码实现 + 自动化测试 | ✅ 完成 |
| TF-P2-005 | P2 | 版本追踪与发布说明 | 建立 release note 并更新测试/用户指南，附带调试流程截图。 | 文档更新 | ✅ 完成 |

> 若需新增任务，请在表格下方以相同格式追加，并同步更新 `docs/evaluations/python-ai-dev.md` 中的优先级列表。
