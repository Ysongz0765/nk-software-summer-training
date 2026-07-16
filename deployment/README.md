# 部署说明

当前部署目录包含 Nginx 开发代理配置。Docker Compose 中的服务包括：

- `mysql`：MySQL 8.4，默认字符集 `utf8mb4`
- `backend`：FastAPI 后端
- `frontend`：Vue 前端
- `nginx`：开发代理，`/api` 转发到后端，其他请求转发到前端

生产环境需要补充 HTTPS、日志、静态资源缓存、限流和安全头。数据库密码应通过环境变量或密钥管理系统注入，不要写入源代码。
