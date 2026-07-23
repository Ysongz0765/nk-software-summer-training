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

## AI 模块

- `POST /api/v1/ai/extract-tasks`
- `POST /api/v1/ai/check-missing`
- `POST /api/v1/ai/generate-report`

## 模板模块

- `POST /api/v1/templates`
- `GET /api/v1/templates`
- `GET /api/v1/templates/{template_id}`

## 报表模块

- `POST /api/v1/reports`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{report_id}`
- `PUT /api/v1/reports/{report_id}`
- `POST /api/v1/reports/{report_id}/versions`
- `GET /api/v1/reports/{report_id}/versions`

## 导出模块

- `POST /api/v1/reports/{report_id}/export`

当前仅返回 JSON/TXT 占位导出结果。
