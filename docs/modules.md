# 模块说明与源码导读

[返回首页](../README.md) · [架构设计](architecture.md) · [业务导读](business-design.md)

## 建议阅读顺序

`schemas.py → workflow.py → tools.py / knowledge.py → service.py → main.py → db/models.py`

| 文件 | 核心对象 / 函数 | 负责内容 |
| --- | --- | --- |
| [app/schemas.py](../app/schemas.py) | DebugRequest、DebugPlan、ToolCall、TraceEvent、AgentRunResponse | 输入输出契约与字段约束 |
| [app/workflow.py](../app/workflow.py) | AgentState、build_workflow、PARAMETER_PATTERN | 节点、共享状态、主流程与条件边 |
| [app/tools.py](../app/tools.py) | TOOL_REGISTRY、execute_tool、PARAMETER_LIMITS | 工具接口与通用化检查规则 |
| [app/knowledge.py](../app/knowledge.py) | create_entry、search_entries | 案例入库、检索及引用内容 |
| [app/service.py](../app/service.py) | execute_run、get_run、get_trace | 图执行、结果汇总、持久化与查询 |
| [app/main.py](../app/main.py) | create_app、lifespan | 路由、数据库初始化与依赖注入 |
| [app/db/models.py](../app/db/models.py) | KnowledgeEntry、AgentRun | 知识及运行记录模型 |
| [app/db/session.py](../app/db/session.py) | create_database_engine、get_db | 引擎与请求会话 |
| [app/core/config.py](../app/core/config.py) | Settings、get_settings | 环境变量与配置校验 |
| [app/core/errors.py](../app/core/errors.py) | AppError、install_handlers | 业务异常与请求校验响应 |

## 节点输入输出

| 节点名称 | 主要读取 | 主要写入 |
| --- | --- | --- |
| intent | question | intent、trace |
| parameter_parse | question、context.parameters | parsed_parameters、trace |
| knowledge_retrieval | question、device_type | knowledge、trace |
| fault_analysis | knowledge | analysis、trace |
| tool_dispatch | parsed_parameters、question、knowledge | tool_calls、warnings、trace |
| plan_generation | knowledge、warnings、reflected | plan、trace |
| result_validation | plan、tool_calls、reflected | validation_errors、trace |
| reflection | trace | reflected、trace |

`_event` 创建新的轨迹列表；节点返回局部字段更新共享状态，保留其他阶段的结果。

## 工具接口

共同类型为 `Callable[[dict[str, Any]], dict[str, Any]]`。

| 工具名 | 主要参数 | 返回内容 |
| --- | --- | --- |
| validate_parameter_range | parameters | valid、violations，越界项包含名称、值、范围与单位 |
| query_fault_tree | symptom | fault_tree、requires_isolation |
| lookup_case_summary | knowledge_count | matched_cases、scope |

`execute_tool` 通过名称查询注册表；未知工具名返回 `tool_not_registered`。调用规格由工作流节点构造，工具结果保存为 `ToolCall`。

## 结构化结果

`DebugPlan` 将 `title`、`risk_level`、`steps`、`stop_conditions`、`citations` 独立建模。运行响应补充输入解析结果、工具调用、警告、节点轨迹与创建时间，使前端能够分别展示方案与执行过程。

## 测试源码导航

[tests/test_agent.py](../tests/test_agent.py) 包含主流程节点顺序、工具记录、参数越界反思、运行记录回查和结构化错误的断言，可用于阅读对应接口的预期行为。
