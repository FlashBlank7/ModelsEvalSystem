import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from services.evaluation_engine import EvaluationEngine
from services.task_queue import TaskQueue
from services.records_manager import RecordsManager
from services.model_manager import ModelManager
from services.dataset_manager import DatasetManager
from database.models import EvaluationTask
from database.config import get_db

class BatchEvaluationManager:
    """批量测评和统一报告管理系统"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.evaluation_engine = EvaluationEngine()
        self.task_queue = TaskQueue()
        self.records_manager = RecordsManager()
        self.model_manager = ModelManager()
        self.dataset_manager = DatasetManager()
    
    def create_batch_evaluation(self, model_paths: List[str], dataset_name: str,
                               config: Dict[str, Any] = None, 
                               task_name: str = None,
                               parallel: bool = True) -> Dict[str, Any]:
        """创建批量测评任务"""
        try:
            if not model_paths:
                raise ValueError("模型路径列表不能为空")
            
            if not dataset_name:
                raise ValueError("数据集名称不能为空")
            
            # 生成任务名称
            if not task_name:
                task_name = f"批量测评-{len(model_paths)}个模型-{dataset_name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 验证数据集
            dataset_validation = self.dataset_manager.validate_dataset(dataset_name)
            if not dataset_validation['success']:
                return {
                    'success': False,
                    'error': f"数据集验证失败: {dataset_validation.get('error', '未知错误')}",
                    'timestamp': datetime.now().isoformat()
                }
            
            # 验证模型
            valid_models = []
            invalid_models = []
            
            for model_path in model_paths:
                if model_path.startswith(('http://', 'https://')):
                    # API模型
                    connection_test = self.evaluation_engine.test_api_connection(model_path, config)
                    if connection_test['success']:
                        valid_models.append(model_path)
                    else:
                        invalid_models.append({'path': model_path, 'error': connection_test.get('error', '连接失败')})
                else:
                    # 本地模型
                    model_info = self.model_manager.get_model_info(model_path)
                    if model_info['success']:
                        valid_models.append(model_path)
                    else:
                        invalid_models.append({'path': model_path, 'error': model_info.get('error', '模型信息获取失败')})
            
            if not valid_models:
                return {
                    'success': False,
                    'error': "没有有效的模型可以进行测评",
                    'invalid_models': invalid_models,
                    'timestamp': datetime.now().isoformat()
                }
            
            # 创建批量任务
            batch_task = {
                'task_type': 'batch',
                'name': task_name,
                'model_paths': valid_models,
                'dataset_name': dataset_name,
                'config': config or {},
                'parallel': parallel,
                'status': 'pending'
            }
            
            # 添加到任务队列
            task_id = self.task_queue.add_task(batch_task)
            
            self.logger.info(f"创建批量测评任务成功: {task_name}, 任务ID: {task_id}")
            
            return {
                'success': True,
                'task_id': task_id,
                'task_name': task_name,
                'total_models': len(model_paths),
                'valid_models': len(valid_models),
                'invalid_models': len(invalid_models),
                'valid_model_paths': valid_models,
                'invalid_model_details': invalid_models,
                'dataset_name': dataset_name,
                'parallel_execution': parallel,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"创建批量测评任务失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def execute_batch_evaluation(self, task_id: int) -> Dict[str, Any]:
        """执行批量测评"""
        try:
            # 获取任务信息
            task_info = self.task_queue.get_task_status(task_id)
            if not task_info:
                return {
                    'success': False,
                    'error': f"任务不存在: {task_id}",
                    'timestamp': datetime.now().isoformat()
                }
            
            if task_info['status'] != 'pending':
                return {
                    'success': False,
                    'error': f"任务状态不正确: {task_info['status']}",
                    'timestamp': datetime.now().isoformat()
                }
            
            # 开始执行
            self.logger.info(f"开始执行批量测评任务: {task_id}")
            
            # 获取任务详情
            task_data = self.task_queue.task_history.get(task_id, {})
            model_paths = task_data.get('model_paths', [])
            dataset_name = task_data.get('dataset_name', '')
            config = task_data.get('config', {})
            parallel = task_data.get('parallel', True)
            
            if not model_paths:
                return {
                    'success': False,
                    'error': "任务中没有有效的模型",
                    'timestamp': datetime.now().isoformat()
                }
            
            # 执行批量测评
            if parallel:
                results = self._execute_parallel_batch(model_paths, dataset_name, config, task_id)
            else:
                results = self._execute_sequential_batch(model_paths, dataset_name, config, task_id)
            
            # 生成综合报告
            report = self.generate_comprehensive_report(results, dataset_name, model_paths)
            
            # 更新任务状态
            self.task_queue._update_task_status(task_id, "completed", report)
            
            self.logger.info(f"批量测评任务执行完成: {task_id}")
            
            return {
                'success': True,
                'task_id': task_id,
                'results': results,
                'report': report,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"批量测评执行失败: {str(e)}")
            self.task_queue._update_task_status(task_id, "failed", str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _execute_parallel_batch(self, model_paths: List[str], dataset_name: str, 
                               config: Dict[str, Any], task_id: int) -> List[Dict[str, Any]]:
        """并行执行批量测评"""
        results = []
        total_models = len(model_paths)
        
        with ThreadPoolExecutor(max_workers=min(len(model_paths), 4)) as executor:
            # 提交所有任务
            future_to_model = {
                executor.submit(self._evaluate_single_model, model_path, dataset_name, config, task_id): model_path
                for model_path in model_paths
            }
            
            # 收集结果
            for i, future in enumerate(as_completed(future_to_model)):
                model_path = future_to_model[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 触发进度回调
                    progress = (i + 1) / total_models
                    self.task_queue._trigger_callback('on_progress', task_id, {
                        'progress': progress,
                        'current_model': model_path,
                        'completed': i + 1,
                        'total': total_models
                    })
                    
                except Exception as e:
                    self.logger.error(f"模型 {model_path} 并行测评失败: {str(e)}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'model_path': model_path,
                        'model_type': 'unknown'
                    })
        
        return results
    
    def _execute_sequential_batch(self, model_paths: List[str], dataset_name: str, 
                                 config: Dict[str, Any], task_id: int) -> List[Dict[str, Any]]:
        """顺序执行批量测评"""
        results = []
        total_models = len(model_paths)
        
        for i, model_path in enumerate(model_paths):
            try:
                result = self._evaluate_single_model(model_path, dataset_name, config, task_id)
                results.append(result)
                
                # 触发进度回调
                progress = (i + 1) / total_models
                self.task_queue._trigger_callback('on_progress', task_id, {
                    'progress': progress,
                    'current_model': model_path,
                    'completed': i + 1,
                    'total': total_models
                })
                
            except Exception as e:
                self.logger.error(f"模型 {model_path} 顺序测评失败: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'model_path': model_path,
                    'model_type': 'unknown'
                })
        
        return results
    
    def _evaluate_single_model(self, model_path: str, dataset_name: str, 
                              config: Dict[str, Any], task_id: int) -> Dict[str, Any]:
        """测评单个模型"""
        try:
            # 检查模型类型
            if model_path.startswith(('http://', 'https://')):
                # API模型
                result = self.evaluation_engine.evaluate_api_model(model_path, dataset_name, config)
            else:
                # 本地模型
                result = self.evaluation_engine.evaluate_local_model(model_path, dataset_name, config)
            
            if result['success']:
                # 创建测评记录
                try:
                    model_info = self.model_manager.get_model_info(model_path)
                    model_id = None
                    if model_info['success']:
                        model_id = model_info['data']['id']
                    
                    dataset_info = self.dataset_manager.validate_dataset(dataset_name)
                    dataset_id = None
                    if dataset_info['success']:
                        dataset_id = dataset_info['data']['id']
                    
                    if model_id and dataset_id:
                        self.records_manager.create_record(
                            task_id=task_id,
                            model_id=model_id,
                            dataset_id=dataset_id,
                            score=result['data'].get('score'),
                            metrics=result['data'].get('metrics', {}),
                            results=result['data'],
                            execution_time=result['data'].get('execution_time'),
                            memory_usage=result['data'].get('memory_usage'),
                            model_type=result['data'].get('model_type', 'local'),
                            status='completed'
                        )
                except Exception as e:
                    self.logger.warning(f"创建测评记录失败: {str(e)}")
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model_path': model_path,
                'model_type': 'unknown'
            }
    
    def generate_comprehensive_report(self, results: List[Dict[str, Any]], 
                                    dataset_name: str, model_paths: List[str]) -> Dict[str, Any]:
        """生成综合报告"""
        try:
            successful_results = [r for r in results if r.get('success', False)]
            failed_results = [r for r in results if not r.get('success', False)]
            
            if not successful_results:
                return {
                    'error': '没有成功的测评结果，无法生成报告',
                    'total_models': len(model_paths),
                    'successful_count': 0,
                    'failed_count': len(failed_results)
                }
            
            # 基础统计
            total_models = len(model_paths)
            successful_count = len(successful_results)
            failed_count = len(failed_results)
            success_rate = successful_count / total_models if total_models > 0 else 0
            
            # 分数统计
            scores = [r['data'].get('score', 0) for r in successful_results if 'data' in r and 'score' in r['data']]
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            
            # 执行时间统计
            exec_times = [r['data'].get('execution_time', 0) for r in successful_results if 'data' in r and 'execution_time' in r['data']]
            avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
            max_exec_time = max(exec_times) if exec_times else 0
            min_exec_time = min(exec_times) if exec_times else 0
            
            # 内存使用统计
            memory_usage = [r['data'].get('memory_usage', 0) for r in successful_results if 'data' in r and 'memory_usage' in r['data']]
            avg_memory = sum(memory_usage) / len(memory_usage) if memory_usage else 0
            max_memory = max(memory_usage) if memory_usage else 0
            min_memory = min(memory_usage) if memory_usage else 0
            
            # 模型类型分布
            model_type_dist = {}
            for result in successful_results:
                model_type = result['data'].get('model_type', 'unknown')
                model_type_dist[model_type] = model_type_dist.get(model_type, 0) + 1
            
            # 排行榜
            rankings = self._generate_model_rankings(successful_results)
            
            # 性能分析
            performance_analysis = self._analyze_performance(successful_results)
            
            # 生成图表数据
            chart_data = self._generate_chart_data(successful_results, failed_results)
            
            report = {
                'summary': {
                    'dataset_name': dataset_name,
                    'total_models': total_models,
                    'successful_evaluations': successful_count,
                    'failed_evaluations': failed_count,
                    'success_rate': round(success_rate * 100, 2),
                    'evaluation_date': datetime.now().isoformat()
                },
                'statistics': {
                    'score': {
                        'average': round(avg_score, 4),
                        'max': round(max_score, 4),
                        'min': round(min_score, 4),
                        'std': self._calculate_std(scores)
                    },
                    'execution_time': {
                        'average': round(avg_exec_time, 2),
                        'max': round(max_exec_time, 2),
                        'min': round(min_exec_time, 2)
                    },
                    'memory_usage': {
                        'average': round(avg_memory, 2),
                        'max': round(max_memory, 2),
                        'min': round(min_memory, 2)
                    }
                },
                'model_type_distribution': model_type_dist,
                'rankings': rankings,
                'performance_analysis': performance_analysis,
                'chart_data': chart_data,
                'detailed_results': {
                    'successful': successful_results,
                    'failed': failed_results
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成综合报告失败: {str(e)}")
            return {'error': str(e)}
    
    def _generate_model_rankings(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成模型排行榜"""
        try:
            # 按分数排序
            ranked_results = sorted(results, key=lambda x: x.get('data', {}).get('score', 0), reverse=True)
            
            rankings = []
            for i, result in enumerate(ranked_results, 1):
                data = result.get('data', {})
                rankings.append({
                    'rank': i,
                    'model_path': result.get('model_path', 'unknown'),
                    'model_type': data.get('model_type', 'unknown'),
                    'score': data.get('score', 0),
                    'execution_time': data.get('execution_time', 0),
                    'memory_usage': data.get('memory_usage', 0),
                    'metrics': data.get('metrics', {})
                })
            
            return rankings
            
        except Exception as e:
            self.logger.error(f"生成排行榜失败: {str(e)}")
            return []
    
    def _analyze_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析性能"""
        try:
            if not results:
                return {}
            
            # 按模型类型分析
            type_analysis = {}
            for result in results:
                data = result.get('data', {})
                model_type = data.get('model_type', 'unknown')
                
                if model_type not in type_analysis:
                    type_analysis[model_type] = {
                        'count': 0,
                        'scores': [],
                        'exec_times': [],
                        'memory_usage': []
                    }
                
                type_analysis[model_type]['count'] += 1
                if 'score' in data:
                    type_analysis[model_type]['scores'].append(data['score'])
                if 'execution_time' in data:
                    type_analysis[model_type]['exec_times'].append(data['execution_time'])
                if 'memory_usage' in data:
                    type_analysis[model_type]['memory_usage'].append(data['memory_usage'])
            
            # 计算平均值
            for model_type in type_analysis:
                analysis = type_analysis[model_type]
                if analysis['scores']:
                    analysis['avg_score'] = sum(analysis['scores']) / len(analysis['scores'])
                if analysis['exec_times']:
                    analysis['avg_exec_time'] = sum(analysis['exec_times']) / len(analysis['exec_times'])
                if analysis['memory_usage']:
                    analysis['avg_memory'] = sum(analysis['memory_usage']) / len(analysis['memory_usage'])
            
            return type_analysis
            
        except Exception as e:
            self.logger.error(f"性能分析失败: {str(e)}")
            return {}
    
    def _generate_chart_data(self, successful_results: List[Dict[str, Any]], 
                           failed_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成图表数据"""
        try:
            # 分数分布直方图数据
            scores = [r['data'].get('score', 0) for r in successful_results if 'data' in r and 'score' in r['data']]
            score_bins = self._create_histogram_bins(scores, bins=10)
            
            # 执行时间分布
            exec_times = [r['data'].get('execution_time', 0) for r in successful_results if 'data' in r and 'execution_time' in r['data']]
            time_bins = self._create_histogram_bins(exec_times, bins=10)
            
            # 模型类型饼图数据
            type_counts = {}
            for result in successful_results:
                model_type = result['data'].get('model_type', 'unknown')
                type_counts[model_type] = type_counts.get(model_type, 0) + 1
            
            return {
                'score_distribution': {
                    'bins': score_bins['bins'],
                    'counts': score_bins['counts']
                },
                'execution_time_distribution': {
                    'bins': time_bins['bins'],
                    'counts': time_bins['counts']
                },
                'model_type_pie': {
                    'labels': list(type_counts.keys()),
                    'data': list(type_counts.values())
                },
                'success_vs_failure': {
                    'labels': ['成功', '失败'],
                    'data': [len(successful_results), len(failed_results)]
                }
            }
            
        except Exception as e:
            self.logger.error(f"生成图表数据失败: {str(e)}")
            return {}
    
    def _create_histogram_bins(self, values: List[float], bins: int = 10) -> Dict[str, List[float]]:
        """创建直方图分箱数据"""
        if not values:
            return {'bins': [], 'counts': []}
        
        min_val = min(values)
        max_val = max(values)
        bin_width = (max_val - min_val) / bins if bins > 0 else 1
        
        bin_edges = [min_val + i * bin_width for i in range(bins + 1)]
        bin_counts = [0] * bins
        
        for value in values:
            bin_index = min(int((value - min_val) / bin_width), bins - 1)
            bin_counts[bin_index] += 1
        
        bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(bins)]
        
        return {
            'bins': bin_centers,
            'counts': bin_counts
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def get_batch_evaluation_history(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取批量测评历史"""
        try:
            all_tasks = self.task_queue.get_all_tasks()
            batch_tasks = [task for task in all_tasks if task.get('task_type') == 'batch']
            
            # 按创建时间排序
            batch_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # 分页
            paginated_tasks = batch_tasks[offset:offset + limit]
            
            return paginated_tasks
            
        except Exception as e:
            self.logger.error(f"获取批量测评历史失败: {str(e)}")
            return []
    
    def export_batch_report(self, task_id: int, format_type: str = "json") -> str:
        """导出批量测评报告"""
        try:
            task_info = self.task_queue.get_task_status(task_id)
            if not task_info:
                raise ValueError(f"任务不存在: {task_id}")
            
            result_data = task_info.get('result', {})
            if not result_data:
                raise ValueError("任务结果不存在")
            
            if format_type.lower() == "json":
                return json.dumps(result_data, ensure_ascii=False, indent=2)
            elif format_type.lower() == "csv":
                return self._export_report_to_csv(result_data)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
                
        except Exception as e:
            self.logger.error(f"导出报告失败: {str(e)}")
            raise
    
    def _export_report_to_csv(self, report_data: Dict[str, Any]) -> str:
        """导出报告为CSV格式"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入报告标题
        writer.writerow(['批量测评报告'])
        writer.writerow([])
        
        # 写入汇总信息
        summary = report_data.get('summary', {})
        writer.writerow(['数据集', summary.get('dataset_name', '')])
        writer.writerow(['总模型数', summary.get('total_models', 0)])
        writer.writerow(['成功测评数', summary.get('successful_evaluations', 0)])
        writer.writerow(['失败测评数', summary.get('failed_evaluations', 0)])
        writer.writerow(['成功率(%)', summary.get('success_rate', 0)])
        writer.writerow([])
        
        # 写入排行榜
        rankings = report_data.get('rankings', [])
        if rankings:
            writer.writerow(['排行榜'])
            writer.writerow(['排名', '模型路径', '模型类型', '分数', '执行时间', '内存使用'])
            
            for rank in rankings:
                writer.writerow([
                    rank.get('rank', ''),
                    rank.get('model_path', ''),
                    rank.get('model_type', ''),
                    rank.get('score', ''),
                    rank.get('execution_time', ''),
                    rank.get('memory_usage', '')
                ])
        
        return output.getvalue()
