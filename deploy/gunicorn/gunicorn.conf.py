# Gunicorn 配置文件
# https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing
import os

# 绑定地址
bind = "127.0.0.1:5000"

# Worker 配置
# 建议: (2 x CPU核心数) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# 进程名称
proc_name = "tax-automation"

# 日志配置
accesslog = "/var/log/tax-automation/gunicorn_access.log"
errorlog = "/var/log/tax-automation/gunicorn_error.log"
loglevel = "info"

# 预加载应用
preload_app = True

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 临时目录
tmp_upload_dir = "/tmp"

# 安全设置
limit_request_line = 4094
limit_request_field = 8190

# 进程管理
daemon = False  # 由 systemd 管理
pidfile = "/var/run/tax-automation/tax-automation.pid"

# 当 worker 退出时，等待的最大时间
graceful_timeout = 30

# 统计
statsd_host = None

# 在 worker fork 后执行的钩子
def post_fork(server, worker):
    server.log.info(f"Worker spawned (pid: {worker.pid})")

# 在 worker 退出时执行的钩子
def worker_exit(server, worker):
    pass

# 在 master 启动时执行的钩子
def on_starting(server):
    server.log.info("Starting Gunicorn...")
