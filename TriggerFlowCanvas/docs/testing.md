# TriggerFlow Canvas 测试方案

## 1. 测试范围
- 后端 REST 接口的功能测试与错误处理。
- FlowBuilder 对流程定义的校验与执行结果。
- 前端交互通过文档说明手动验证关键路径（自动化测试留待后续扩展）。

## 2. 自动化测试
使用 `pytest` 编写的用例位于 `tests/triggerflow_canvas/`，覆盖：

1. **默认流程加载**：`GET /api/flow` 返回默认 JSON，节点数量正确。
2. **流程保存**：`POST /api/flow` 可写入临时文件并再次读取。
3. **流程执行**：对线性流程进行执行，验证输出为预期的 Echo + Uppercase 结果。
4. **错误流程校验**：构造包含分支的流程，期望 `/api/execute` 返回 400，提示不支持。

运行命令：

```bash
pytest tests/triggerflow_canvas -vv
```

## 3. 手工验证建议
- 在 ReactFlow 画布中拖拽节点位置，确认连线实时更新。
- 新增 LLM 节点并修改提示词，保存后刷新浏览器，配置仍然存在。
- 在右上角输入框填入执行文本，点击“Execute” 按钮，查看底部状态栏展示执行结果与耗时。

