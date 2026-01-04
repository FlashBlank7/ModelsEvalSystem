from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from services.records_manager import RecordsManager
from services.excellent_records_manager import ExcellentRecordsManager

router = APIRouter()
records_manager = RecordsManager()
excellent_manager = ExcellentRecordsManager()

@router.get("/")
async def get_records(limit: int = 100, offset: int = 0, order_by: str = "created_at", order_dir: str = "desc"):
    """获取测评记录列表"""
    try:
        records = records_manager.get_all_records(limit, offset, order_by, order_dir)
        return {
            'success': True,
            'data': [
                {
                    'id': record.id,
                    'model_name': record.model.name if record.model else "Unknown",
                    'dataset_name': record.dataset.name if record.dataset else "Unknown",
                    'score': record.score,
                    'model_type': record.model_type,
                    'status': record.status,
                    'created_at': record.created_at.isoformat() if record.created_at else None,
                    'execution_time': record.execution_time,
                    'memory_usage': record.memory_usage
                }
                for record in records
            ]
        }
    except Exception as e:
        logging.error(f"获取测评记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{record_id}")
async def get_record(record_id: int):
    """获取单个测评记录"""
    try:
        record = records_manager.get_record(record_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"记录不存在: {record_id}")
        
        return {
            'success': True,
            'data': {
                'id': record.id,
                'task_id': record.task_id,
                'model_id': record.model_id,
                'dataset_id': record.dataset_id,
                'model_name': record.model.name if record.model else "Unknown",
                'dataset_name': record.dataset.name if record.dataset else "Unknown",
                'score': record.score,
                'metrics': record.metrics,
                'results': record.results,
                'execution_time': record.execution_time,
                'memory_usage': record.memory_usage,
                'model_type': record.model_type,
                'accuracy': record.accuracy,
                'loss': record.loss,
                'perplexity': record.perplexity,
                'custom_metrics': record.custom_metrics,
                'config': record.config,
                'status': record.status,
                'error_message': record.error_message,
                'created_at': record.created_at.isoformat() if record.created_at else None,
                'is_excellent': record.is_excellent,
                'excellent_category': record.excellent_category,
                'excellent_reason': record.excellent_reason,
                'excellent_tags': record.excellent_tags,
                'added_to_excellent_at': record.added_to_excellent_at.isoformat() if record.added_to_excellent_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取测评记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_record(record_data: Dict[str, Any]):
    """创建测评记录"""
    try:
        record = records_manager.create_record(**record_data)
        return {
            'success': True,
            'record_id': record.id,
            'message': '记录创建成功'
        }
    except Exception as e:
        logging.error(f"创建测评记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{record_id}")
async def update_record(record_id: int, record_data: Dict[str, Any]):
    """更新测评记录"""
    try:
        result = records_manager.update_record(record_id, **record_data)
        if not result:
            raise HTTPException(status_code=404, detail=f"记录不存在: {record_id}")
        
        return {'success': True, 'message': '记录更新成功'}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"更新测评记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{record_id}")
async def delete_record(record_id: int):
    """删除测评记录"""
    try:
        result = records_manager.delete_record(record_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"记录不存在: {record_id}")
        
        return {'success': True, 'message': '记录删除成功'}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"删除测评记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/")
async def search_records(
    model_name: Optional[str] = None,
    dataset_name: Optional[str] = None,
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """搜索测评记录"""
    try:
        # 转换日期字符串
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.fromisoformat(start_date)
        if end_date:
            end_date_obj = datetime.fromisoformat(end_date)
        
        records, total_count = records_manager.search_records(
            model_name, dataset_name, model_type, status,
            min_score, max_score, start_date_obj, end_date_obj,
            limit, offset
        )
        
        return {
            'success': True,
            'data': [
                {
                    'id': record.id,
                    'model_name': record.model.name if record.model else "Unknown",
                    'dataset_name': record.dataset.name if record.dataset else "Unknown",
                    'score': record.score,
                    'model_type': record.model_type,
                    'status': record.status,
                    'created_at': record.created_at.isoformat() if record.created_at else None
                }
                for record in records
            ],
            'total_count': total_count
        }
    except Exception as e:
        logging.error(f"搜索测评记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/overview")
async def get_records_statistics():
    """获取测评记录统计"""
    try:
        stats = records_manager.get_record_statistics()
        return {'success': True, 'data': stats}
    except Exception as e:
        logging.error(f"获取记录统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rankings/{dataset_id}")
async def get_model_rankings(dataset_id: int, metric: str = "score", limit: int = 10):
    """获取模型排行榜"""
    try:
        rankings = records_manager.get_model_rankings(dataset_id, metric, limit)
        return {'success': True, 'data': rankings}
    except Exception as e:
        logging.error(f"获取模型排行栟失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/")
async def export_records(format_type: str = "json", filters: Optional[Dict[str, Any]] = None):
    """导出测评记录"""
    try:
        result = records_manager.export_records(format_type, filters)
        return {
            'success': True,
            'data': result,
            'filename': f'records_export_{int(datetime.now().timestamp())}.{format_type}'
        }
    except Exception as e:
        logging.error(f"导出记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 优秀记录管理路由
@router.post("/{record_id}/excellent")
async def add_to_excellent(record_id: int, reason: Optional[str] = None, 
                          tags: Optional[List[str]] = None, category: str = "general"):
    """将记录添加到优秀记录"""
    try:
        result = excellent_manager.add_to_excellent_records(record_id, reason, tags, category)
        if not result:
            raise HTTPException(status_code=400, detail="添加优秀记录失败")
        
        return {'success': True, 'message': '已添加到优秀记录'}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"添加优秀记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{record_id}/excellent")
async def remove_from_excellent(record_id: int, reason: Optional[str] = None):
    """从优秀记录中移除"""
    try:
        result = excellent_manager.remove_from_excellent_records(record_id, reason)
        if not result:
            raise HTTPException(status_code=400, detail="移除优秀记录失败")
        
        return {'success': True, 'message': '已从优秀记录中移除'}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"移除优秀记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/excellent/")
async def get_excellent_records(
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    model_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "score",
    order_dir: str = "desc"
):
    """获取优秀记录列表"""
    try:
        records = excellent_manager.get_excellent_records(
            category, tags, model_type, limit, offset, order_by, order_dir
        )
        
        return {
            'success': True,
            'data': [
                {
                    'id': record.id,
                    'model_name': record.model.name if record.model else "Unknown",
                    'dataset_name': record.dataset.name if record.dataset else "Unknown",
                    'score': record.score,
                    'model_type': record.model_type,
                    'excellent_category': record.excellent_category,
                    'excellent_reason': record.excellent_reason,
                    'excellent_tags': record.excellent_tags,
                    'added_to_excellent_at': record.added_to_excellent_at.isoformat() if record.added_to_excellent_at else None
                }
                for record in records
            ]
        }
    except Exception as e:
        logging.error(f"获取优秀记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/excellent/summary")
async def get_excellent_summary():
    """获取优秀记录摘要"""
    try:
        summary = excellent_manager.get_excellent_records_summary()
        return {'success': True, 'data': summary}
    except Exception as e:
        logging.error(f"获取优秀记录摘要失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/excellent/categories")
async def get_excellent_categories():
    """获取优秀记录分类"""
    try:
        categories = excellent_manager.get_excellent_categories()
        return {'success': True, 'data': categories}
    except Exception as e:
        logging.error(f"获取优秀记录分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/excellent/tags")
async def get_excellent_tags():
    """获取优秀记录标签"""
    try:
        tags = excellent_manager.get_excellent_tags()
        return {'success': True, 'data': tags}
    except Exception as e:
        logging.error(f"获取优秀记录标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/excellent/recommendations/{record_id}")
async def get_excellent_recommendations(record_id: int, limit: int = 5):
    """获取优秀记录推荐"""
    try:
        recommendations = excellent_manager.get_recommended_excellent_records(record_id, limit)
        return {'success': True, 'data': recommendations}
    except Exception as e:
        logging.error(f"获取优秀记录推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/excellent/top-performers/{dataset_id}")
async def get_top_excellent_models(dataset_id: int, metric: str = "score", limit: int = 10):
    """获取最佳优秀模型排行"""
    try:
        rankings = excellent_manager.get_top_excellent_models(dataset_id, metric, limit)
        return {'success': True, 'data': rankings}
    except Exception as e:
        logging.error(f"获取最佳优秀模型排行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/excellent/export/")
async def export_excellent_records(format_type: str = "json", filters: Optional[Dict[str, Any]] = None):
    """导出优秀记录"""
    try:
        result = excellent_manager.export_excellent_records(format_type, filters)
        return {
            'success': True,
            'data': result,
            'filename': f'excellent_records_export_{int(datetime.now().timestamp())}.{format_type}'
        }
    except Exception as e:
        logging.error(f"导出优秀记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
