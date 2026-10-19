# Agent 工程化设计导读

[返回首页](../README.md) · [架构设计](architecture.md) · [API](api.md)

## 1. 从问题到统一参数

参数解析使用中英文名称映射，将 voltage / 电压等名称归一化为统一字段，提取数值和可选单位。随后合并 `context.parameters`，同名字段以结构化上下文为准。

```mermaid
flowchart LR
    Q["自然语言问题"] --> Regex["PARAMETER_PATTERN"]
    Regex --> Names["PARAMETER_NAMES 名称映射"]
    Names --> Values["数值转 float / 保存单位字段"]
    Context["context.parameters"] --> Merge["合并参数 · context 优先"]
    Values --> Merge
    Merge --> State["parsed_parameters"]
    State --> Tool["validate_parameter_range"]
```

设计关注点是输入归一化与优先级规则。通用范围按字段约定的单位解释，数值范围规则与名称解析分别定义在工具层和工作流层。

## 2. 检索证据如何进入方案

检索使用 `device_type` 约束知识范围，再对提取的字母/数字词项执行故障码与症状匹配；没有匹配结果时，读取同类型案例。每次最多五条。

```mermaid
flowchart TB
    Query["question / device_type"] --> Terms["提取长度大于 2 的字母数字词项"]
    Terms --> Search["设备类型 AND 故障码/症状匹配"]
    Search --> Found{"有结果？"}
    Found -->|否| Fallback["读取同类型知识条目"]
    Found -->|是| Evidence["knowledge · 最多 5 条"]
    Fallback --> Evidence
    Evidence --> Hypothesis["fault_analysis · 首条原因形成假设"]
    Evidence --> Safe["前 2 条 safe_action"]
    Evidence --> Sources["全部检索条目的来源引用"]
    Safe --> Plan["plan_generation"]
    Sources --> Plan
```

知识引用格式为 `[source:fault_code]`。知识条目的安全动作形成建议步骤；工具范围反馈形成风险警告，两类输入在方案生成阶段承担不同职责。

## 3. 工具调用契约

工作流在 `tool_dispatch` 中构造三项调用规格，并按顺序交给注册表调度。每项调用记录名称、参数和结果，便于将工具执行过程与用户可读方案分开展示。

```mermaid
sequenceDiagram
    participant W as tool_dispatch
    participant D as execute_tool
    participant R as TOOL_REGISTRY
    participant S as AgentState
    W->>D: name + arguments
    D->>R: 按名称查找 Callable
    R-->>D: 工具函数
    D-->>W: result dict
    W->>W: 汇总 ToolCall
    W->>W: 读取参数 violations
    W->>S: tool_calls / warnings / trace
```

扩展工具时，先定义清晰的字典入参和返回字段，再注册函数，并在节点中提供调用规格。该边界让工具实现与图结构保持分离。

## 4. 校验—反思—重生成

`result_validation` 检查步骤数量、停止条件和需要反思的参数反馈。路由规则为：

```text
validation_errors 非空 且 reflected 为 false → reflection
其他情况 → END
```

反思节点设置标志并记录 `retried`。方案生成节点读取该标志，在安全状态步骤之后增加停止调整与专业复核提示。再次校验后按同一路由规则结束，参数警告继续保留。

| 状态字段 | 用途 |
| --- | --- |
| validation_errors | 当前校验问题 |
| reflected | 限制单次请求的反思次数 |
| warnings | 保留参数风险反馈 |
| trace | 记录回路经过的节点、状态与摘要 |

这是针对规则反馈的有界修正设计，重点在于可解释条件、保留风险和明确停止行为。

## 5. 运行记录与过程查看

```mermaid
sequenceDiagram
    participant U as API Client
    participant A as FastAPI
    participant G as LangGraph
    participant DB as AgentRun
    U->>A: POST /api/v1/runs
    A->>G: invoke(initial_state)
    G-->>A: 最终共享状态
    A->>DB: 保存 request / result / trace
    A-->>U: 202 + run_id / plan / tool_calls / trace
    U->>A: GET /runs/{run_id}/trace
    A->>DB: 按 UUID 查询
    DB-->>A: 有序事件
    A-->>U: node / status / summary
```

## 6. 场景阅读

以下文件为接口输入示例，适合对照分支条件阅读源码：

- [debug_request.json](../examples/debug_request.json)：问题描述中的电流与频率，加上结构化上下文中的电压。
- [reflection_request.json](../examples/reflection_request.json)：电压输入超过通用范围，用于理解校验反馈及反思路径。
- [knowledge_case.json](../examples/knowledge_case.json)：结构化知识条目的字段关系。

推荐讲解顺序：状态图说明控制流，状态表说明数据流，工具注册表说明扩展边界，反思条件说明纠错设计，运行记录说明可观测性。
