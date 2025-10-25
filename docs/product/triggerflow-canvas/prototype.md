# Triggerflow Canvas 原型说明

- 原型链接（Figma）：https://www.figma.com/proto/2P8uN0PZWnF3YwTqgkL9n3/Triggerflow-Canvas-MVP?page-id=0%3A1&type=design&node-id=1-230&viewport=318%2C144%2C0.12&scaling=min-zoom&starting-point-node-id=1%3A230
- 访问说明：链接已开放“可查看”权限，需使用公司邮箱账号登录 Figma 才可查看内部注释与交互动效。
- 包含页面：
  1. 流程画布与节点配置侧边栏
  2. 工作流运行监控仪表板
  3. 模板中心与流程导入对话框
- 关键交互：
  - 通过拖拽触发器、条件、动作节点至画布，点击连线形成执行路径。
  - 在节点详情侧边栏中配置触发条件、数据映射和动作参数，并可即时预览测试。
  - 在运行监控页面查看执行轨迹、失败节点高亮，并支持一键重试。
  - 模板中心可筛选、预览与导入模板，导入后直接进入画布编辑态。

## 模块对应帧索引
- **画布编辑器与画布服务**：`Canvas_Main`、`Node_Settings` 帧演示无限画布缩放、节点吸附、撤销重做提示条。
- **节点配置面板**：`Trigger_Config`, `Condition_Builder`, `Action_Test` 帧展示动态表单、条件构建器及测试运行面板。
- **数据映射与转换**：`Data_Mapping` 帧提供字段树拖拽、表达式编辑器、样本数据选择器的交互。
- **工作流执行引擎反馈**：`Run_Timeline` 帧模拟执行轨迹图与节点耗时 Tooltip。
- **版本管理与发布流**：`Version_Diff` 帧显示发布前差异对比与灰度开关设定。
- **运行监控与告警**：`Dashboard`、`Alert_Setup` 帧展示核心指标与告警渠道配置流程。
- **模板中心与协作**：`Template_List`, `Template_Import`, `Comments` 帧说明搜索过滤、导入检测、评论与 @ 成员体验。
- **接入与扩展**：`Connector_Vault`、`SDK_Onboarding` 帧覆盖凭证库状态与第三方节点提交流程。

如需查看交互动效，请在 Figma 原型中切换至 `Prototype` 模式并按 `Present` 预览。
