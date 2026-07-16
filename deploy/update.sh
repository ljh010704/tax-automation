#!/bin/bash
# 税务记账助手 - 更新脚本
# 用法: sudo bash update.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then
    log_error "请使用 sudo 运行此脚本"
    exit 1
fi

APP_DIR="/opt/tax-automation"
BACKUP_DIR="/opt/tax-automation-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

log_info "开始更新税务记账助手..."

# 备份当前版本
log_info "备份当前版本..."
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$APP_DIR" .
log_info "备份已保存: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

# 停止服务
log_info "停止服务..."
systemctl stop tax-automation

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 更新代码（保留数据和配置）
log_info "更新代码..."
rsync -av --exclude='data' --exclude='.env' --exclude='venv' "$PROJECT_DIR/" "$APP_DIR/"

# 更新依赖
log_info "更新 Python 依赖..."
sudo -u taxapp "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
sudo -u taxapp "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements_web.txt"
sudo -u taxapp "$APP_DIR/venv/bin/pip" install gunicorn

# 修复权限
chown -R taxapp:taxapp "$APP_DIR"

# 启动服务
log_info "启动服务..."
systemctl start tax-automation

# 检查状态
sleep 3
if systemctl is-active --quiet tax-automation; then
    log_info "更新完成！服务运行正常"
else
    log_error "服务启动失败，查看日志: journalctl -u tax-automation -n 50"
    log_warn "如需回滚: sudo tar -xzf $BACKUP_DIR/backup_$TIMESTAMP.tar.gz -C $APP_DIR"
    exit 1
fi
