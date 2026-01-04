import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import Session

from database.models import EvaluationRecord, EvaluationTask, Model, Dataset
from database.config import get_db

class RecordsManager:
    """测试记录管理系统 - 实现增删改查功能"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_record(self, task_id: int, model_id: int, dataset_id: int, 
                     score: float = None, metrics: Dict = None, 
                     results: Dict = None, execution_time: float = None,
                     memory_usage: float = None, model_type: str = "local",
                     accuracy: float = None, loss: float = None, 
                     perplexity: float = None, custom_metrics: Dict = None,
                     config: Dict = None, evaluation_time: float = None,
                     status: str = "completed", error_message: str = None) -> EvaluationRecord:
        """创建新的测评记录"""
        try:
            db = next(get_db())
            
            record = EvaluationRecord(
                task_id=task_id,
                model_id=model_id,
                dataset_id=dataset_id,
                score=score,
                metrics=metrics or {},
                results=results or {},
                execution_time=execution_time,
                memory_usage=memory_usage,
                model_type=model_type,
                accuracy=accuracy,
                loss=loss,
                perplexity=perplexity,
                custom_metrics=custom_metrics or {},
                config=config or {},
                evaluation_time=evaluation_time,
                status=status,
                error_message=error_message
            )
            
            db.add(record)
            db.commit()
            db.refresh(record)
            
            self.logger.info(f"创建测评记录成功: ID {record.id}")
            return record
            
        except Exception as e:
            self.logger.error(f"创建测评记录失败: {str(e)}")
            raise
        finally:
            db.close()
    
    def get_record(self, record_id: int) -> Optional[EvaluationRecord]:
        """根据ID获取单个测评记录"""
        try:
            db = next(get_db())
            record = db.query(EvaluationRecord).filter(
                EvaluationRecord.id == record_id
            ).first()
            return record
        except Exception as e:
            self.logger.error(f"获取测评记录失败: {str(e)}")
            return None
        finally:
            db.close()
    
    def get_all_records(self, limit: int = 100, offset: int = 0, 
                       order_by: str = "created_at", order_dir: str = "desc") -> List[EvaluationRecord]:
        """获取所有测评记录，支持分页和排序"""
        try:
            db = next(get_db())
            query = db.query(EvaluationRecord)
            
            # 排序
            if order_by == "score":
                order_field = EvaluationRecord.score
            elif order_by == "created_at":
                order_field = EvaluationRecord.created_at
            else:
                order_field = EvaluationRecord.created_at
            
            if order_dir.lower() == "asc":
                query = query.order_by(asc(order_field))
            else:
                query = query.order_by(desc(order_field))
            
            # 分页
            records = query.offset(offset).limit(limit).all()
            return records
            
        except Exception as e:
            self.logger.error(f"获取测评记录列表失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_records_by_model(self, model_id: int, limit: int = 100, offset: int = 0) -> List[EvaluationRecord]:
        """根据模型ID获取测评记录"""
        try:
            db = next(get_db())
            records = db.query(EvaluationRecord).filter(
                EvaluationRecord.model_id == model_id
            ).order_by(desc(EvaluationRecord.created_at)).offset(offset).limit(limit).all()
            return records
        except Exception as e:
            self.logger.error(f"根据模型获取测评记录失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_records_by_dataset(self, dataset_id: int, limit: int = 100, offset: int = 0) -> List[EvaluationRecord]:
        """根据数据集ID获取测评记录"""
        try:
            db = next(get_db())
            records = db.query(EvaluationRecord).filter(
                EvaluationRecord.dataset_id == dataset_id
            ).order_by(desc(EvaluationRecord.created_at)).offset(offset).limit(limit).all()
            return records
        except Exception as e:
            self.logger.error(f"根据数据集获取测评记录失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_records_by_task(self, task_id: int) -> List[EvaluationRecord]:
        """根据任务ID获取测评记录"""
        try:
            db = next(get_db())
            records = db.query(EvaluationRecord).filter(
                EvaluationRecord.task_id == task_id
            ).order_by(desc(EvaluationRecord.created_at)).all()
            return records
        except Exception as e:
            self.logger.error(f"根据任务获取测评记录失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_top_performers(self, dataset_id: int, model_type: str = None, limit: int = 3) -> List[EvaluationRecord]:
        """获取指定数据集上表现最好的前N个模型"""
        try:
            db = next(get_db())
            query = db.query(EvaluationRecord).filter(
                EvaluationRecord.dataset_id == dataset_id,
                EvaluationRecord.status == "completed"
            )
            
            if model_type:
                query = query.filter(EvaluationRecord.model_type == model_type)
            
            records = query.order_by(desc(EvaluationRecord.score)).limit(limit).all()
            return records
            
        except Exception as e:
            self.logger.error(f"获取最佳表现记录失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def update_record(self, record_id: int, **kwargs) -> bool:
        """更新测评记录"""
        try:
            db = next(get_db())
            record = db.query(EvaluationRecord).filter(
                EvaluationRecord.id == record_id
            ).first()
            
            if not record:
                self.logger.warning(f"测评记录不存在: ID {record_id}")
                return False
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            db.commit()
            self.logger.info(f"更新测评记录成功: ID {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新测评记录失败: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def delete_record(self, record_id: int) -> bool:
        """删除测评记录"""
        try:
            db = next(get_db())
            record = db.query(EvaluationRecord).filter(
                EvaluationRecord.id == record_id
            ).first()
            
            if not record:
                self.logger.warning(f"测评记录不存在: ID {record_id}")
                return False
            
            db.delete(record)
            db.commit()
            self.logger.info(f"删除测评记录成功: ID {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除测评记录失败: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def search_records(self, model_name: str = None, dataset_name: str = None,
                      model_type: str = None, status: str = None,
                      min_score: float = None, max_score: float = None,
                      start_date: datetime = None, end_date: datetime = None,
                      limit: int = 100, offset: int = 0) -> Tuple[List[EvaluationRecord], int]:
        """搜索测评记录"""
        try:
            db = next(get_db())
            query = db.query(EvaluationRecord)
            
            # 添加过滤条件
            if model_name:
                query = query.join(Model).filter(
                    Model.name.contains(model_name)
                )
            
            if dataset_name:
                query = query.join(Dataset).filter(
                    Dataset.name.contains(dataset_name)
                )
            
            if model_type:
                query = query.filter(EvaluationRecord.model_type == model_type)
            
            if status:
                query = query.filter(EvaluationRecord.status == status)
            
            if min_score is not None:
                query = query.filter(EvaluationRecord.score >= min_score)
            
            if max_score is not None:
                query = query.filter(EvaluationRecord.score <= max_score)
            
            if start_date:
                query = query.filter(EvaluationRecord.created_at >= start_date)
            
            if end_date:
                query = query.filter(EvaluationRecord.created_at <= end_date)
            
            # 获取总数
            total_count = query.count()
            
            # 排序和分页
            records = query.order_by(desc(EvaluationRecord.created_at)).offset(offset).limit(limit).all()
            
            return records, total_count
            
        except Exception as e:
            self.logger.error(f"搜索测评记录失败: {str(e)}")
            return [], 0
        finally:
            db.close()
    
    def get_record_statistics(self) -> Dict[str, Any]:
        """获取测评记录统计信息"""
        try:
            db = next(get_db())
            
            # 总记录数
            total_records = db.query(EvaluationRecord).count()
            
            # 成功记录数
            successful_records = db.query(EvaluationRecord).filter(
                EvaluationRecord.status == "completed"
            ).count()
            
            # 失败记录数
            failed_records = db.query(EvaluationRecord).filter(
                EvaluationRecord.status == "failed"
            ).count()
            
            # 平均分数
            avg_score = db.query(EvaluationRecord.score).filter(
                EvaluationRecord.score.isnot(None)
            ).all()
            average_score = sum([record[0] for record in avg_score]) / len(avg_score) if avg_score else 0
            
            # 模型类型分布
            model_type_stats = {}
            model_types = db.query(EvaluationRecord.model_type).distinct().all()
            for model_type in model_types:
                count = db.query(EvaluationRecord).filter(
                    EvaluationRecord.model_type == model_type[0]
                ).count()
                model_type_stats[model_type[0]] = count
            
            # 最近7天的记录数
            recent_date = datetime.now().timestamp() - 7 * 24 * 3600
            recent_records = db.query(EvaluationRecord).filter(
                EvaluationRecord.created_at >= datetime.fromtimestamp(recent_date)
            ).count()
            
            return {
                'total_records': total_records,
                'successful_records': successful_records,
                'failed_records': failed_records,
                'success_rate': successful_records / total_records if total_records > 0 else 0,
                'average_score': average_score,
                'model_type_distribution': model_type_stats,
                'recent_7_days_records': recent_records
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {}
        finally:
            db.close()
    
    def get_model_rankings(self, dataset_id: int, metric: str = "score", limit: int = 10) -> List[Dict[str, Any]]:
        """获取模型排行榜"""
        try:
            db = next(get_db())
            
            # 根据指标排序
            if metric == "score":
                order_field = EvaluationRecord.score
            elif metric == "accuracy":
                order_field = EvaluationRecord.accuracy
            elif metric == "speed":  # 基于执行时间排序
                order_field = EvaluationRecord.execution_time
            else:
                order_field = EvaluationRecord.score
            
            records = db.query(EvaluationRecord).filter(
                EvaluationRecord.dataset_id == dataset_id,
                EvaluationRecord.status == "completed"
            ).join(Model).order_by(desc(order_field)).limit(limit).all()
            
            rankings = []
            for i, record in enumerate(records, 1):
                rankings.append({
                    'rank': i,
                    'model_id': record.model_id,
                    'model_name': record.model.name,
                    'model_type': record.model_type,
                    'score': getattr(record, metric),
                    'created_at': record.created_at.isoformat() if record.created_at else None
                })
            
            return rankings
            
        except Exception as e:
            self.logger.error(f"获取模型排行榜失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def export_records(self, format_type: str = "json", filters: Dict = None) -> str:
        """导出测评记录"""
        try:
            # 获取记录
            if filters:
                records, _ = self.search_records(**filters)
            else:
                records = self.get_all_records(limit=10000)  # 限制导出数量
            
            if format_type.lower() == "json":
                return self._export_to_json(records)
            elif format_type.lower() == "csv":
                return self._export_to_csv(records)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
                
        except Exception as e:
            self.logger.error(f"导出记录失败: {str(e)}")
            raise
    
    def _export_to_json(self, records: List[EvaluationRecord]) -> str:
        """导出为JSON格式"""
        import json
        
        data = []
        for record in records:
            data.append({
                'id': record.id,
                'task_id': record.task_id,
                'model_id': record.model_id,
                'dataset_id': record.dataset_id,
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
                'evaluation_time': record.evaluation_time,
                'status': record.status,
                'error_message': record.error_message,
                'created_at': record.created_at.isoformat() if record.created_at else None
            })
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _export_to_csv(self, records: List[EvaluationRecord]) -> str:
        """导出为CSV格式"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        headers = ['ID', '任务ID', '模型ID', '数据集ID', '分数', '执行时间', 
                  '内存使用', '模型类型', '准确率', '损失', '困惑度', '状态', '创建时间']
        writer.writerow(headers)
        
        # 写入数据
        for record in records:
            writer.writerow([
                record.id,
                record.task_id,
                record.model_id,
                record.dataset_id,
                record.score,
                record.execution_time,
                record.memory_usage,
                record.model_type,
                record.accuracy,
                record.loss,
                record.perplexity,
                record.status,
                record.created_at.isoformat() if record.created_at else ''
            ])
        
        return output.getvalue()
