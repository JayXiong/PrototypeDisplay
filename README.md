# 原型展示平台

上传 HTML 原型 → 生成访问链接 → 统计访问量。单人管理，Docker 一键部署。

## 快速部署（推荐，仅需安装 Docker）

```bash
# 1. （可选）修改配置：复制 .env.example 为 .env，改管理员密码/端口等
copy .env.example .env

# 2. 启动（首次会自动构建，需要几分钟）
docker compose up -d --build

# 3. 查看日志，确认启动成功
docker compose logs -f app
```

启动成功后：

- 管理后台：`http://localhost:8080`
- 默认账号：`admin` / `admin123`（**登录后请立即在右上角修改密码**）
- 原型访问地址格式：`http://localhost:8080/p/xxxxxxxx/`

常用命令：

```bash
docker compose stop      # 停止
docker compose start     # 再次启动
docker compose down      # 停止并删除容器（数据保留在卷中）
docker compose up -d --build   # 更新代码后重新构建部署
```

> 部署到服务器后，把 `localhost:8080` 换成服务器 IP 或域名即可分享给团队。

## 使用说明

| 功能 | 操作 |
|------|------|
| 新建项目 | 首页 → 「新建项目」→ 填名称、备注，上传单个 `.html` 或包含 `index.html` 的 `.zip`（≤50MB） |
| 更新原型 | 点「编辑」重新上传，覆盖旧原型 |
| 禁用原型 | 表格中的开关，禁用后访客打开链接会看到提示页 |
| 删除项目 | 点「删除」，文件与统计数据一并删除（二次确认） |
| 访问统计 | 「访问统计」页：累计/今日访问、按小时或按天趋势、单项目筛选、访问排行 |

## 本地开发（不改代码可跳过）

```bash
# 后端（需本机 Python 3.11+ 和 MySQL，或先 docker compose up -d db）
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev   # http://localhost:5173，已配置代理到 8000
```

## 项目结构

```
├── backend/            # FastAPI 后端（含 /p/{slug} 原型托管与访问埋点）
│   └── app/
│       ├── main.py             # 入口：原型访问路由 + 前端托管
│       ├── auth.py             # 登录认证（JWT）
│       ├── models.py           # 数据表：user / project / visit_log
│       ├── routers_auth.py     # 登录 / 修改密码
│       ├── routers_projects.py # 项目增删改查、启用禁用
│       └── routers_stats.py    # 访问统计（按小时 / 按天）
├── frontend/           # Vue 3 + Element Plus 管理端
├── Dockerfile          # 多阶段构建：构建前端 → Python 运行
├── docker-compose.yml  # MySQL + 应用，一键启动
└── .env.example        # 配置模板
```

## 常见问题

- **端口被占用**：`.env` 中改 `APP_PORT`，如 `APP_PORT=9090`。
- **忘记管理员密码**：`.env` 中修改 `ADMIN_PASSWORD` 后执行 `docker compose down && docker compose up -d` 不会重置已有账号；如需重置，执行 `docker compose exec db mysql -uroot -p proto_display -e "DELETE FROM user;"` 并重启 app 容器（会按 .env 重新创建账号）。
- **数据备份**：MySQL 数据在 `db_data` 卷，原型文件在 `uploads_data` 卷，可用 `docker run --rm -v proto-display_db_data:/data -v ${PWD}:/bak alpine tar czf /bak/db_backup.tar.gz /data` 备份。
