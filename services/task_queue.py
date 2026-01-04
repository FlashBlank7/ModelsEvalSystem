import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from queue import Queue
import threading
from concurrent.futures import ThreadPoolExecutor

from database.models import EvaluationTask
from database.config import get_db
from services.evaluation_engine import EvaluationEngine
# Unused imports removed to fix import error
# from services.model_manager import ModelManager
# from services.dataset_manager import DatasetManager

class TaskQueue:
    """测评任务队列管理系统"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.task_queue = Queue()
        self.task_history = {}
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.evaluation_engine = EvaluationEngine()
        self.model_manager = None  # Will be initialized when needed
        self.dataset_manager = None  # Will be initialized when needed
        
        # 任务回调函数
        self.task_callbacks = {
            'on_start': [],
            'on_progress': [],
            'on_complete': [],
            'on_error': []
        }
        
        # 启动队列处理线程
        self.queue_thread = None
        self.start_queue_processing()
    
    def start_queue_processing(self):
        """启动队列处理线程"""
        if not self.is_running:
            self.is_running = True
            self.queue_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.queue_thread.start()
            self.logger.info("任务队列处理已启动")
    
    def stop_queue_processing(self):
        """停止队列处理线程"""
        self.is_running = False
        if self.queue_thread:
            self.queue_thread.join(timeout=5)
        self.logger.info("任务队列处理已停止")
    
    def _process_queue(self):
        """队列处理主循环"""
        while self.is_running:
            try:
                if not self.task_queue.empty():
                    task_data = self.task_queue.get(timeout=1)
                    self._execute_task(task_data)
                    self.task_queue.task_done()
                else:
                    time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"队列处理错误: {str(e)}")
                time.sleep(1)
    
    def _execute_task(self, task_data: Dict[str, Any]):
        """执行单个任务"""
        try:
            task_id = task_data['task_id']
            self.logger.info(f"开始执行任务: {task_id}")
            
            # 更新任务状态为运行中
            self._update_task_status(task_id, "running")
            
            # 触发开始回调
            self._trigger_callback('on_start', task_id, task_data)
            
            # 执行具体的测评任务
            if task_data['task_type'] == "single":
                result = self._execute_single_evaluation(task_data)
            elif task_data['task_type'] == "batch":
                result = self._execute_batch_evaluation(task_data)
            elif task_data['task_type'] == "api":
                result = self._execute_api_evaluation(task_data)
            else:
                raise ValueError(f"未知的任务类型: {task_data['task_type']}")
            
            # 更新任务状态为完成
            self._update_task_status(task_id, "completed", result)
            
            # 触发完成回调
            self._trigger_callback('on_complete', task_id, result)
            
            self.logger.info(f"任务 {task_id} 执行完成")
            
        except Exception as e:
            self.logger.error(f"任务执行失败: {str(e)}")
            error_msg = str(e)
            
            # 更新任务状态为失败
            if 'task_id' in task_data:
                self._update_task_status(task_data['task_id'], "failed", error_msg)
            
            # 触发错误回调
            self._trigger_callback('on_error', task_data.get('task_id'), error_msg)
    
    def _execute_single_evaluation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个模型测评"""
        model_path = task_data['model_path']
        dataset_name = task_data['dataset_name']
        config = task_data.get('config', {})
        
        # 检查模型类型
        if model_path.startswith(('http://', 'https://')):
            # API模型
            return self.evaluation_engine.evaluate_api_model(
                model_path, dataset_name, config
            )
        else:
            # 本地模型
            return self.evaluation_engine.evaluate_local_model(
                model_path, dataset_name, config
            )
    
    def _execute_batch_evaluation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行批量模型测评"""
        model_paths = task_data['model_paths']
        dataset_name = task_data['dataset_name']
        config = task_data.get('config', {})
        
        results = []
        total_models = len(model_paths)
        
        for i, model_path in enumerate(model_paths):
            # 触发进度回调
            progress = (i + 1) / total_models
            self._trigger_callback('on_progress', task_data['task_id'], {
                'progress': progress,
                'current_model': model_path,
                'completed': i + 1,
                'total': total_models
            })
            
            try:
                if model_path.startswith(('http://', 'https://')):
                    result = self.evaluation_engine.evaluate_api_model(
                        model_path, dataset_name, config
                    )
                else:
                    result = self.evaluation_engine.evaluate_local_model(
                        model_path, dataset_name, config
                    )
                results.append(result)
            except Exception as e:
                self.logger.error(f"模型 {model_path} 测评失败: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'model_path': model_path
                })
        
        # 生成批量报告
        return {
            'success': True,
            'task_type': 'batch',
            'results': results,
            'summary': self._generate_batch_summary(results),
            'timestamp': datetime.now().isoformat()
        }
    
    def _execute_api_evaluation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行API模型测评"""
        model_path = task_data['model_path']
        dataset_name = task_data['dataset_name']
        config = task_data.get('config', {})
        
        return self.evaluation_engine.evaluate_api_model(
            model_path, dataset_name, config
        )
    
    def _generate_batch_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成批量测评总结"""
        successful_results = [r for r in results if r.get('success', False)]
        
        if not successful_results:
            return {'error': '没有成功的测评结果'}
        
        # 计算统计信息
        scores = [r.get('score', 0) for r in successful_results if 'score' in r]
        
        summary = {
            'total_models': len(results),
            'successful_evaluations': len(successful_results),
            'failed_evaluations': len(results) - len(successful_results),
            'average_score': sum(scores) / len(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'top_performers': sorted(successful_results, 
                                   key=lambda x: x.get('score', 0), 
                                   reverse=True)[:3]
        }
        
        return summary
    
    def _update_task_status(self, task_id: int, status: str, result: Any = None):
        """更新任务状态到数据库"""
        try:
            db = next(get_db())
            task = db.query(EvaluationTask).filter(EvaluationTask.id == task_id).first()
            if task:
                task.status = status
                if result:
                    task.result = result if isinstance(result, str) else str(result)
                    task.completed_at = datetime.now()
                db.commit()
        except Exception as e:
            self.logger.error(f"更新任务状态失败: {str(e)}")
        finally:
            db.close()
    
    def _trigger_callback(self, callback_type: str, task_id: Any, data: Any):
        """触发回调函数"""
        for callback in self.task_callbacks.get(callback_type, []):
            try:
                callback(task_id, data)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {str(e)}")
    
    def add_task(self, task_data: Dict[str, Any]) -> int:
        """添加任务到队列"""
        # 创建数据库记录
        try:
            db = next(get_db())
            task = EvaluationTask(
                name=task_data.get('name', '测评任务'),
                task_type=task_data.get('task_type', 'single'),
                model_path=task_data.get('model_path'),
                model_paths=task_data.get('model_paths', []),
                dataset_name=task_data.get('dataset_name'),
                config=task_data.get('config', {}),
                status="pending"
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            task_id = task.id
        except Exception as e:
            self.logger.error(f"创建任务记录失败: {str(e)}")
            raise
        finally:
            db.close()
        
        # 添加到队列
        task_data['task_id'] = task_id
        self.task_queue.put(task_data)
        self.task_history[task_id] = task_data
        
        self.logger.info(f"任务已添加到队列: {task_id}")
        return task_id
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            'is_running': self.is_running,
            'queue_size': self.task_queue.qsize(),
            'pending_tasks': list(self.task_history.keys()),
            'thread_alive': self.queue_thread.is_alive() if self.queue_thread else False
        }
    
    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            db = next(get_db())
            task = db.query(EvaluationTask).filter(EvaluationTask.id == task_id).first()
            if task:
                return {
                    'id': task.id,
                    'name': task.name,
                    'task_type': task.task_type,
                    'status': task.status,
                    'model_path': task.model_path,
                    'dataset_name': task.dataset_name,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'result': task.result
                }
        except Exception as e:
            self.logger.error(f"获取任务状态失败: {str(e)}")
        finally:
            db.close()
        
        return None
    
    def cancel_task(self, task_id: int) -> bool:
        """取消任务"""
        # 从队列中移除待执行的任务
        temp_queue = Queue()
        cancelled = False
        
        while not self.task_queue.empty():
            task = self.task_queue.get()
            if task.get('task_id') != task_id:
                temp_queue.put(task)
            else:
                cancelled = True
        
        # 将剩余任务放回原队列
        while not temp_queue.empty():
            self.task_queue.put(temp_queue.get())
        
        if cancelled:
            # 更新数据库状态
            self._update_task_status(task_id, "cancelled")
            self.logger.info(f"任务已取消: {task_id}")
        
        return cancelled
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        try:
            db = next(get_db())
            tasks = db.query(EvaluationTask).order_by(EvaluationTask.created_at.desc()).all()
            return [
                {
                    'id': task.id,
                    'name': task.name,
                    'task_type': task.task_type,
                    'status': task.status,
                    'model_path': task.model_path,
                    'dataset_name': task.dataset_name,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'result': task.result
                }
                for task in tasks
            ]
        except Exception as e:
            self.logger.error(f"获取任务列表失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def add_callback(self, callback_type: str, callback_func: Callable):
        """添加回调函数"""
        if callback_type in self.task_callbacks:
            self.task_callbacks[callback_type].append(callback_func)
    
    def remove_callback(self, callback_type: str, callback_func: Callable):
        """移除回调函数"""
        if callback_type in self.task_callbacks:
            try:
                self.task_callbacks[callback_type].remove(callback_func)
            except ValueError:
                pass
    
    def clear_queue(self):
        """清空队列"""
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except:
                break
        self.logger.info("任务队列已清空")
    
    def __del__(self):
        """析构函数"""
        self.stop_queue_processing()
        self.executor.shutdown(wait=True)
