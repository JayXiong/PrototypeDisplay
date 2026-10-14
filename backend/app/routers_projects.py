import secrets
import shutil
import zipfile
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import get_current_user
from .config import MAX_UPLOAD_MB, UPLOAD_DIR
from .database import get_db
from .models import AdminUser, Project, VisitLog
from .services import extract_project_file, project_to_dict

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


async def _save_upload(file: UploadFile, tmp_path: Path) -> None:
    name = file.filename or ""
    if not (name.lower().endswith(".html") or name.lower().endswith(".zip")):
        raise HTTPException(status_code=400, detail="仅支持上传 .html 文件或 .zip 压缩包")
    limit = MAX_UPLOAD_MB * 1024 * 1024
    size = 0
    with open(tmp_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                f.close()
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail=f"文件大小不能超过 {MAX_UPLOAD_MB}MB")
            f.write(chunk)


@router.get("")
def list_projects(
    search: str = "",
    status: int | None = None,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_user),
):
    q = db.query(Project)
    if search:
        q = q.filter(Project.name.contains(search))
    if status is not None:
        q = q.filter(Project.status == status)
    projects = q.order_by(Project.updated_at.desc()).all()

    today = date.today()
    counts = dict(
        db.query(VisitLog.project_id, func.count(VisitLog.id))
        .group_by(VisitLog.project_id)
        .all()
    )
    today_counts = dict(
        db.query(VisitLog.project_id, func.count(VisitLog.id))
        .filter(func.date(VisitLog.visited_at) == today)
        .group_by(VisitLog.project_id)
        .all()
    )
    return [
        project_to_dict(p, visits=counts.get(p.id, 0), today_visits=today_counts.get(p.id, 0))
        for p in projects
    ]


@router.post("")
async def create_project(
    name: str = Form(...),
    remark: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_user),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="项目名称不能为空")

    while True:
        slug = secrets.token_hex(4)  # 8 位短链
        if not db.query(Project).filter(Project.slug == slug).first():
            break

    tmp_path = Path(UPLOAD_DIR) / f"tmp_{slug}_{file.filename}"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    await _save_upload(file, tmp_path)
    try:
        extract_project_file(tmp_path, Path(UPLOAD_DIR) / slug)
    except ValueError as e:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    project = Project(name=name, slug=slug, remark=remark, status=1)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_to_dict(project, visits=0, today_visits=0)


@router.put("/{project_id}")
async def update_project(
    project_id: int,
    name: str = Form(None),
    remark: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id)
    if name is not None and name.strip():
        project.name = name.strip()
    if remark is not None:
        project.remark = remark

    if file is not None and file.filename:
        tmp_path = Path(UPLOAD_DIR) / f"tmp_{project.slug}_{file.filename}"
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        await _save_upload(file, tmp_path)
        try:
            target = Path(UPLOAD_DIR) / project.slug
            shutil.rmtree(target, ignore_errors=True)  # 覆盖旧原型
            extract_project_file(tmp_path, target)
        except ValueError as e:
            tmp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            tmp_path.unlink(missing_ok=True)

    db.commit()
    db.refresh(project)
    visits = (
        db.query(func.count(VisitLog.id)).filter(VisitLog.project_id == project.id).scalar()
    )
    return project_to_dict(project, visits=visits, today_visits=0)


@router.put("/{project_id}/status")
def update_status(
    project_id: int,
    status: int,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_user),
):
    if status not in (0, 1):
        raise HTTPException(status_code=400, detail="状态值非法")
    project = _get_project_or_404(db, project_id)
    project.status = status
    db.commit()
    return {"id": project.id, "status": project.status}


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id)
    shutil.rmtree(Path(UPLOAD_DIR) / project.slug, ignore_errors=True)
    db.query(VisitLog).filter(VisitLog.project_id == project.id).delete()
    db.delete(project)
    db.commit()
    return {"message": "已删除"}


@router.get("/{project_id}/visits/recent")
def recent_visits(
    project_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_user),
):
    _get_project_or_404(db, project_id)
    rows = (
        db.query(VisitLog)
        .filter(VisitLog.project_id == project_id)
        .order_by(VisitLog.visited_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [
        {"ip": r.ip, "user_agent": r.user_agent, "visited_at": str(r.visited_at)}
        for r in rows
    ]
