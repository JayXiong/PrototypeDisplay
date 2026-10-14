from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import AdminUser, Project, VisitLog

router = APIRouter(prefix="/api/stats", tags=["stats"])

HOUR_FMT = "%Y-%m-%d %H:00:00"
DAY_FMT = "%Y-%m-%d"


def _fill_buckets(start: datetime, end: datetime, granularity: str, counts: dict) -> list:
    """补齐没有访问数据的时间桶，方便前端画图。"""
    series = []
    if granularity == "hour":
        cur = start.replace(minute=0, second=0, microsecond=0)
        step = timedelta(hours=1)
        fmt = HOUR_FMT
    else:
        cur = start.replace(hour=0, minute=0, second=0, microsecond=0)
        step = timedelta(days=1)
        fmt = DAY_FMT
    while cur < end:
        key = cur.strftime(fmt)
        series.append({"bucket": key, "count": counts.get(key, 0)})
        cur += step
    return series


def _query_series(db: Session, granularity: str, start: datetime, end: datetime, project_id: int | None):
    fmt = HOUR_FMT if granularity == "hour" else DAY_FMT
    q = db.query(
        func.date_format(VisitLog.visited_at, fmt).label("bucket"),
        func.count(VisitLog.id).label("count"),
    ).filter(VisitLog.visited_at >= start, VisitLog.visited_at < end)
    if project_id is not None:
        q = q.filter(VisitLog.project_id == project_id)
    rows = q.group_by("bucket").all()
    return _fill_buckets(start, end, granularity, {r.bucket: r.count for r in rows})


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: AdminUser = Depends(get_current_user)):
    today = date.today()
    total = db.query(func.count(VisitLog.id)).scalar() or 0
    today_count = (
        db.query(func.count(VisitLog.id))
        .filter(func.date(VisitLog.visited_at) == today)
        .scalar()
        or 0
    )
    project_count = db.query(func.count(Project.id)).scalar() or 0
    top = (
        db.query(Project.id, Project.name, func.count(VisitLog.id).label("count"))
        .outerjoin(VisitLog, VisitLog.project_id == Project.id)
        .group_by(Project.id, Project.name)
        .order_by(func.count(VisitLog.id).desc())
        .limit(10)
        .all()
    )
    return {
        "total_visits": total,
        "today_visits": today_count,
        "project_count": project_count,
        "top_projects": [{"id": t.id, "name": t.name, "visits": t.count} for t in top],
    }


@router.get("/series")
def series(
    granularity: str = Query("day", pattern="^(hour|day)$"),
    days: int = Query(7, ge=1, le=90),
    project_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: AdminUser = Depends(get_current_user),
):
    end = datetime.now()
    start = end - timedelta(days=days)
    if granularity == "hour" and days > 7:
        start = end - timedelta(days=7)  # 按小时最多看 7 天
    return _query_series(db, granularity, start, end, project_id=project_id)
