import shutil
import zipfile
from pathlib import Path

from .models import Project


def project_to_dict(p: Project, visits: int = 0, today_visits: int = 0) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "remark": p.remark or "",
        "status": p.status,
        "created_at": str(p.created_at),
        "updated_at": str(p.updated_at),
        "visits": visits,
        "today_visits": today_visits,
    }


def extract_project_file(src: Path, dest: Path) -> None:
    """把上传的单个 HTML 或 ZIP 解压到 dest 目录，保证 dest/index.html 存在。"""
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()

    if src.suffix.lower() == ".html":
        shutil.copyfile(src, dest / "index.html")
        return

    try:
        with zipfile.ZipFile(src) as z:
            names = z.namelist()
            index_names = [n for n in names if n.split("/")[-1] == "index.html"]
            if not index_names:
                raise ValueError("ZIP 包中未找到 index.html 文件")
            prefix = ""
            if "index.html" not in names:
                shortest = min(index_names, key=len)
                parts = shortest.split("/")
                if len(parts) >= 2:
                    prefix = "/".join(parts[:-1]) + "/"

            for info in z.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                if name.startswith("__MACOSX") or "/__MACOSX/" in name:
                    continue
                if prefix and not name.startswith(prefix):
                    continue
                rel = name[len(prefix):]
                if not rel:
                    continue
                target = (dest / rel).resolve()
                if not str(target).startswith(str(dest_resolved) + "\\") and not str(
                    target
                ).startswith(str(dest_resolved) + "/"):
                    if target != dest_resolved:
                        raise ValueError("ZIP 中存在非法文件路径")
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as fsrc, open(target, "wb") as fdst:
                    shutil.copyfileobj(fsrc, fdst)
    except zipfile.BadZipFile:
        raise ValueError("ZIP 文件已损坏，无法解压")
