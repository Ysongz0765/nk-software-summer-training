# API 说明

数据库从 PostgreSQL 切换为 MySQL 不改变现有 API 路径、请求结构和响应结构。

## 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## 健康检查

`GET /api/v1/health`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok",
    "service": "reportflow-api",
    "version": "0.1.0"
  }
}
```

## 文件模块

- `POST /api/v1/files/upload`
- `GET /api/v1/files/{file_id}`

`POST /api/v1/files/upload` 的 multipart form-data 现在支持可选字段
`project_id`。如果传入项目，后端会校验该项目属于当前登录用户，并在文件记录中保存
`project_id`。

## OCR 模块

- `POST /api/v1/ocr/recognize`
- `POST /api/v1/ocr/recognize-upload`
- `POST /api/v1/ocr/recognize-batch`
- `POST /api/v1/ocr/extract-tasks`
- `POST /api/v1/ocr/extract-tasks-upload`

`recognize-upload` 接收 multipart 图片或 PDF 文件并立即返回 OCR 结果；当前真实 PaddleOCR
provider 支持 `.png`、`.jpg`、`.jpeg`、`.pdf`。PDF 会先按页渲染成临时图片再识别。
`extract-tasks` 和 `extract-tasks-upload` 会先执行 OCR，再把识别文本交给 AI 模块提取
`TaskItem`。

`OCR_PROVIDER=qwen` 时，后端会调用 Qwen 多模态模型识别微信聊天记录、Git 截图、终端/IDE
截图等工作素材。Qwen provider 同样复用以上 OCR API，不改变前端上传接口。

## AI 模块

- `POST /api/v1/ai/extract-tasks`
- `POST /api/v1/ai/analyze-github-progress`
- `POST /api/v1/ai/check-missing`
- `POST /api/v1/ai/generate-report`

`POST /api/v1/ai/analyze-github-progress` 用于 GitHub API → DeepSeek 项目进度分析。

请求：

```json
{
  "repo_url": "https://github.com/owner/repo",
  "report_type": "daily",
  "max_items": 10
}
```

响应 `data`：

```json
{
  "repo_url": "https://github.com/owner/repo",
  "repository": {},
  "source_text": "GitHub 项目进度分析素材...",
  "tasks": []
}
```

后端会拉取仓库基本信息、最近 commits、issues、pull requests 和 languages，整理为
`source_text` 后调用 AI 任务提取。公开仓库可匿名访问；私有仓库或更高限额需配置
`GITHUB_API_TOKEN`。

`generate-report` 兼容原请求结构，并新增可选字段：

```json
{
  "project_id": 1,
  "start_date": "2026-07-24",
  "end_date": "2026-07-24",
  "file_ids": [1],
  "task_ids": [1],
  "user_notes": "本次重点"
}
```

传入 `project_id` 后，后端会构建 `source_data.project_context`，只读取当前项目的
任务、文件、历史报表、成员和项目记忆。

## 项目模块

- `POST /api/v1/projects`
- `GET /api/v1/projects?status=active`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `PUT /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/tasks`
- `GET /api/v1/projects/{project_id}/tasks`
- `GET /api/v1/projects/{project_id}/tasks/{task_id}`
- `PATCH /api/v1/projects/{project_id}/tasks/{task_id}`
- `DELETE /api/v1/projects/{project_id}/tasks/{task_id}`
- `POST /api/v1/projects/{project_id}/members`
- `GET /api/v1/projects/{project_id}/members`
- `PATCH /api/v1/projects/{project_id}/members/{member_id}`
- `DELETE /api/v1/projects/{project_id}/members/{member_id}`
- `GET /api/v1/projects/{project_id}/files`
- `GET /api/v1/projects/{project_id}/context`
- `POST /api/v1/projects/{project_id}/generate-summary`

项目接口必须登录。所有项目相关读取都会校验 `project.user_id == current_user.id`。
`DELETE /projects/{project_id}` 当前执行归档，将项目状态改为 `archived`，不会物理删除
文件、报表或模板。

## 模板模块

- `POST /api/v1/templates`
- `GET /api/v1/templates?project_id=1`
- `GET /api/v1/templates/{template_id}`

模板新增可选 `project_id`。`project_id = null` 表示全局模板；传入项目时，列表返回
用户全局模板和当前项目专属模板。

## 报表模块

- `POST /api/v1/reports`
- `GET /api/v1/reports?project_id=1`
- `GET /api/v1/reports/{report_id}`
- `PUT /api/v1/reports/{report_id}`
- `POST /api/v1/reports/{report_id}/versions`
- `GET /api/v1/reports/{report_id}/versions`

创建报表支持可选 `project_id`，列表支持按项目筛选，详情会返回 `project` 基本信息。

## 导出模块

- `POST /api/v1/reports/{report_id}/export`

当前支持 JSON、Word、Excel 和 PDF 导出。导出记录会继承报表的 `project_id`，
方便项目详情页查询导出历史。
