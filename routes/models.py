from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import logging

from services.model_manager import ModelManager
from services.evaluation_engine import EvaluationEngine

router = APIRouter()
model_manager = ModelManager()
evaluation_engine = EvaluationEngine()

@router.get("/")
async def get_models():
    """获取所有模型列表"""
    try:
        result = model_manager.get_models_list()
        return result
    except Exception as e:
        logging.error(f"获取模型列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_path}")
async def get_model_info(model_path: str):
    """获取指定模型信息"""
    try:
        result = model_manager.get_model_info(model_path)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error', '模型不存在'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取模型信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_model(model_path: str, background_tasks: BackgroundTasks):
    """导入模型"""
    try:
        result = model_manager.import_model(model_path)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', '模型导入失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"导入模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{model_path}")
async def remove_model(model_path: str):
    """移除模型"""
    try:
        result = model_manager.remove_model(model_path)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error', '模型不存在或移除失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"移除模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_path}/test")
async def test_model(model_path: str):
    """测试模型连接"""
    try:
        if model_path.startswith(('http://', 'https://')):
            # API模型测试
            result = evaluation_engine.test_api_connection(model_path)
        else:
            # 本地模型测试
            result = model_manager.get_model_info(model_path)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', '模型测试失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"测试模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/local")
async def scan_local_models():
    """扫描本地模型目录"""
    try:
        result = model_manager.scan_local_models()
        return result
    except Exception as e:
        logging.error(f"扫描本地模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview")
async def get_models_stats():
    """获取模型统计信息"""
    try:
        models_list = model_manager.get_models_list()
        if models_list['success']:
            models = models_list['data']
            stats = {
                'total_models': len(models),
                'local_models': len([m for m in models if m['model_type'] == 'local']),
                'api_models': len([m for m in models if m['model_type'] == 'api']),
                'recent_imports': len([m for m in models if m.get('imported_at')])
            }
            return {'success': True, 'data': stats}
        else:
            return {'success': False, 'error': '无法获取模型列表'}
    except Exception as e:
        logging.error(f"获取模型统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types/available")
async def get_model_types():
    """获取支持的模型类型"""
    return {
        'success': True,
        'data': {
            'local_types': ['transformers', 'pytorch', 'tensorflow', 'onnx'],
            'api_types': ['openai', 'gemini', 'deepseek', 'custom'],
            'supported_formats': ['.bin', '.safetensors', '.ckpt', '.pth', '.pt']
        }
    }
