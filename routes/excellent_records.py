from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime
from database.config import get_db
from database.models import ExcellentRecord, EvaluationRecord, Model, Dataset
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

router = APIRouter()

def get_db():
    db = get_db()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
async def get_excellent_records(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取优秀测评记录列表"""
    try:
        query = db.query(ExcellentRecord)
        
        if category:
            query = query.filter(ExcellentRecord.category == category)
        
        records = query.order_by(desc(ExcellentRecord.created_at)).offset(skip).limit(limit).all()
        
        result = []
        for record in records:
            # 获取关联的原始测评记录
            evaluation_record = db.query(EvaluationRecord).filter(
                EvaluationRecord.id == record.evaluation_record_id
            ).first()
            
            record_info = {
                'id': record.id,
                'title': record.title,
                'description': record.description,
                'category': record.category,
                'tags': record.tags,
                'is_featured': record.is_featured,
                'view_count': record.view_count,
                'like_count': record.like_count,
                'created_at': record.created_at.isoformat() if record.created_at else None,
                'evaluation_record': None
            }
            
            if evaluation_record:
                record_info['evaluation_record'] = {
                    'id': evaluation_record.id,
                    'model_name': evaluation_record.model.name if evaluation_record.model else None,
                    'dataset_name': evaluation_record.dataset.name if evaluation_record.dataset else None,
                    'accuracy': evaluation_record.accuracy,
                    'loss': evaluation_record.loss,
                    'perplexity': evaluation_record.perplexity,
                    'evaluation_time': evaluation_record.evaluation_time,
                    'created_at': evaluation_record.created_at.isoformat() if evaluation_record.created_at else None
                }
            
            result.append(record_info)
        
        return {
            'success': True,
            'data': result,
            'total': query.count(),
            'skip': skip,
            'limit': limit
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.post("/")
async def create_excellent_record(
    evaluation_record_id: int,
    title: str,
    description: str = "",
    category: str = "general",
    tags: List[str] = None,
    is_featured: bool = False,
    db: Session = Depends(get_db)
):
    """创建优秀测评记录"""
    try:
        # 检查测评记录是否存在
        evaluation_record = db.query(EvaluationRecord).filter(
            EvaluationRecord.id == evaluation_record_id
        ).first()
        
        if not evaluation_record:
            return {
                'success': False,
                'error': f'测评记录 {evaluation_record_id} 不存在',
                'timestamp': datetime.now().isoformat()
            }
        
        # 检查是否已经创建过优秀记录
        existing = db.query(ExcellentRecord).filter(
            ExcellentRecord.evaluation_record_id == evaluation_record_id
        ).first()
        
        if existing:
            return {
                'success': False,
                'error': f'测评记录 {evaluation_record_id} 已经创建过优秀记录',
                'timestamp': datetime.now().isoformat()
            }
        
        # 创建优秀记录
        excellent_record = ExcellentRecord(
            evaluation_record_id=evaluation_record_id,
            title=title,
            description=description,
            category=category,
            tags=tags or [],
            is_featured=is_featured
        )
        
        db.add(excellent_record)
        db.commit()
        db.refresh(excellent_record)
        
        return {
            'success': True,
            'data': {
                'id': excellent_record.id,
                'message': '优秀测评记录创建成功'
            }
        }
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.put("/{record_id}")
async def update_excellent_record(
    record_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新优秀测评记录"""
    try:
        record = db.query(ExcellentRecord).filter(ExcellentRecord.id == record_id).first()
        
        if not record:
            return {
                'success': False,
                'error': f'优秀记录 {record_id} 未找到',
                'timestamp': datetime.now().isoformat()
            }
        
        # 更新允许的字段
        allowed_fields = ['title', 'description', 'category', 'tags', 'is_featured']
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(record, field):
                if field == 'tags' and isinstance(value, list):
                    setattr(record, field, value)
                else:
                    setattr(record, field, value)
        
        db.commit()
        db.refresh(record)
        
        return {
            'success': True,
            'data': {
                'message': f'优秀记录 {record_id} 已更新',
                'record_id': record_id
            }
        }
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.delete("/{record_id}")
async def delete_excellent_record(record_id: int, db: Session = Depends(get_db)):
    """删除优秀测评记录"""
    try:
        record = db.query(ExcellentRecord).filter(ExcellentRecord.id == record_id).first()
        
        if not record:
            return {
                'success': False,
                'error': f'优秀记录 {record_id} 未找到',
                'timestamp': datetime.now().isoformat()
            }
        
        db.delete(record)
        db.commit()
        
        return {
            'success': True,
            'data': {
                'message': f'优秀记录 {record_id} 已删除',
                'record_id': record_id
            }
        }
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.post("/{record_id}/like")
async def like_excellent_record(record_id: int, db: Session = Depends(get_db)):
    """点赞优秀测评记录"""
    try:
        record = db.query(ExcellentRecord).filter(ExcellentRecord.id == record_id).first()
        
        if not record:
            return {
                'success': False,
                'error': f'优秀记录 {record_id} 未找到',
                'timestamp': datetime.now().isoformat()
            }
        
        record.like_count = (record.like_count or 0) + 1
        db.commit()
        
        return {
            'success': True,
            'data': {
                'like_count': record.like_count,
                'message': '点赞成功'
            }
        }
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.post("/{record_id}/view")
async def view_excellent_record(record_id: int, db: Session = Depends(get_db)):
    """浏览优秀测评记录"""
    try:
        record = db.query(ExcellentRecord).filter(ExcellentRecord.id == record_id).first()
        
        if not record:
            return {
                'success': False,
                'error': f'优秀记录 {record_id} 未找到',
                'timestamp': datetime.now().isoformat()
            }
        
        record.view_count = (record.view_count or 0) + 1
        db.commit()
        
        return {
            'success': True,
            'data': {
                'view_count': record.view_count
            }
        }
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.get("/categories")
async def get_excellent_record_categories(db: Session = Depends(get_db)):
    """获取优秀记录分类统计"""
    try:
        categories = db.query(
            ExcellentRecord.category,
            func.count(ExcellentRecord.id).label('count')
        ).group_by(ExcellentRecord.category).all()
        
        result = [{'category': cat[0], 'count': cat[1]} for cat in categories]
        
        return {
            'success': True,
            'data': result
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.get("/featured")
async def get_featured_excellent_records(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取精选优秀记录"""
    try:
        records = db.query(ExcellentRecord)\
            .filter(ExcellentRecord.is_featured == True)\
            .order_by(desc(ExcellentRecord.like_count), desc(ExcellentRecord.created_at))\
            .limit(limit)\
            .all()
        
        result = []
        for record in records:
            evaluation_record = db.query(EvaluationRecord).filter(
                EvaluationRecord.id == record.evaluation_record_id
            ).first()
            
            record_info = {
                'id': record.id,
                'title': record.title,
                'description': record.description,
                'category': record.category,
                'tags': record.tags,
                'view_count': record.view_count,
                'like_count': record.like_count,
                'evaluation_record': None
            }
            
            if evaluation_record:
                record_info['evaluation_record'] = {
                    'id': evaluation_record.id,
                    'model_name': evaluation_record.model.name if evaluation_record.model else None,
                    'dataset_name': evaluation_record.dataset.name if evaluation_record.dataset else None,
                    'accuracy': evaluation_record.accuracy,
                    'loss': evaluation_record.loss,
                    'perplexity': evaluation_record.perplexity,
                    'evaluation_time': evaluation_record.evaluation_time
                }
            
            result.append(record_info)
        
        return {
            'success': True,
            'data': result
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.get("/top-liked")
async def get_top_liked_records(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取点赞最多的记录"""
    try:
        records = db.query(ExcellentRecord)\
            .order_by(desc(ExcellentRecord.like_count))\
            .limit(limit)\
            .all()
        
        result = []
        for record in records:
            evaluation_record = db.query(EvaluationRecord).filter(
                EvaluationRecord.id == record.evaluation_record_id
            ).first()
            
            record_info = {
                'id': record.id,
                'title': record.title,
                'description': record.description,
                'category': record.category,
                'like_count': record.like_count,
                'evaluation_record': None
            }
            
            if evaluation_record:
                record_info['evaluation_record'] = {
                    'id': evaluation_record.id,
                    'model_name': evaluation_record.model.name if evaluation_record.model else None,
                    'dataset_name': evaluation_record.dataset.name if evaluation_record.dataset else None,
                    'accuracy': evaluation_record.accuracy,
                    'loss': evaluation_record.loss,
                    'perplexity': evaluation_record.perplexity
                }
            
            result.append(record_info)
        
        return {
            'success': True,
            'data': result
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
