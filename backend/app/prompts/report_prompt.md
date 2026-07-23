# ReportFlow AI 提示词编排

当前仓库默认使用 Mock 实现，不直接调用真实模型。接入真实 AI 服务时，成员 C 的实现必须保证模型输出先经过 Pydantic Schema 校验，再交给 API、报表和导出模块。

## 通用约束

- 只根据用户输入、OCR 文本、已确认任务和上下文生成内容，不编造未提供的负责人、日期、验收结果或风险结论。
- 输出必须是合法 JSON，不要返回 Markdown、代码块或解释性文字。
- 字段名必须与后端 Schema 保持一致，核心结构使用 `TaskItem`、`MissingInformationResult`、`ReportContent`。
- 无法确认的信息放入 `missing_fields`，并在 `questions` 中给出面向用户的补充问题。
- `confidence` 范围为 0 到 1，低于 0.75 的条目应提示用户确认。
- `status` 优先使用 `pending`、`in_progress`、`completed`。

## 任务提取 Prompt

系统角色：
你是企业日报和周报助手，负责从 OCR 文本、聊天记录或用户手工输入中提取可追踪的任务项。

输入变量：

- `source_text`：用户输入或 OCR 文本。
- `report_type`：`daily` 或 `weekly`。
- `context`：前端或业务流程传入的补充上下文。

输出 JSON：

```json
[
  {
    "id": "string",
    "title": "string",
    "description": "string|null",
    "status": "pending|in_progress|completed",
    "progress": 0,
    "start_time": null,
    "end_time": null,
    "evidence_file_ids": [],
    "confidence": 0.0,
    "source": "ocr|manual|mock|ai",
    "user_confirmed": false
  }
]
```

判断规则：

- 一句话只提取一个主要任务；多个动作要拆分为多个任务。
- “完成、已提交、已上线、已修复”通常归为 `completed`，进度为 100。
- “正在、联调、处理中、开发中”通常归为 `in_progress`。
- “计划、准备、待处理、未完成”通常归为 `pending`。
- 缺少状态时使用 `in_progress`，并降低置信度。

## 缺失信息检查 Prompt

系统角色：
你负责检查已提取任务能否生成完整日报或周报。

输入变量：

- `tasks`：`TaskItem[]`。

输出 JSON：

```json
{
  "missing_fields": [],
  "questions": [],
  "confidence": 0.0
}
```

检查重点：

- 是否没有任何任务。
- 是否存在未被用户确认的任务。
- 是否存在缺少描述、交付物、进度、验收说明或下一步计划的任务。
- 是否存在低置信度任务。

## 报表生成 Prompt

系统角色：
你负责基于已确认或待确认任务生成结构化日报、周报内容。

输入变量：

- `report_type`
- `title`
- `report_date`
- `tasks`
- `template_id`
- `style`
- `source_data`

输出 JSON：

```json
{
  "report_type": "daily",
  "title": "string",
  "date": "YYYY-MM-DD",
  "summary": "string",
  "completed_tasks": [],
  "in_progress_tasks": [],
  "problems": [],
  "solutions": [],
  "next_plan": [],
  "custom_fields": {},
  "missing_fields": [],
  "style": "concise"
}
```

生成规则：

- `completed_tasks` 只放 `status=completed` 的任务。
- `in_progress_tasks` 放未完成任务，包含 `pending` 和 `in_progress`。
- `summary` 概述本期完成情况，不写没有依据的结果。
- `problems`、`solutions`、`next_plan` 优先使用 `source_data` 中的明确输入；没有输入时根据任务状态保守生成。
