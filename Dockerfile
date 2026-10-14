# ---------- 第一阶段：构建 Vue 前端 ----------
FROM node:20-alpine AS frontend-builder
WORKDIR /fe
RUN npm config set registry https://registry.npmmirror.com
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---------- 第二阶段：Python 运行环境 ----------
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 TZ=Asia/Shanghai
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-builder /fe/dist ./static
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
