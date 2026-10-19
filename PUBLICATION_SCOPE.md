# 公开内容与授权说明

本仓库中的公开代码、架构设计与技术文档由 **Hzhikai** 基于本人实际项目经验独立整理并授权发布，用于 LLM 应用开发交流、开源共同学习与求职作品展示。

## 公开工程内容

| 技术方向 | 公开内容 |
| --- | --- |
| Agent 编排 | LangGraph 状态图、七阶段主流程、条件边与反思节点 |
| 状态管理 | TypedDict 状态、上下文参数合并、节点增量更新 |
| 知识增强 | 结构化故障条目、设备类型检索、关键词匹配与来源引用 |
| 工具调用 | 命名注册表、统一调度、参数范围检查、故障树与案例汇总 |
| 反思纠错 | 结果校验、参数反馈、有界重生成与停止条件 |
| 工程接口 | FastAPI/OpenAPI、Pydantic 契约、运行记录与节点轨迹查询 |
| 工程组织 | 配置示例、Windows 脚本、示例输入、测试源码与架构文档 |

## 阅读与使用

建议从 [README](README.md)、[业务设计导读](docs/business-design.md)和[模块说明](docs/modules.md)阅读设计，再对照 [workflow.py](app/workflow.py) 与 [tools.py](app/tools.py) 查看实现。配置项由环境变量管理，见 [.env.example](.env.example)。

## 作者与许可证

Hzhikai 创作并发布的代码与文档采用 [MIT License](LICENSE)。第三方依赖遵循各自的上游许可证，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

欢迎阅读、引用、讨论和改进，并请保留作者与许可证信息。
