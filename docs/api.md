# REST API 与数据契约

[返回首页](../README.md) · [架构设计](architecture.md)

基础路径：`http://127.0.0.1:8102/api/v1`。交互文档：`/docs`；OpenAPI：`/openapi.json`。契约源码：[schemas.py](../app/schemas.py)，路由源码：[main.py](../app/main.py)。

## 路由

| 方法与路径 | 返回模型 | 用途 |
| --- | --- | --- |
| GET /health | 服务状态对象 | 服务状态、运行计数 |
| POST /runs | AgentRunResponse，HTTP 202 | 请求内执行并保存工作流 |
| GET /runs/{run_id} | AgentRunResponse | 按 UUID 查询已保存结果 |
| GET /runs/{run_id}/trace | TraceEvent[] | 查询有序节点事件 |
| POST /knowledge/cases | KnowledgeRead，HTTP 201 | 新增结构化知识 |

## 调试请求

`DebugRequest`：

| 字段 | 类型与约束 | 说明 |
| --- | --- | --- |
| question | string，3—3000 字符 | 问题、告警和参数描述 |
| device_type | string，2—64 字符 | 默认 generic_drive |
| context | object | 可通过 parameters 提供结构化参数 |

```json
{
  "question": "驱动器启动时报过流告警，电流=24A，频率=50Hz，应该如何排查？",
  "device_type": "generic_drive",
  "context": {
    "parameters": {
      "voltage": 380.0
    }
  }
}
```

`context.parameters` 的同名字段覆盖文本提取值。调用返回完整结果后，可使用 `run_id` 继续查看记录。

```powershell
$base = "http://127.0.0.1:8102/api/v1"
$body = Get-Content -LiteralPath .\examples\debug_request.json -Raw -Encoding UTF8
$run = Invoke-RestMethod -Method Post -Uri "$base/runs" `
    -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body))
Invoke-RestMethod -Uri "$base/runs/$($run.run_id)"
Invoke-RestMethod -Uri "$base/runs/$($run.run_id)/trace"
```

## 响应字段

| 字段 | 内容 |
| --- | --- |
| run_id / created_at | UUID 与创建时间 |
| status / intent / device_type | 运行状态、意图分类与设备类型 |
| parsed_parameters | 归一化参数与单位字段 |
| plan | title、risk_level、steps、stop_conditions、citations |
| tool_calls | 工具 name、arguments、result |
| warnings | 风险提示列表 |
| trace | 有序 node、status、summary 事件 |

`TraceEvent.status` 为 `succeeded` 或 `retried`。轨迹接口返回相同的事件结构，工具参数与结果通过运行结果中的 `tool_calls` 阅读。

## 知识条目

`POST /knowledge/cases` 使用 `KnowledgeCreate`：

- device_type：设备类型，2—64 字符。
- fault_code：故障码，1—64 字符。
- symptom：症状，3—512 字符。
- probable_cause / safe_action：可能原因与安全动作，各 3—2000 字符。
- source：来源标识，2—128 字符。

返回字段增加 UUID `id`。请求示例见 [knowledge_case.json](../examples/knowledge_case.json)。

## 错误格式

业务错误与请求校验错误采用 `code`、`message`、`request_id`、`details` 结构。不存在的运行记录返回 HTTP 404 与 `run_not_found`；参数校验错误返回 HTTP 422 与字段详情。

## 集成建议

前端以 `run_id` 关联结果页和轨迹页；方案、工具明细与节点事件分别渲染。服务按 OpenAPI 数据模型交换数据，避免把节点摘要当作完整状态快照。
