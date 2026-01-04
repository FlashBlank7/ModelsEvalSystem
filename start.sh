#!/bin/bash

# 设置环境变量
export HF_ENDPOINT=https://hf-mirror.com
export PYTHONPATH=/home/a/ServiceEndFiles/Workspaces/ModelEvaluator

# 创建模型目录
mkdir -p /home/a/ServiceEndFiles/Models

# 创建数据库
python3 -c "
from database.models import Base
from database.config import engine
Base.metadata.create_all(bind=engine)
print('数据库表创建完成')
"

# 启动服务器
echo "启动模型测评系统..."
python -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
