# ReportFlow AI 开发指南

## 1. 项目概述

ReportFlow AI 是一个面向日报、周报生成的网页平台，采用前后端分离和模块化单体架构。当前仓库提供 FastAPI 后端、Vue 3 前端、MySQL 数据库配置、Alembic 迁移、Docker Compose 编排和 Mock 服务骨架。

设计目标中的主要数据流：

用户输入或截图
→ OCR识别
→ 任务提取
→ 信息补充
→ 报表内容生成
→ 在线编辑
→ Word、Excel、PDF导出

当前代码中，OCR、AI、模板和导出模块已有可替换接口与 Mock 实现，但真实 OCR、真实 AI 服务、完整在线编辑和 Word、Excel、PDF 导出尚未完成。所有核心模块应围绕统一的 `TaskItem` 和 `ReportContent` 数据结构交互。

## 2. 技术栈

前端：

- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios

后端：

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2
- Alembic
- MySQL 8.4
- PyMySQL
- Pytest
- Ruff
- MyPy

部署：

- Docker Compose
- Nginx

## 3. 团队模块边界

成员A：

- `backend/app/core`
- `backend/app/api`
- `backend/app/models`
- `backend/app/repositories`
- `backend/alembic`
- `database`
- `deployment`
- 系统集成和公共接口

成员B：

- `frontend`
- 在线编辑
- 文件上传与预览
- 页面交互

成员C：

- `backend/app/services/ocr`
- `backend/app/services/ai`
- `backend/app/prompts`
- OCR、任务提取、补充追问和内容生成

成员D：

- `backend/app/services/template`
- `backend/app/services/export`
- 模板解析和 Word、Excel、PDF 导出

要求：

- 不要在没有任务要求时大范围修改其他成员模块。
- 模块之间通过 Schema、Service 接口和 REST API 交互。
- 禁止直接依赖其他模块的内部实现。
- 公共 Schema 变更必须同步检查前端 TypeScript 类型和 API 文档。

## 4. 核心架构规则

- 当前采用模块化单体，不拆分微服务。
- 路由层只负责参数接收、权限检查和调用 Service。
- 业务逻辑放入 `services`。
- 数据访问放入 `repositories`。
- SQLAlchemy 模型放入 `models`。
- API 请求和响应模型放入 `schemas`。
- 配置统一从环境变量读取，入口为 `backend/app/core/config.py`。
- 文件存储在 `storage` 目录，数据库只保存路径和元数据。
- AI、OCR、模板、导出模块需要保留可替换接口。
- 未配置真实 AI 服务时必须能够使用 Mock 实现。
- 不要在代码中硬编码密钥、密码或绝对路径。

## 5. 数据库规则

- 正式数据库为 MySQL 8.4。
- Python 驱动为 PyMySQL。
- 测试环境可以使用 SQLite。
- JSON 字段使用 SQLAlchemy 通用 `JSON` 类型。
- 禁止使用 PostgreSQL `JSONB`。
- 表结构变更必须通过 SQLAlchemy Model 和 Alembic 管理。
- 不要只在 DBeaver 中手动修改表结构。
- 新增或修改模型后检查并生成迁移文件。
- JSON 默认值使用 `default=dict` 或 `default=list`，禁止使用可变对象字面量。
- MySQL 使用 `utf8mb4`。
- 不自动删除数据库、表、迁移文件或 Docker Volume。

## 6. 开发流程

执行任务前：

1. 阅读相关目录和已有实现。
2. 检查当前 Git 状态。
3. 明确任务所属模块。
4. 优先复用现有 Schema、Service 和工具函数。
5. 先给出简短实施计划。

执行任务时：

1. 只修改与任务有关的文件。
2. 不删除用户已有代码。
3. 不重构无关模块。
4. 保持现有 API 兼容，除非任务明确要求更改。
5. 对未实现部分明确标注 TODO，不伪造实现。
6. 新增代码需要合理类型标注和错误处理。
7. 避免重复实现已有能力。

完成任务后：

1. 运行相关格式检查。
2. 运行相关测试。
3. 检查导入和启动是否正常。
4. 总结修改文件和实际验证结果。
5. 明确说明未执行或失败的检查。
6. 不自动执行 `git commit` 或 `git push`。

## 7. 常用命令

Windows PowerShell：

```powershell
# 后端依赖安装
cd reportflow-ai\backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -e ".[dev]"

# 后端启动
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Pytest
.\.venv\Scripts\python -m pytest

# Ruff
.\.venv\Scripts\python -m ruff check app tests

# MyPy
.\.venv\Scripts\python -m mypy app

# Alembic迁移
.\.venv\Scripts\python -m alembic upgrade head

# 生成 Alembic 迁移
.\.venv\Scripts\python -m alembic revision --autogenerate -m "describe change"
```

Linux 或 macOS：

```bash
# 后端依赖安装
cd reportflow-ai/backend
python -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e ".[dev]"

# 后端启动
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Pytest
.venv/bin/python -m pytest

# Ruff
.venv/bin/python -m ruff check app tests

# MyPy
.venv/bin/python -m mypy app

# Alembic迁移
.venv/bin/python -m alembic upgrade head
```

前端：

```bash
cd reportflow-ai/frontend
npm install
npm run dev
npm run type-check
npm run lint
npm run build
```

Docker Compose：

```bash
cd reportflow-ai
docker compose up --build
docker compose down
docker compose logs -f
```

Makefile 当前提供：

```bash
make install
make dev
make test
make lint
make format
make migrate
make migration m="describe change"
make up
make down
make logs
```

## 8. 测试要求

- 修改 Schema 时测试数据校验。
- 修改数据库模型时测试建表和迁移。
- 修改 Repository 时增加 CRUD 测试。
- 修改 API 时测试成功和错误响应。
- 修改 AI、OCR、模板或导出模块时测试 Mock 实现。
- 修复缺陷时尽量增加回归测试。
- 默认自动化测试不应依赖真实 AI 密钥。
- 默认自动化测试不应依赖真实 MySQL 服务，除非显式执行集成测试。
- 不得声称未实际运行的测试已经通过。

## 9. API和响应规范

- API前缀使用 `/api/v1`。
- 保持统一响应结构：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

- 错误通过统一异常处理返回。
- 不在端点中返回未序列化的 ORM 对象。
- 前后端共享字段发生变化时同步更新：
  - Pydantic Schema
  - TypeScript类型
  - Mock数据
  - API文档
  - 相关测试

## 10. Git规则

- 不直接推送或提交，除非用户明确要求。
- 不覆盖或回退其他成员未提交的修改。
- 不执行破坏性Git命令。
- 提交信息推荐：
  - `feat:`
  - `fix:`
  - `docs:`
  - `refactor:`
  - `test:`
  - `chore:`
- 每项任务尽量保持小范围、可审查的修改。

## 11. 禁止事项

- 禁止提交 `.env`、密钥或真实密码。
- 禁止擅自删除数据库数据或 Docker Volume。
- 禁止擅自更换主要技术栈。
- 禁止将项目重构为微服务。
- 禁止绕过统一 Schema 直接传递不可控 AI 文本。
- 禁止把上传文件二进制直接存入数据库。
- 禁止为了消除错误而删除测试。
- 禁止声称尚未实现的功能已经完成。
- 禁止在数据库迁移任务中修改前端业务页面。
- 禁止在无关任务中格式化整个仓库。

## 12. 当前状态

已完成：

- FastAPI 应用骨架，入口为 `backend/app/main.py`。
- `/api/v1` 路由聚合和 `GET /api/v1/health`。
- 文件、OCR、AI、模板、报表、导出模块的基础 API 路由。
- `TaskItem`、`ReportContent`、统一 `ApiResponse` 等 Pydantic Schema。
- SQLAlchemy 2 模型、Repository 基类和 `ReportRepository` 示例。
- Alembic 初始迁移 `backend/alembic/versions/0001_initial_schema.py`。
- MySQL 8.4 + PyMySQL 配置，SQLite 测试配置。
- Vue 3 + TypeScript + Vite 前端骨架。
- Vue Router、Pinia、Axios、Element Plus 配置。
- Docker Compose 中的 `mysql`、`backend`、`frontend`、`nginx` 服务配置。

Mock实现：

- `MockOCRService`
- `MockAIReportService`
- `MockTemplateService`
- `MockExportService`
- `samples/mock-tasks.json`
- `samples/mock-report.json`

尚未完成：

- 真实 OCR 接入。
- 真实 AI 服务接入。
- 完整认证、权限和用户体系。
- 完整在线富文本编辑器体验。
- 完整 Word、Excel、PDF 模板解析和导出。
- 生产级文件存储、病毒扫描和审计日志。

当前可运行命令：

- 后端：`python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- 后端测试：`python -m pytest`
- 后端检查：`python -m ruff check app tests`、`python -m mypy app`
- 前端：`npm run dev`
- 前端检查：`npm run type-check`、`npm run lint`
- 数据库迁移：`python -m alembic upgrade head`
- Docker：`docker compose up --build`、`docker compose down`、`docker compose logs -f`

已知风险：

- 当前多个核心业务模块仍是 Mock，占位接口不能当作真实业务能力。
- Docker 命令依赖本机安装 Docker CLI 和 Docker Engine。
- MySQL 密码需要通过 `.env` 配置，不能提交真实值。
- 前端生产构建可能因 Element Plus 等依赖产生较大 chunk，需要后续按页面或组件拆分优化。
