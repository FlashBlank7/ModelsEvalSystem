import os
import sys
from contextlib import asynccontextmanager

# 设置环境变量
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import HTMLResponse

# 导入数据库和路由
from database.config import engine, Base
from database.models import *
from services.gpu_monitor import GPUMonitor
from services.task_queue import TaskQueue
from services.model_manager import ModelManager
from services.evaluation_engine import EvaluationEngine

# 全局实例
gpu_monitor = GPUMonitor()
task_queue = TaskQueue()
model_manager = ModelManager()
evaluation_engine = EvaluationEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    Base.metadata.create_all(bind=engine)
    
    # 启动后台任务
    task_queue.start_queue_processing()
    
    yield
    
    # 关闭时清理资源
    task_queue.stop_worker()

app = FastAPI(
    title="模型测评系统",
    description="基于 lm_task 的模型测评平台",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 导入所有路由
from routes import models, datasets, evaluation, records, monitoring

# 前端路由
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
async def dashboard_page(request: Request):
    """仪表板页面"""
    return templates.TemplateResponse("index.html", {"request": request, "active_section": "dashboard"})

@app.get("/models")
async def models_page(request: Request):
    """模型管理页面"""
    return templates.TemplateResponse("index.html", {"request": request, "active_section": "models"})

@app.get("/datasets")
async def datasets_page(request: Request):
    """数据集页面"""
    return templates.TemplateResponse("index.html", {"request": request, "active_section": "datasets"})

@app.get("/evaluation")
async def evaluation_page(request: Request):
    """测评执行页面"""
    return templates.TemplateResponse("index.html", {"request": request, "active_section": "evaluation"})

@app.get("/records")
async def records_page(request: Request):
    """测评记录页面"""
    return templates.TemplateResponse("index.html", {"request": request, "active_section": "records"})

@app.get("/monitoring")
async def monitoring_page(request: Request):
    """系统监控页面"""
    return templates.TemplateResponse("index.html", {"request": request, "active_section": "monitoring"})

# 注册路由
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
app.include_router(records.router, prefix="/api/records", tags=["records"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "模型测评系统运行正常"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)