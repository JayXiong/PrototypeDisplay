#!/usr/bin/env bash
# 原型展示平台 一键部署脚本（在服务器上执行）
# 用法：
#   chmod +x deploy.sh
#   ./deploy.sh          # 首次运行会生成 .env 配置文件，改完密码后再次运行即可启动
set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "=============================================================="
  echo " 已生成 .env 配置文件，请先编辑它（必改两项）："
  echo "   1. ADMIN_PASSWORD  管理员登录密码"
  echo "   2. SECRET_KEY      随便换成一长串随机字符"
  echo " 修改后重新执行 ./deploy.sh 即可启动"
  echo "=============================================================="
  exit 0
fi

echo ">>> 开始构建并启动（首次需要几分钟下载镜像）..."
docker compose up -d --build

echo ""
echo ">>> 等待服务就绪..."
sleep 10
docker compose ps

echo ""
echo "=============================================================="
echo " 部署完成！"
echo " 管理后台: http://服务器IP:${APP_PORT:-8080}"
echo " 原型链接: http://服务器IP:${APP_PORT:-8080}/p/xxxxxxxx/"
echo " 查看日志: docker compose logs -f app"
echo "=============================================================="
