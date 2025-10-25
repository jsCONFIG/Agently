# Python AI 开发体验报告

## 本地启动（Poetry + Node）
- **时间记录**：
  - 2025-10-25 10:11:51 执行 `poetry install`，3.5s 内结束，但由于 `pyproject.toml` 与 `poetry.lock` 差异过大直接失败，未安装依赖。
  - 2025-10-25 10:12:23 执行 `npm install`，0.8s 内因获取 `@playwright/test` 返回 403 Forbidden 失败。
- **问题**：
  - Poetry 提示需重新生成锁文件，否则无法继续安装，导致说明文档中的 `poetry install` 无法直接复现。
  - npm 访问被远端拒绝（403），需要额外的镜像或凭据才能下载依赖。
- **影响**：本地后端与前端均无法按照文档完成启动；需要手动调整依赖或配置私有源。

## Docker 启动
- **时间记录**：2025-10-25 10:12:31 执行 `docker compose up --build`，立即因环境缺少 docker 客户端而失败。
- **问题**：实验环境未预装 Docker，说明文档未提供替代方案或前置检查提示。

## 画布流程构建与执行验证
- 在无法启动前端的前提下，直接使用 `triggerflow_canvas.connector.run_workflow` 构造典型 AI 管线：HTTP 触发器 → LLM 回复 → Python 后处理。执行日志可正确按节点顺序输出，验证了画布蓝图到执行计划的编译与模拟执行链路。
- 该流程可作为日后接入真实模型推理与数据归档的基础骨架。

## 体验评价
- **易用性**：指令简洁，但关键依赖失败后缺乏退路说明；建议在文档中提供 `poetry lock` 更新指南与 npm 镜像配置示例。
- **性能**：编译与执行模拟步骤轻量、耗时可忽略；若能成功安装依赖，预计本地开发体验流畅。
- **文档**：TriggerFlow Canvas 指南结构清晰，但缺少常见错误（锁文件失效、受限网络下载 403、缺失 Docker）的排查章节。

## 改进建议
1. 在用户指南中加入环境前置检查脚本，自动检测 Docker、Poetry、Node 版本。
2. 提供 `poetry.lock` 重新生成与缓存依赖的官方流程，避免安装被动失败。
3. 为 npm 安装写明如何配置代理/镜像，或提供预打包的前端构建产物。
4. 增强 `TriggerFlowConnector` 的模拟执行，让 AI 节点可以插入可配置的伪响应，方便在离线环境验证链路。

## 优先级任务列表

| 优先级 | 问题 & 背景 | 解决方案概要 | 状态 | 负责人 |
| ------ | ------------ | ------------ | ---- | ------ |
| P0 | `poetry install` 与 `poetry.lock` 不一致导致依赖安装失败。 | 在用户指南加入锁文件更新流程，并提供自动化预检脚本提示需要重新生成锁。 | ✅ 已完成 | TriggerFlow Canvas 团队 |
| P0 | npm 403 导致前端依赖无法获取。 | 文档新增企业代理/镜像配置示例，并在预检脚本报告缺失的 npm。 | ✅ 已完成 | TriggerFlow Canvas 团队 |
| P1 | Docker 未安装且文档无替代方案。 | 发布命令行预检工具，输出 Docker 缺失的警告及替代启动建议。 | ✅ 已完成 | TriggerFlow Canvas 团队 |
| P1 | 无法在离线环境验证节点行为。 | 为 `TriggerFlowConnector` 增加节点调试覆盖与可视化日志。 | ✅ 已完成 | TriggerFlow Canvas 团队 |
| P2 | 缺乏集中任务追踪与版本结论。 | 创建 `docs/release-notes/triggerflow-canvas.md` 记录迭代结果并维护任务清单。 | ✅ 已完成 | TriggerFlow Canvas 团队 |

> 详细任务拆解见 `docs/product/triggerflow-canvas/backlog.md`。
