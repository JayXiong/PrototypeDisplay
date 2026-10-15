# Prototype Display Platform

[简体中文](README.md) | [English](README.en.md)

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3.4+-4FC08D?logo=vuedotjs&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-one--click--deploy-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Upload HTML prototypes → get a shareable link → track visits. Single-admin, one-click Docker deployment.

## Quick Start (Docker required only)

```bash
# 1. (Optional) Configure: copy .env.example to .env, set admin password / port, etc.
copy .env.example .env

# 2. Start (first run builds automatically, takes a few minutes)
docker compose up -d --build

# 3. Check logs to confirm startup
docker compose logs -f app
```

Once running:

- Admin dashboard: `http://localhost:8080`
- Default account: `admin` / `admin123` (**change the password immediately after login**)
- Prototype URL format: `http://localhost:8080/p/xxxxxxxx/`

Common commands:

```bash
docker compose stop            # Stop
docker compose start           # Start again
docker compose down            # Stop and remove containers (data persists in volumes)
docker compose up -d --build   # Rebuild and deploy after code changes
```

> After deploying to a server, replace `localhost:8080` with your server IP or domain to share with your team.

## Usage

| Feature | How |
|---------|-----|
| Create project | Home → "New Project" → fill in name & remark, upload a single `.html` or a `.zip` containing `index.html` (≤50MB) |
| Update prototype | Click "Edit" and re-upload; the old prototype is replaced |
| Disable prototype | Toggle the switch in the table; visitors will see a notice page when disabled |
| Delete project | Click "Delete"; prototype files and visit stats are removed together (with confirmation) |
| Visit stats | "Stats" page: total / today's visits, hourly or daily trends, per-project filter, visit ranking |

## Local Development (skip if not modifying code)

```bash
# Backend (requires local Python 3.11+ and MySQL, or run `docker compose up -d db` first)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev   # http://localhost:5173, proxy to port 8000 pre-configured
```

## Project Structure

```
├── backend/            # FastAPI backend (hosts /p/{slug} prototypes + visit tracking)
│   └── app/
│       ├── main.py             # Entry: prototype routes + frontend hosting
│       ├── auth.py             # Authentication (JWT)
│       ├── models.py           # Tables: user / project / visit_log
│       ├── routers_auth.py     # Login / change password
│       ├── routers_projects.py # Project CRUD, enable/disable
│       └── routers_stats.py    # Visit stats (hourly / daily)
├── frontend/           # Vue 3 + Element Plus admin dashboard
├── Dockerfile          # Multi-stage build: build frontend → Python runtime
├── docker-compose.yml  # MySQL + app, one command to start
└── .env.example        # Configuration template
```

## FAQ

- **Port already in use**: change `APP_PORT` in `.env`, e.g. `APP_PORT=9090`.
- **Forgot admin password**: changing `ADMIN_PASSWORD` in `.env` won't reset an existing account; to reset, run `docker compose exec db mysql -uroot -p proto_display -e "DELETE FROM user;"` and restart the app container (account will be re-created from .env).
- **Data backup**: MySQL data lives in the `db_data` volume, prototype files in `uploads_data`. Backup example: `docker run --rm -v proto-display_db_data:/data -v ${PWD}:/bak alpine tar czf /bak/db_backup.tar.gz /data`.
