# ReportFlow AI

ReportFlow AI 是一个网页端智能报表生成平台骨架，用于生成、编辑和导出项目日报、周报等内容。当前仓库重点提供公共基础设施、后端架构、前端骨架、Mock 服务和团队协作边界。

## 核心功能

- 文件上传、OCR、AI 抽取、模板解析、报表生成和导出的 API 边界。
- 统一 `TaskItem` 与 `ReportContent` 数据结构。
- FastAPI 后端、Vue 3 前端、MySQL 8.4、Alembic 和 Docker Compose 开发环境。
- 无真实 AI 密钥时可通过 Mock 服务运行。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router、Axios。
- 后端：Python 3.11+、FastAPI、Pydantic、SQLAlchemy 2、Alembic、Pytest、Ruff、MyPy。
- 数据库：MySQL 8.4，Python 驱动为 PyMySQL，默认字符集为 `utf8mb4`。
- 测试数据库：SQLite 内存数据库。
- 图形化数据库管理工具：DBeaver Community。
- 部署：Docker、Docker Compose、Nginx。

## 目录结构

```text
reportflow-ai/
  backend/        FastAPI 后端
  frontend/       Vue 3 前端
  database/       MySQL 初始化和导出说明
  deployment/     Nginx 等部署配置
  docs/           架构、接口、数据库和协作文档
  samples/        共享 Mock 数据
  scripts/        开发脚本
  storage/        上传、模板、导出和临时文件目录
```

## 本地环境要求

- Python 3.11+
- Node.js 20+
- Docker Desktop 或兼容 Docker Compose 的环境
- MySQL 8.4，可直接安装本地 MySQL，也可使用 Docker Compose 启动

## 后端启动

Windows PowerShell：

```powershell
cd reportflow-ai\backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
Copy-Item ..\.env.example ..\.env
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：

- 健康检查：`http://localhost:8000/api/v1/health`
- Swagger：`http://localhost:8000/docs`

## 前端启动

```powershell
cd reportflow-ai\frontend
npm install
npm run dev
```

默认访问：`http://localhost:5173`

## Docker Compose 启动

```powershell
cd reportflow-ai
Copy-Item .env.example .env
docker compose up --build
```

访问：

- Nginx 入口：`http://localhost:8080`
- 后端直连：`http://localhost:8000`
- 前端直连：`http://localhost:5173`
- MySQL：`localhost:3307`

## 本地 MySQL 配置

如果不使用 Docker Compose，可在本机 MySQL 中创建数据库和用户：

```sql
CREATE DATABASE reportflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'reportflow'@'%' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON reportflow.* TO 'reportflow'@'%';
FLUSH PRIVILEGES;
```

本地直连示例：

```env
DATABASE_URL=mysql+pymysql://reportflow:change_me@localhost:3306/reportflow?charset=utf8mb4
```

如果密码包含特殊字符，请在 `DATABASE_URL` 中进行 URL 编码，或在部署脚本中使用 SQLAlchemy `URL.create` 构造连接地址。

## DBeaver 连接 MySQL

- Host：`localhost`
- Port：`3307`（Docker Compose 暴露端口；本机直接安装 MySQL 时通常为 `3306`）
- Database：`reportflow`
- Username：`reportflow`
- Password：读取本地 `.env` 中的 `MYSQL_PASSWORD`

## 数据库迁移

```powershell
cd reportflow-ai\backend
.\.venv\Scripts\python -m alembic upgrade head
```

生成新迁移：

```powershell
.\.venv\Scripts\python -m alembic revision --autogenerate -m "describe change"
```

Alembic 负责表结构迁移，不负责把旧 PostgreSQL 业务数据自动复制到 MySQL。

## 数据库导出

导出表结构和演示数据命令见 [database/README.md](database/README.md)。这些命令需要数据库密码，不会在仓库脚本中自动执行。

## 测试方法

后端测试默认使用 SQLite 内存数据库：

```powershell
cd reportflow-ai\backend
.\.venv\Scripts\python -m pytest
```

前端检查：

```powershell
cd reportflow-ai\frontend
npm run type-check
npm run lint
```

## 团队模块边界

- 成员 A：`backend/app/core`、`backend/app/api`、数据库模型、部署与文档。
- 成员 B：`frontend/src`，尤其是页面、布局、编辑器与上传交互。
- 成员 C：`backend/app/services/ocr`、`backend/app/services/ai`、`backend/app/prompts`。
- 成员 D：`backend/app/services/template`、`backend/app/services/export`、模板与导出适配。

## 当前已完成功能

- 后端 FastAPI 可启动，提供统一 `/api/v1` 路由。
- `GET /api/v1/health` 可返回服务状态。
- 预留文件、OCR、AI、模板、报表和导出 API，并提供 Mock 返回。
- SQLAlchemy 模型、Pydantic Schema、Alembic 配置已创建。
- MySQL 8.4 + PyMySQL 配置已完成，SQLite 测试仍可运行。
- 前端 Vue 骨架、路由、Pinia、Axios、Element Plus 已配置。
- Docker Compose 包含 frontend、backend、mysql、nginx。

## 当前未完成功能

- 未接入真实 OCR、大模型、Word/Excel/PDF 导出。
- 未实现完整认证、权限和真实用户体系。
- 未实现在线富文本编辑器完整体验。
- 未实现生产级文件存储、病毒扫描和审计日志。

## 常见问题

- 本地没有 MySQL：优先使用 Docker Compose。
- AI 接口返回 Mock：确认 `.env` 中 `AI_PROVIDER=mock`，当前阶段不需要真实密钥。
- Windows 下 `make` 不可用：按 README 中的 PowerShell 命令逐步执行。
- 数据库连接失败：检查 `.env` 中 `DATABASE_URL`、`MYSQL_*` 和 MySQL 容器健康状态。
- 旧 PostgreSQL Docker Volume 不会自动迁移到 MySQL；确认备份无误后再手动清理。
