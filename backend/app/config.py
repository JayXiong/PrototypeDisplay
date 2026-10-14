import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:proto2024@localhost:3306/proto_display?charset=utf8mb4",
)
SECRET_KEY = os.getenv("SECRET_KEY", "please-change-this-secret-key")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "72"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
