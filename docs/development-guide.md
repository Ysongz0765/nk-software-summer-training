# 开发指南

## 本地开发

1. 复制 `.env.example` 为 `.env`。
2. 启动 MySQL 8.4，或直接使用 Docker Compose。
3. 安装后端和前端依赖。
4. 执行 `alembic upgrade head` 初始化表结构。
5. 启动后端和前端。

## 数据库连接

Docker 环境默认使用：

```env
DATABASE_URL=mysql+pymysql://reportflow:change_me@mysql:3306/reportflow?charset=utf8mb4
```

本地 MySQL 可将主机名改为 `localhost`。如果密码包含特殊字符，需要在连接字符串中 URL 编码。

## 推荐顺序

- 先完成后端基础接口和数据库迁移。
- 再接入前端占位页面。
- 最后扩展 OCR、AI、模板和导出模块。

## 代码规范

- Python 使用 Ruff 和 MyPy。
- 前端使用 ESLint、Prettier 和 TypeScript。
- 所有新接口都必须补充统一响应和错误处理。
- 自动化测试默认使用 SQLite 内存库，不依赖本地 MySQL。
