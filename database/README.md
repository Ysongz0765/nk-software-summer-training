# 数据库目录

`database/init` 用于放置 MySQL 容器首次启动时执行的初始化 SQL。业务表结构由 Alembic 管理，避免在初始化脚本中重复维护。

当前 Qwen OCR、DeepSeek AI 和 GitHub 项目进度分析不新增业务表；它们通过现有报表、任务、文件和 `source_data` 字段保存结果。若后续要保存 GitHub 仓库授权、增量同步游标或 webhook 事件，应新增 SQLAlchemy model 并生成 Alembic 迁移。

## MySQL 约定

- 数据库名：`reportflow`
- 字符集：`utf8mb4`
- 排序规则：`utf8mb4_unicode_ci`
- Docker Compose 宿主机访问端口：`3307`（容器内仍为 `3306`）
- 图形化管理工具建议：DBeaver Community

## 导出数据库结构

```bash
mysqldump \
  -h 127.0.0.1 \
  -P 3307 \
  -u reportflow \
  -p \
  --no-data \
  --default-character-set=utf8mb4 \
  reportflow > database/reportflow_schema.sql
```

## 导出演示数据

```bash
mysqldump \
  -h 127.0.0.1 \
  -P 3307 \
  -u reportflow \
  -p \
  --no-create-info \
  --default-character-set=utf8mb4 \
  reportflow > database/demo_data.sql
```

## 完整导出

```bash
mysqldump \
  -h 127.0.0.1 \
  -P 3307 \
  -u reportflow \
  -p \
  --default-character-set=utf8mb4 \
  reportflow > database/reportflow_full.sql
```

这些命令需要输入密码，且可能覆盖本地导出文件，仓库脚本不会自动执行。
