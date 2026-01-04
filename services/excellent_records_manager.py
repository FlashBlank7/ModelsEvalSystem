import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import Session

from database.models import EvaluationRecord, Model, Dataset
from database.config import get_db

class ExcellentRecordsManager:
    """优秀测评记录管理系统"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def add_to_excellent_records(self, record_id: int, reason: str = None, 
                                tags: List[str] = None, category: str = "general") -> bool:
        """将测评记录添加到优秀记录集合"""
        try:
            db = next(get_db())
            
            # 获取测评记录
            record = db.query(EvaluationRecord).filter(
                EvaluationRecord.id == record_id
            ).first()
            
            if not record:
                self.logger.warning(f"测评记录不存在: ID {record_id}")
                return False
            
            # 检查是否已经是优秀记录
            if record.is_excellent:
                self.logger.info(f"记录 {record_id} 已经是优秀记录")
                return True
            
            # 更新记录为优秀记录
            record.is_excellent = True
            record.excellent_reason = reason or "操作者选择"
            record.excellent_tags = tags or []
            record.excellent_category = category
            record.added_to_excellent_at = datetime.now()
            
            db.commit()
            
            self.logger.info(f"成功将记录 {record_id} 添加到优秀记录集合")
            return True
            
        except Exception as e:
            self.logger.error(f"添加优秀记录失败: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def remove_from_excellent_records(self, record_id: int, reason: str = None) -> bool:
        """从优秀记录集合中移除记录"""
        try:
            db = next(get_db())
            
            record = db.query(EvaluationRecord).filter(
                EvaluationRecord.id == record_id
            ).first()
            
            if not record:
                self.logger.warning(f"测评记录不存在: ID {record_id}")
                return False
            
            # 移除优秀记录标记
            record.is_excellent = False
            record.removed_from_excellent_at = datetime.now()
            record.removal_reason = reason or "操作者移除"
            
            db.commit()
            
            self.logger.info(f"成功从优秀记录集合中移除记录 {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除优秀记录失败: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_excellent_records(self, category: str = None, tags: List[str] = None,
                            model_type: str = None, limit: int = 100, offset: int = 0,
                            order_by: str = "score", order_dir: str = "desc") -> List[EvaluationRecord]:
        """获取优秀测评记录"""
        try:
            db = next(get_db())
            query = db.query(EvaluationRecord).filter(
                EvaluationRecord.is_excellent == True
            )
            
            # 过滤条件
            if category:
                query = query.filter(EvaluationRecord.excellent_category == category)
            
            if model_type:
                query = query.filter(EvaluationRecord.model_type == model_type)
            
            if tags:
                # 这里假设tags是JSON数组，需要根据实际数据库结构调整
                query = query.filter(EvaluationRecord.excellent_tags.contains(tags))
            
            # 排序
            if order_by == "score":
                order_field = EvaluationRecord.score
            elif order_by == "created_at":
                order_field = EvaluationRecord.created_at
            elif order_by == "added_at":
                order_field = EvaluationRecord.added_to_excellent_at
            else:
                order_field = EvaluationRecord.score
            
            if order_dir.lower() == "asc":
                query = query.order_by(asc(order_field))
            else:
                query = query.order_by(desc(order_field))
            
            records = query.offset(offset).limit(limit).all()
            return records
            
        except Exception as e:
            self.logger.error(f"获取优秀记录失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_excellent_records_summary(self) -> Dict[str, Any]:
        """获取优秀记录统计摘要"""
        try:
            db = next(get_db())
            
            # 总优秀记录数
            total_excellent = db.query(EvaluationRecord).filter(
                EvaluationRecord.is_excellent == True
            ).count()
            
            # 按类别统计
            category_stats = {}
            categories = db.query(EvaluationRecord.excellent_category).filter(
                EvaluationRecord.is_excellent == True
            ).distinct().all()
            
            for category in categories:
                if category[0]:  # 确保类别不为空
                    count = db.query(EvaluationRecord).filter(
                        and_(
                            EvaluationRecord.is_excellent == True,
                            EvaluationRecord.excellent_category == category[0]
                        )
                    ).count()
                    category_stats[category[0]] = count
            
            # 按模型类型统计
            model_type_stats = {}
            model_types = db.query(EvaluationRecord.model_type).filter(
                EvaluationRecord.is_excellent == True
            ).distinct().all()
            
            for model_type in model_types:
                if model_type[0]:  # 确保类型不为空
                    count = db.query(EvaluationRecord).filter(
                        and_(
                            EvaluationRecord.is_excellent == True,
                            EvaluationRecord.model_type == model_type[0]
                        )
                    ).count()
                    model_type_stats[model_type[0]] = count
            
            # 平均分数
            excellent_records = db.query(EvaluationRecord).filter(
                EvaluationRecord.is_excellent == True,
                EvaluationRecord.score.isnot(None)
            ).all()
            
            avg_score = sum([record.score for record in excellent_records]) / len(excellent_records) if excellent_records else 0
            
            # 最近添加的记录
            recent_additions = db.query(EvaluationRecord).filter(
                EvaluationRecord.is_excellent == True
            ).order_by(desc(EvaluationRecord.added_to_excellent_at)).limit(5).all()
            
            return {
                'total_excellent_records': total_excellent,
                'category_distribution': category_stats,
                'model_type_distribution': model_type_stats,
                'average_score': round(avg_score, 3),
                'recent_additions': [
                    {
                        'id': record.id,
                        'model_name': record.model.name if record.model else "Unknown",
                        'dataset_name': record.dataset.name if record.dataset else "Unknown",
                        'score': record.score,
                        'category': record.excellent_category,
                        'added_at': record.added_to_excellent_at.isoformat() if record.added_to_excellent_at else None
                    }
                    for record in recent_additions
                ]
            }
            
        except Exception as e:
            self.logger.error(f"获取优秀记录摘要失败: {str(e)}")
            return {}
        finally:
            db.close()
    
    def search_excellent_records(self, keyword: str = None, min_score: float = None,
                               max_score: float = None, start_date: datetime = None,
                               end_date: datetime = None, category: str = None,
                               model_type: str = None, tags: List[str] = None,
                               limit: int = 100, offset: int = 0) -> Tuple[List[EvaluationRecord], int]:
        """搜索优秀测评记录"""
        try:
            db = next(get_db())
            query = db.query(EvaluationRecord).filter(
                EvaluationRecord.is_excellent == True
            )
            
            # 文本搜索
            if keyword:
                query = query.filter(
                    or_(
                        EvaluationRecord.excellent_reason.contains(keyword),
                        EvaluationRecord.excellent_category.contains(keyword)
                    )
                )
            
            # 分数范围
            if min_score is not None:
                query = query.filter(EvaluationRecord.score >= min_score)
            
            if max_score is not None:
                query = query.filter(EvaluationRecord.score <= max_score)
            
            # 日期范围
            if start_date:
                query = query.filter(EvaluationRecord.added_to_excellent_at >= start_date)
            
            if end_date:
                query = query.filter(EvaluationRecord.added_to_excellent_at <= end_date)
            
            # 其他过滤条件
            if category:
                query = query.filter(EvaluationRecord.excellent_category == category)
            
            if model_type:
                query = query.filter(EvaluationRecord.model_type == model_type)
            
            if tags:
                query = query.filter(EvaluationRecord.excellent_tags.contains(tags))
            
            # 获取总数和结果
            total_count = query.count()
            records = query.order_by(desc(EvaluationRecord.added_to_excellent_at)).offset(offset).limit(limit).all()
            
            return records, total_count
            
        except Exception as e:
            self.logger.error(f"搜索优秀记录失败: {str(e)}")
            return [], 0
        finally:
            db.close()
    
    def get_top_excellent_models(self, dataset_id: int = None, metric: str = "score", 
                               limit: int = 10) -> List[Dict[str, Any]]:
        """获取最佳优秀模型排行"""
        try:
            db = next(get_db())
            
            query = db.query(EvaluationRecord).filter(
                EvaluationRecord.is_excellent == True,
                EvaluationRecord.status == "completed"
            )
            
            if dataset_id:
                query = query.filter(EvaluationRecord.dataset_id == dataset_id)
            
            # 根据指标排序
            if metric == "score":
                order_field = EvaluationRecord.score
            elif metric == "accuracy":
                order_field = EvaluationRecord.accuracy
            elif metric == "speed":  # 基于执行时间排序
                order_field = EvaluationRecord.execution_time
            else:
                order_field = EvaluationRecord.score
            
            excellent_records = query.order_by(desc(order_field)).limit(limit).all()
            
            rankings = []
            for i, record in enumerate(excellent_records, 1):
                rankings.append({
                    'rank': i,
                    'record_id': record.id,
                    'model_id': record.model_id,
                    'model_name': record.model.name if record.model else "Unknown",
                    'dataset_name': record.dataset.name if record.dataset else "Unknown",
                    'model_type': record.model_type,
                    'score': getattr(record, metric),
                    'excellent_category': record.excellent_category,
                    'excellent_reason': record.excellent_reason,
                    'excellent_tags': record.excellent_tags,
                    'added_at': record.added_to_excellent_at.isoformat() if record.added_to_excellent_at else None
                })
            
            return rankings
            
        except Exception as e:
            self.logger.error(f"获取最佳优秀模型排行失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def update_excellent_record(self, record_id: int, reason: str = None, 
                              tags: List[str] = None, category: str = None) -> bool:
        """更新优秀记录信息"""
        try:
            db = next(get_db())
            
            record = db.query(EvaluationRecord).filter(
                EvaluationRecord.id == record_id,
                EvaluationRecord.is_excellent == True
            ).first()
            
            if not record:
                self.logger.warning(f"优秀记录不存在: ID {record_id}")
                return False
            
            # 更新字段
            if reason is not None:
                record.excellent_reason = reason
            
            if tags is not None:
                record.excellent_tags = tags
            
            if category is not None:
                record.excellent_category = category
            
            record.updated_at = datetime.now()
            
            db.commit()
            
            self.logger.info(f"更新优秀记录成功: {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新优秀记录失败: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_excellent_categories(self) -> List[str]:
        """获取所有优秀记录类别"""
        try:
            db = next(get_db())
            categories = db.query(EvaluationRecord.excellent_category).filter(
                and_(
                    EvaluationRecord.is_excellent == True,
                    EvaluationRecord.excellent_category.isnot(None)
                )
            ).distinct().all()
            
            return [cat[0] for cat in categories if cat[0]]
            
        except Exception as e:
            self.logger.error(f"获取优秀记录类别失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_excellent_tags(self) -> List[str]:
        """获取所有优秀记录标签"""
        try:
            db = next(get_db())
            records = db.query(EvaluationRecord).filter(
                and_(
                    EvaluationRecord.is_excellent == True,
                    EvaluationRecord.excellent_tags.isnot(None)
                )
            ).all()
            
            tags = set()
            for record in records:
                if record.excellent_tags:
                    tags.update(record.excellent_tags)
            
            return list(tags)
            
        except Exception as e:
            self.logger.error(f"获取优秀记录标签失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def export_excellent_records(self, format_type: str = "json", 
                               filters: Dict = None) -> str:
        """导出优秀测评记录"""
        try:
            # 获取记录
            if filters:
                records, _ = self.search_excellent_records(**filters)
            else:
                records = self.get_excellent_records(limit=10000)
            
            if format_type.lower() == "json":
                return self._export_excellent_to_json(records)
            elif format_type.lower() == "csv":
                return self._export_excellent_to_csv(records)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
                
        except Exception as e:
            self.logger.error(f"导出优秀记录失败: {str(e)}")
            raise
    
    def _export_excellent_to_json(self, records: List[EvaluationRecord]) -> str:
        """导出优秀记录为JSON格式"""
        import json
        
        data = []
        for record in records:
            data.append({
                'id': record.id,
                'model_name': record.model.name if record.model else "Unknown",
                'dataset_name': record.dataset.name if record.dataset else "Unknown",
                'score': record.score,
                'model_type': record.model_type,
                'excellent_category': record.excellent_category,
                'excellent_reason': record.excellent_reason,
                'excellent_tags': record.excellent_tags,
                'accuracy': record.accuracy,
                'execution_time': record.execution_time,
                'memory_usage': record.memory_usage,
                'added_to_excellent_at': record.added_to_excellent_at.isoformat() if record.added_to_excellent_at else None,
                'created_at': record.created_at.isoformat() if record.created_at else None
            })
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _export_excellent_to_csv(self, records: List[EvaluationRecord]) -> str:
        """导出优秀记录为CSV格式"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        headers = ['ID', '模型名称', '数据集名称', '分数', '模型类型', '优秀类别', 
                  '优秀原因', '标签', '准确率', '执行时间', '内存使用', '添加时间']
        writer.writerow(headers)
        
        # 写入数据
        for record in records:
            writer.writerow([
                record.id,
                record.model.name if record.model else "Unknown",
                record.dataset.name if record.dataset else "Unknown",
                record.score,
                record.model_type,
                record.excellent_category,
                record.excellent_reason,
                ', '.join(record.excellent_tags) if record.excellent_tags else '',
                record.accuracy,
                record.execution_time,
                record.memory_usage,
                record.added_to_excellent_at.isoformat() if record.added_to_excellent_at else ''
            ])
        
        return output.getvalue()
    
    def get_recommended_excellent_records(self, current_record_id: int = None, 
                                        limit: int = 5) -> List[Dict[str, Any]]:
        """获取推荐的优秀记录（基于相似性）"""
        try:
            db = next(get_db())
            
            if current_record_id:
                # 获取当前记录的信息作为推荐基准
                current_record = db.query(EvaluationRecord).filter(
                    EvaluationRecord.id == current_record_id
                ).first()
                
                if current_record:
                    # 基于相同数据集和模型类型推荐
                    query = db.query(EvaluationRecord).filter(
                        and_(
                            EvaluationRecord.is_excellent == True,
                            EvaluationRecord.id != current_record_id,
                            EvaluationRecord.dataset_id == current_record.dataset_id,
                            EvaluationRecord.model_type == current_record.model_type
                        )
                    ).order_by(desc(EvaluationRecord.score)).limit(limit)
                else:
                    # 如果找不到当前记录，返回通用的优秀记录
                    query = db.query(EvaluationRecord).filter(
                        EvaluationRecord.is_excellent == True
                    ).order_by(desc(EvaluationRecord.score)).limit(limit)
            else:
                # 返回通用的优秀记录
                query = db.query(EvaluationRecord).filter(
                    EvaluationRecord.is_excellent == True
                ).order_by(desc(EvaluationRecord.score)).limit(limit)
            
            records = query.all()
            
            recommendations = []
            for record in records:
                recommendations.append({
                    'record_id': record.id,
                    'model_name': record.model.name if record.model else "Unknown",
                    'dataset_name': record.dataset.name if record.dataset else "Unknown",
                    'score': record.score,
                    'model_type': record.model_type,
                    'excellent_category': record.excellent_category,
                    'similarity_reason': f"相同数据集和模型类型" if current_record_id else "高分记录"
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"获取推荐优秀记录失败: {str(e)}")
            return []
        finally:
            db.close()
