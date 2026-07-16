#!/bin/bash
# 本地快速启动 Web 版本（开发用）

set -e

cd "$(dirname "$0")/.."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -q -r requirements.txt
pip install -q -r requirements_web.txt

# 复制环境配置
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "已创建 .env 文件，请根据需要修改配置"
fi

# 启动应用
echo "启动 Web 服务..."
echo "访问地址: http://localhost:5000"
python run_web.py
