#!/bin/bash
# 税务记账助手 - Ubuntu 22.04 部署脚本
# 用法: sudo bash deploy.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 sudo 运行此脚本"
    exit 1
fi

# 配置变量
APP_NAME="tax-automation"
APP_USER="taxapp"
APP_DIR="/opt/tax-automation"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/$APP_NAME"
DATA_DIR="$APP_DIR/data"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

log_info "开始部署税务记账助手..."
log_info "项目目录: $PROJECT_DIR"
log_info "安装目录: $APP_DIR"

# 1. 更新系统
log_info "更新系统包..."
apt update && apt upgrade -y

# 2. 安装依赖
log_info "安装系统依赖..."
apt install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    nginx \
    sqlite3 \
    libsqlite3-dev \
    wget \
    curl \
    git

# 3. 创建应用用户
if ! id "$APP_USER" &>/dev/null; then
    log_info "创建应用用户: $APP_USER"
    useradd -r -m -s /bin/bash "$APP_USER"
fi

# 4. 复制项目文件
log_info "复制项目文件..."
mkdir -p "$APP_DIR"
cp -r "$PROJECT_DIR"/* "$APP_DIR/"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

# 5. 创建虚拟环境
log_info "创建 Python 虚拟环境..."
sudo -u "$APP_USER" python3.10 -m venv "$VENV_DIR"

# 6. 安装 Python 依赖
log_info "安装 Python 依赖..."
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements_web.txt"
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install gunicorn

# 7. 安装 Playwright
log_info "安装 Playwright 和浏览器..."
sudo -u "$APP_USER" "$VENV_DIR/bin/playwright" install chromium
"$VENV_DIR/bin/playwright" install-deps chromium

# 8. 创建数据目录
log_info "创建数据目录..."
mkdir -p "$DATA_DIR/logs"
mkdir -p "$DATA_DIR/screenshots"
chown -R "$APP_USER":"$APP_USER" "$DATA_DIR"

# 9. 生成环境变量配置
log_info "生成环境配置..."
if [ ! -f "$APP_DIR/.env" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    cat > "$APP_DIR/.env" << EOF
# 税务记账助手环境配置
FLASK_APP=run_web.py
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY
PORT=5000

# 数据库路径
DATABASE_PATH=$DATA_DIR/entities.db
WEB_DATABASE_PATH=$DATA_DIR/web.db

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=$LOG_DIR

# 自动报税配置
AUTO_DECLARATION_ENABLED=true
DEFAULT_PROVINCE=fujian
HEADLESS_MODE=true
EOF
    chown "$APP_USER":"$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    log_warn "已生成 .env 配置文件，请检查并修改必要配置"
fi

# 10. 安装 systemd 服务
log_info "安装 systemd 服务..."
cp "$SCRIPT_DIR/systemd/tax-automation.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable tax-automation
systemctl start tax-automation

# 11. 配置 Nginx
log_info "配置 Nginx..."
cp "$SCRIPT_DIR/nginx/tax-automation.conf" /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/tax-automation.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 12. 配置防火墙
log_info "配置防火墙..."
if command -v ucf &> /dev/null; then
    ufw allow 'Nginx Full'
    ufw --force enable
fi

# 13. 创建日志目录
mkdir -p "$LOG_DIR"
chown -R "$APP_USER":"$APP_USER" "$LOG_DIR"

# 14. 初始化数据库
log_info "初始化数据库..."
sudo -u "$APP_USER" bash -c "cd $APP_DIR && source venv/bin/activate && python -c 'from web.auth import init_auth_db; init_auth_db()'"

log_info "部署完成！"
echo ""
echo "=========================================="
echo "  税务记账助手已成功部署"
echo "=========================================="
echo ""
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "管理命令:"
echo "  查看状态: sudo systemctl status tax-automation"
echo "  重启服务: sudo systemctl restart tax-automation"
echo "  查看日志: sudo journalctl -u tax-automation -f"
echo "  应用日志: sudo tail -f $LOG_DIR/app.log"
echo ""
echo "首次使用:"
echo "  1. 访问上述地址"
echo "  2. 点击注册创建管理员账号"
echo "  3. 登录后即可使用"
echo ""
echo "配置文件: $APP_DIR/.env"
echo "数据目录: $DATA_DIR"
echo "日志目录: $LOG_DIR"
echo ""
log_warn "请确保修改 .env 中的 SECRET_KEY"
log_warn "建议配置 HTTPS 以提高安全性"
