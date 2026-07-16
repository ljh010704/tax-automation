# 税务记账助手 - Ubuntu 22.04 部署指南

本文档介绍如何将税务记账助手部署到 Ubuntu 22.04 服务器上。

## 系统要求

- Ubuntu 22.04 LTS
- 至少 2GB 内存
- 至少 20GB 磁盘空间
- root 或 sudo 权限

## 快速部署

### 1. 上传项目到服务器

```bash
# 方式1: 使用 scp
scp -r tax-automation user@server:/tmp/

# 方式2: 使用 git
ssh user@server
cd /tmp
git clone your-repo-url tax-automation
```

### 2. 运行部署脚本

```bash
ssh user@server
cd /tmp/tax-automation
sudo bash deploy/deploy.sh
```

脚本会自动完成：
- 安装系统依赖（Python 3.10、Nginx、SQLite 等）
- 创建应用用户 `taxapp`
- 创建 Python 虚拟环境并安装依赖
- 安装 Playwright 和 Chromium 浏览器
- 配置 systemd 服务
- 配置 Nginx 反向代理
- 生成环境配置文件

### 3. 访问应用

部署完成后，通过浏览器访问：

```
http://服务器IP
```

首次访问需要注册管理员账号。

## 手动部署步骤

如果自动脚本不适用，可以按以下步骤手动部署。

### 1. 安装系统依赖

```bash
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip nginx sqlite3
```

### 2. 创建应用用户

```bash
sudo useradd -r -m -s /bin/bash taxapp
```

### 3. 复制项目文件

```bash
sudo mkdir -p /opt/tax-automation
sudo cp -r /tmp/tax-automation/* /opt/tax-automation/
sudo chown -R taxapp:taxapp /opt/tax-automation
```

### 4. 创建虚拟环境

```bash
cd /opt/tax-automation
sudo -u taxapp python3.10 -m venv venv
sudo -u taxapp venv/bin/pip install --upgrade pip
sudo -u taxapp venv/bin/pip install -r requirements.txt
sudo -u taxapp venv/bin/pip install -r requirements_web.txt
sudo -u taxapp venv/bin/pip install gunicorn
```

### 5. 安装 Playwright

```bash
sudo -u taxapp venv/bin/playwright install chromium
sudo -u taxapp venv/bin/playwright install-deps chromium
```

### 6. 创建环境配置

```bash
sudo -u taxapp cat > /opt/tax-automation/.env << 'EOF'
FLASK_APP=run_web.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-this
PORT=5000
DATABASE_PATH=/opt/tax-automation/data/entities.db
WEB_DATABASE_PATH=/opt/tax-automation/data/web.db
LOG_LEVEL=INFO
LOG_DIR=/var/log/tax-automation
AUTO_DECLARATION_ENABLED=true
DEFAULT_PROVINCE=fujian
HEADLESS_MODE=true
EOF

sudo chmod 600 /opt/tax-automation/.env
```

**重要**: 请修改 `SECRET_KEY` 为一个随机字符串。

### 7. 创建数据目录

```bash
sudo mkdir -p /opt/tax-automation/data/logs
sudo mkdir -p /opt/tax-automation/data/screenshots
sudo mkdir -p /var/log/tax-automation
sudo chown -R taxapp:taxapp /opt/tax-automation/data
sudo chown -R taxapp:taxapp /var/log/tax-automation
```

### 8. 配置 systemd 服务

```bash
sudo cp /opt/tax-automation/deploy/systemd/tax-automation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tax-automation
sudo systemctl start tax-automation
```

### 9. 配置 Nginx

```bash
sudo cp /opt/tax-automation/deploy/nginx/tax-automation.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/tax-automation.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 10. 配置防火墙

```bash
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## 管理命令

### 服务管理

```bash
# 查看状态
sudo systemctl status tax-automation

# 启动
sudo systemctl start tax-automation

# 停止
sudo systemctl stop tax-automation

# 重启
sudo systemctl restart tax-automation

# 查看日志
sudo journalctl -u tax-automation -f
sudo journalctl -u tax-automation -n 50
```

### 应用日志

```bash
# Gunicorn 日志
sudo tail -f /var/log/tax-automation/gunicorn_error.log
sudo tail -f /var/log/tax-automation/gunicorn_access.log

# Nginx 日志
sudo tail -f /var/log/nginx/tax-automation.access.log
sudo tail -f /var/log/nginx/tax-automation.error.log
```

## 更新应用

### 使用更新脚本

```bash
cd /tmp/tax-automation
sudo bash deploy/update.sh
```

更新脚本会：
- 自动备份当前版本
- 停止服务
- 更新代码（保留数据和配置）
- 更新依赖
- 重启服务

### 手动更新

```bash
# 备份
sudo tar -czf /opt/backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /opt/tax-automation .

# 停止服务
sudo systemctl stop tax-automation

# 更新代码（保留数据和配置）
sudo rsync -av --exclude='data' --exclude='.env' --exclude='venv' /tmp/tax-automation/ /opt/tax-automation/

# 更新依赖
sudo -u taxapp /opt/tax-automation/venv/bin/pip install -r /opt/tax-automation/requirements.txt
sudo -u taxapp /opt/tax-automation/venv/bin/pip install -r /opt/tax-automation/requirements_web.txt

# 修复权限
sudo chown -R taxapp:taxapp /opt/tax-automation

# 启动服务
sudo systemctl start tax-automation
```

## 配置 HTTPS（推荐）

### 使用 Let's Encrypt

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书（需要域名）
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

certbot 会自动修改 Nginx 配置并设置自动续期。

### 手动配置

编辑 `/etc/nginx/sites-available/tax-automation.conf`，取消注释 HTTPS 配置部分，并修改：
- `server_name` 为你的域名
- `ssl_certificate` 和 `ssl_certificate_key` 为证书路径

## 数据库备份

### 手动备份

```bash
# 备份 entities.db
sudo -u taxapp sqlite3 /opt/tax-automation/data/entities.db ".backup /opt/backup/entities_$(date +%Y%m%d).db"

# 备份 web.db
sudo -u taxapp sqlite3 /opt/tax-automation/data/web.db ".backup /opt/backup/web_$(date +%Y%m%d).db"
```

### 自动备份（cron）

```bash
# 编辑 crontab
sudo crontab -e

# 添加以下行（每天凌晨2点备份）
0 2 * * * /usr/bin/sqlite3 /opt/tax-automation/data/entities.db ".backup /opt/backup/entities_$(date +\%Y\%m\%d).db"
0 2 * * * /usr/bin/sqlite3 /opt/tax-automation/data/web.db ".backup /opt/backup/web_$(date +\%Y\%m\%d).db"
```

## 故障排查

### 服务无法启动

```bash
# 查看详细错误
sudo journalctl -u tax-automation -n 50 --no-pager

# 检查配置文件
sudo -u taxapp /opt/tax-automation/venv/bin/python -c "from web.app import create_app; create_app()"
```

### 权限问题

```bash
# 修复权限
sudo chown -R taxapp:taxapp /opt/tax-automation
sudo chown -R taxapp:taxapp /var/log/tax-automation
```

### 数据库锁定

```bash
# 检查是否有残留进程
sudo ps aux | grep tax-automation

# 重启服务
sudo systemctl restart tax-automation
```

### Playwright 问题

```bash
# 重新安装浏览器
sudo -u taxapp /opt/tax-automation/venv/bin/playwright install chromium
sudo -u taxapp /opt/tax-automation/venv/bin/playwright install-deps chromium
```

## 性能优化

### 调整 Gunicorn Worker 数

编辑 `/opt/tax-automation/deploy/gunicorn/gunicorn.conf.py`：

```python
workers = 4  # 根据 CPU 核心数调整
```

重启服务生效。

### 启用 Nginx 缓存

编辑 Nginx 配置，在 `location /static/` 中添加：

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=static_cache:10m max_size=1g;
```

## 安全建议

1. **修改默认 SECRET_KEY**
   - 编辑 `/opt/tax-automation/.env`
   - 使用 `openssl rand -hex 32` 生成新的密钥

2. **配置 HTTPS**
   - 使用 Let's Encrypt 免费证书
   - 强制 HTTPS 访问

3. **限制访问 IP**
   - 配置 Nginx 或防火墙规则
   - 只允许特定 IP 访问

4. **定期备份**
   - 配置自动备份任务
   - 将备份文件存储到远程位置

5. **更新系统**
   - 定期运行 `apt update && apt upgrade`
   - 及时应用安全补丁

## 常见问题

### Q: 如何修改端口？

编辑 `/opt/tax-automation/.env`，修改 `PORT=5000`，然后重启服务。

### Q: 如何查看当前配置？

```bash
cat /opt/tax-automation/.env
```

### Q: 如何重置管理员密码？

```bash
sudo -u taxapp /opt/tax-automation/venv/bin/python << EOF
from web.auth import get_db, _hash_password
import secrets
db = get_db()
salt = secrets.token_hex(16)
password_hash = _hash_password('newpassword', salt)
db.execute('UPDATE users SET password_hash=?, salt=? WHERE username=?', 
           (password_hash, salt, 'admin'))
db.commit()
EOF
```

### Q: 自动报税功能无法工作？

1. 检查 Playwright 是否正确安装
2. 确认 `.env` 中 `HEADLESS_MODE=true`
3. 查看日志: `sudo tail -f /var/log/tax-automation/gunicorn_error.log`
4. 注意：服务器上自动报税需要手动登录，建议配合 VNC 或 X11 转发

## 技术支持

如有问题，请查看：
- 项目 README.md
- 日志文件
- systemd 服务状态

---

**最后更新**: 2026-07-14
