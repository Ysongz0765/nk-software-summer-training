# 团队协作

## 分支

- `main`
- `develop`
- `feature/backend-core`
- `feature/frontend`
- `feature/ai`
- `feature/export`

## PR 规则

- 每个 PR 说明范围、影响和验证结果。
- 不提交真实密钥、数据库密码或个人连接串。
- 不在路由层堆大量业务逻辑。
- 后端涉及数据库变更时，需要说明 Alembic 迁移和 MySQL / SQLite 兼容性。

## 模块责任

- 成员 A：后端核心、数据库、部署、文档。
- 成员 B：前端页面、交互和编辑器。
- 成员 C：OCR、AI 提取、补充追问。
- 成员 D：模板解析、导出和文件生成。

## Mock 数据规则

- `samples/mock-tasks.json` 和 `samples/mock-report.json` 是共享联调源。
- 前端、后端和 AI 模块都应能使用同一份 Mock 数据。
