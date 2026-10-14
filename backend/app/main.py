from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from .config import STATIC_DIR, UPLOAD_DIR
from .database import Base, SessionLocal, engine, get_db
from .models import AdminUser, Project, VisitLog
from .routers_auth import router as auth_router
from .routers_projects import router as projects_router
from .routers_stats import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(AdminUser).first():
            from .auth import hash_password
            from .config import ADMIN_PASSWORD, ADMIN_USERNAME

            db.add(
                AdminUser(username=ADMIN_USERNAME, password_hash=hash_password(ADMIN_PASSWORD))
            )
            db.commit()
    finally:
        db.close()
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="原型展示平台", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(stats_router)

DISABLED_PAGE = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>原型已禁用</title><style>body{font-family:sans-serif;display:flex;height:100vh;
align-items:center;justify-content:center;background:#f5f5f5}
.card{text-align:center;padding:60px 80px;background:#fff;border-radius:12px;
box-shadow:0 4px 16px rgba(0,0,0,.08)}h1{color:#e6a23c;font-size:24px}p{color:#909399}</style>
</head><body><div class="card"><h1>原型已禁用</h1><p>该原型暂不可访问，请联系管理员。</p>
</div></body></html>"""

NOT_FOUND_PAGE = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>页面不存在</title><style>body{font-family:sans-serif;display:flex;height:100vh;
align-items:center;justify-content:center;background:#f5f5f5}
.card{text-align:center;padding:60px 80px;background:#fff;border-radius:12px;
box-shadow:0 4px 16px rgba(0,0,0,.08)}h1{color:#909399;font-size:24px}p{color:#c0c4cc}</style>
</head><body><div class="card"><h1>404</h1><p>原型不存在或已被删除。</p></div></body></html>"""


def _log_visit(db: Session, project_id: int, request: Request) -> None:
    db.add(
        VisitLog(
            project_id=project_id,
            ip=request.client.host if request.client else "",
            user_agent=(request.headers.get("user-agent") or "")[:512],
        )
    )
    db.commit()


def _serve_page(slug: str, path: str, request: Request, db: Session):
    project = db.query(Project).filter(Project.slug == slug).first()
    if project is None:
        return HTMLResponse(NOT_FOUND_PAGE, status_code=404)
    if project.status != 1:
        return HTMLResponse(DISABLED_PAGE, status_code=403)

    base = (Path(UPLOAD_DIR) / project.slug).resolve()
    rel = path.strip("/")
    if not rel:
        rel = "index.html"
        # 首次进入统一 301 到带斜杠的地址，保证相对资源路径正确
        if not request.url.path.endswith("/"):
            from fastapi.responses import RedirectResponse

            return RedirectResponse(request.url.path + "/", status_code=301)
    target = (base / rel).resolve()
    if not str(target).startswith(str(base)):
        return HTMLResponse(NOT_FOUND_PAGE, status_code=404)
    if target.is_dir():
        target = target / "index.html"
    if not target.is_file():
        return HTMLResponse(NOT_FOUND_PAGE, status_code=404)

    if target.suffix.lower() == ".html":
        _log_visit(db, project.id, request)
    return FileResponse(target)


@app.get("/p/{slug}", include_in_schema=False)
def serve_proto_root(slug: str, request: Request, db: Session = Depends(get_db)):
    return _serve_page(slug, "", request, db)


@app.get("/p/{slug}/{path:path}", include_in_schema=False)
def serve_proto(slug: str, path: str, request: Request, db: Session = Depends(get_db)):
    return _serve_page(slug, path, request, db)


# 前端管理端（Vue 构建产物）+ SPA 路由回退
_static_exists = Path(STATIC_DIR).is_dir()


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("p/"):
        raise HTTPException(status_code=404, detail="Not Found")
    if _static_exists:
        candidate = Path(STATIC_DIR) / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index = Path(STATIC_DIR) / "index.html"
        if index.is_file():
            return FileResponse(index)
    return HTMLResponse(
        "<h3>前端尚未构建</h3><p>请先执行前端构建（Docker 部署会自动完成）。</p>",
        status_code=200,
    )
