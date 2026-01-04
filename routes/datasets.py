from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging

from services.dataset_manager import DatasetManager

router = APIRouter()
dataset_manager = DatasetManager()

@router.get("/")
async def get_datasets():
    """获取所有数据集列表"""
    try:
        result = dataset_manager.get_available_datasets()
        return result
    except Exception as e:
        logging.error(f"获取数据集列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_dataset(dataset_name: str):
    """验证数据集"""
    try:
        result = dataset_manager.validate_dataset(dataset_name)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', '数据集验证失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"验证数据集失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info/{dataset_name}")
async def get_dataset_info(dataset_name: str):
    """获取数据集详细信息"""
    try:
        result = dataset_manager.get_dataset_info(dataset_name)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error', '数据集不存在'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取数据集信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/supported")
async def get_supported_tasks():
    """获取支持的任务类型"""
    try:
        result = dataset_manager.get_supported_tasks()
        return result
    except Exception as e:
        logging.error(f"获取支持任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/cache")
async def get_download_cache():
    """获取下载缓存信息"""
    try:
        result = dataset_manager.get_download_cache_info()
        return result
    except Exception as e:
        logging.error(f"获取下载缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/download/cache")
async def clear_download_cache():
    """清理下载缓存"""
    try:
        result = dataset_manager.clear_download_cache()
        return result
    except Exception as e:
        logging.error(f"清理下载缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview")
async def get_datasets_stats():
    """获取数据集统计信息"""
    try:
        datasets = dataset_manager.get_available_datasets()
        if datasets['success']:
            data = datasets['data']
            stats = {
                'total_datasets': len(data),
                'categories': list(set([d.get('category', 'unknown') for d in data])),
                'total_size_gb': sum([d.get('size_gb', 0) for d in data]),
                'recently_used': len([d for d in data if d.get('last_used_at')])
            }
            return {'success': True, 'data': stats}
        else:
            return {'success': False, 'error': '无法获取数据集列表'}
    except Exception as e:
        logging.error(f"获取数据集统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_dataset_categories():
    """获取数据集分类列表"""
    try:
        datasets = dataset_manager.get_available_datasets()
        if datasets['success']:
            categories = list(set([d.get('category', 'unknown') for d in datasets['data']]))
            return {'success': True, 'data': categories}
        else:
            return {'success': False, 'error': '无法获取数据集分类'}
    except Exception as e:
        logging.error(f"获取数据集分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
