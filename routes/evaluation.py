from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging

from services.evaluation_engine import EvaluationEngine
from services.task_queue import TaskQueue
from services.batch_evaluation_manager import BatchEvaluationManager

router = APIRouter()
evaluation_engine = EvaluationEngine()
task_queue = TaskQueue()
batch_manager = BatchEvaluationManager()

@router.post("/single")
async def evaluate_single_model(model_path: str, dataset_name: str, config: Dict[str, Any] = None):
    """测评单个模型"""
    try:
        result = evaluation_engine.evaluate_model(model_path, dataset_name, config)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', '测评失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"单模型测评失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api")
async def evaluate_api_model(model_path: str, dataset_name: str, config: Dict[str, Any] = None):
    """测评API模型"""
    try:
        result = evaluation_engine.evaluate_api_model(model_path, dataset_name, config)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'API模型测评失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"API模型测评失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/local")
async def evaluate_local_model(model_path: str, dataset_name: str, config: Dict[str, Any] = None):
    """测评本地模型"""
    try:
        result = evaluation_engine.evaluate_local_model(model_path, dataset_name, config)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', '本地模型测评失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"本地模型测评失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-api")
async def test_api_connection(model_path: str, config: Dict[str, Any] = None):
    """测试API连接"""
    try:
        result = evaluation_engine.test_api_connection(model_path, config)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'API连接测试失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"API连接测试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def create_batch_evaluation(model_paths: list, dataset_name: str, 
                                 config: Dict[str, Any] = None, task_name: str = None,
                                 parallel: bool = True):
    """创建批量测评任务"""
    try:
        result = batch_manager.create_batch_evaluation(model_paths, dataset_name, config, task_name, parallel)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', '创建批量测评失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"创建批量测评失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/{task_id}/execute")
async def execute_batch_evaluation(task_id: int):
    """执行批量测评任务"""
    try:
        result = batch_manager.execute_batch_evaluation(task_id)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', '执行批量测评失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"执行批量测评失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch/{task_id}/report")
async def get_batch_report(task_id: int):
    """获取批量测评报告"""
    try:
        task_info = task_queue.get_task_status(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        result = task_info.get('result', {})
        if not result:
            raise HTTPException(status_code=404, detail="任务结果不存在")
        
        return {'success': True, 'data': result}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取批量测评报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch/history")
async def get_batch_history(limit: int = 20, offset: int = 0):
    """获取批量测评历史"""
    try:
        result = batch_manager.get_batch_evaluation_history(limit, offset)
        return {'success': True, 'data': result}
    except Exception as e:
        logging.error(f"获取批量测评历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_evaluation_history():
    """获取测评历史"""
    try:
        result = evaluation_engine.get_evaluation_history()
        return result
    except Exception as e:
        logging.error(f"获取测评历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks")
async def get_tasks():
    """获取任务队列状态"""
    try:
        result = task_queue.get_queue_status()
        return result
    except Exception as e:
        logging.error(f"获取任务队列状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/task")
async def add_task(task_data: Dict[str, Any]):
    """添加测评任务"""
    try:
        task_id = task_queue.add_task(task_data)
        return {'success': True, 'task_id': task_id}
    except Exception as e:
        logging.error(f"添加任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}")
async def get_task_status(task_id: int):
    """获取任务状态"""
    try:
        result = task_queue.get_task_status(task_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/task/{task_id}/cancel")
async def cancel_task(task_id: int):
    """取消任务"""
    try:
        result = task_queue.cancel_task(task_id)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', '取消任务失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"取消任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
