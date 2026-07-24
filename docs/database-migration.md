# 数据库迁移说明

当前仓库未发现真实 PostgreSQL 业务数据、迁移历史或需要保留的数据库 Volume，因此本次仅完成代码与配置迁移，没有执行数据复制。

## 当前结论

- 仓库处于初始化阶段。
- 没有发现需要从 PostgreSQL 自动转换到 MySQL 的业务数据。
- Alembic 仅负责创建 MySQL 表结构，不负责跨数据库搬运历史记录。

## 当前迁移文件

- `0001_initial_schema.py`：创建用户、文件、模板、报表、版本和导出记录表。
- `0002_project_spaces.py`：新增项目空间相关表，并为 `uploaded_files`、`templates`、
  `reports`、`export_records` 增加可空 `project_id`。

`0002_project_spaces.py` 的兼容策略：

- 旧文件、旧模板、旧报表和旧导出记录保留 `project_id = null`，不会失效。
- 项目任务、成员和记忆通过项目外键管理；API 默认归档项目，不物理删除业务数据。
- MySQL 表使用 InnoDB、`utf8mb4` 和显式索引；SQLite 测试通过 Alembic batch 模式执行。

运行迁移：

```powershell
cd reportflow-ai\backend
.\.venv\Scripts\python -m alembic upgrade head
```

验证降级：

```powershell
cd reportflow-ai\backend
.\.venv\Scripts\python -m alembic downgrade base
```

## 未来若存在旧 PostgreSQL 数据

1. 先完整备份 PostgreSQL 数据库和 Volume。
2. 停止写入。
3. 导出表结构和业务数据。
4. 在 MySQL 8.4 中重建表结构。
5. 转换 JSON、布尔、时间、UUID 和自增字段。
6. 导入 MySQL 并做行数核对。
7. 切换 `DATABASE_URL`，确认无误后再考虑清理旧库。
