# 部署说明

当前部署目录包含 Nginx 开发代理配置。Docker Compose 中的服务包括：

- `mysql`：MySQL 8.4，默认字符集 `utf8mb4`
- `backend`：FastAPI 后端
- `frontend`：Vue 前端
- `nginx`：开发代理，`/api` 转发到后端，其他请求转发到前端

生产环境需要补充 HTTPS、日志、静态资源缓存、限流和安全头。数据库密码应通过环境变量或密钥管理系统注入，不要写入源代码。

真实 AI/OCR 和 GitHub 分析相关密钥也必须通过环境变量注入：

- `AI_API_KEY`：DeepSeek 报表生成和任务提取。
- `QWEN_API_KEY`：Qwen 多模态截图识别。
- `GITHUB_API_TOKEN`：私有仓库访问或提升 GitHub API 限额。

部署时确认 `CORS_ORIGINS` 包含实际前端域名，避免浏览器请求被拦截。
