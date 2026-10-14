from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user, hash_password, verify_password
from .database import get_db
from .models import AdminUser

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    from .auth import create_token

    return {"token": create_token(user.username), "username": user.username}


@router.get("/me")
def me(user: AdminUser = Depends(get_current_user)):
    return {"username": user.username}


@router.put("/password")
def change_password(
    req: ChangePasswordRequest,
    user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少 6 位")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "密码修改成功"}
