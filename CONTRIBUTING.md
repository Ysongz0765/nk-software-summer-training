# 贡献指南

ReportFlow AI 使用单仓库协作。当前阶段以清晰边界、可运行骨架和 Mock 联调为优先。

## 分支规则

- `main`：稳定版本，只接收经过评审的合并。
- `develop`：日常集成分支。
- `feature/backend-core`：成员 A 维护后端基础设施与集成。
- `feature/frontend`：成员 B 维护前端页面与交互。
- `feature/ai`：成员 C 维护 OCR、AI 抽取、补充追问与生成逻辑。
- `feature/export`：成员 D 维护模板解析与导出逻辑。

## Pull Request 规则

1. PR 必须说明变更范围、验证方法和潜在影响。
2. 不提交真实密钥、密码或个人数据库连接。
3. 后端变更至少运行 `pytest`，前端变更至少运行类型检查。
4. 模块之间通过 `ReportContent`、`TaskItem` 等公共结构交互，避免跨模块读取内部实现。
5. 数据库变更以 MySQL 8.4 为正式环境，SQLite 为自动化测试环境，并通过 Alembic 管理表结构。

## Commit Message

推荐格式：

- `feat: add report mock endpoint`
- `fix: handle validation error response`
- `docs: update api specification`
- `refactor: split ai service interface`
- `test: add mock ai service test`
- `chore: update docker compose`
