import os
import subprocess
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import GPUtil
import psutil
import logging

class GPUMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_gpu_status(self) -> Dict[str, Any]:
        """获取 GPU 状态信息"""
        try:
            gpus = GPUtil.getGPUs()
            gpu_info = []
            
            for gpu in gpus:
                gpu_data = {
                    'id': gpu.id,
                    'name': gpu.name,
                    'memory_total': gpu.memoryTotal,
                    'memory_used': gpu.memoryUsed,
                    'memory_free': gpu.memoryFree,
                    'memory_percent': (gpu.memoryUsed / gpu.memoryTotal) * 100,
                    'temperature': gpu.temperature,
                    'load': gpu.load * 100,
                    'uuid': gpu.uuid
                }
                gpu_info.append(gpu_data)
            
            return {
                'success': True,
                'data': {
                    'gpus': gpu_info,
                    'total_gpus': len(gpus),
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"获取GPU状态失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_nvidia_smi_output(self) -> Dict[str, Any]:
        """获取 nvidia-smi 输出"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu', 
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpu_data = []
                
                for line in lines:
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 7:
                        gpu_data.append({
                            'id': int(parts[0]),
                            'name': parts[1],
                            'memory_total': int(parts[2]),
                            'memory_used': int(parts[3]),
                            'memory_free': int(parts[4]),
                            'temperature': int(parts[5]),
                            'utilization': int(parts[6])
                        })
                
                return {
                    'success': True,
                    'data': {
                        'gpus': gpu_data,
                        'raw_output': result.stdout,
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"获取nvidia-smi输出失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            return {
                'success': True,
                'data': {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory': {
                        'total': psutil.virtual_memory().total,
                        'available': psutil.virtual_memory().available,
                        'percent': psutil.virtual_memory().percent,
                        'used': psutil.virtual_memory().used
                    },
                    'disk': {
                        'total': psutil.disk_usage('/').total,
                        'used': psutil.disk_usage('/').used,
                        'free': psutil.disk_usage('/').free,
                        'percent': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
                    },
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_gpu_availability(self) -> bool:
        """检查GPU是否可用"""
        try:
            gpus = GPUtil.getGPUs()
            return len(gpus) > 0
        except:
            return False    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """获取全面的系统状态信息"""
        try:
            # 获取GPU状态
            gpu_status = self.get_gpu_status()
            
            # 获取系统信息
            system_info = self.get_system_info()
            
            # 获取nvidia-smi详细信息
            nvidia_smi = self.get_nvidia_smi_output()
            
            # 综合分析
            total_gpu_memory = 0
            total_gpu_used = 0
            gpu_count = 0
            max_temperature = 0
            max_utilization = 0
            
            if gpu_status['success']:
                for gpu in gpu_status['data']['gpus']:
                    total_gpu_memory += gpu['memory_total']
                    total_gpu_used += gpu['memory_used']
                    gpu_count += 1
                    max_temperature = max(max_temperature, gpu['temperature'])
                    max_utilization = max(max_utilization, gpu['load'])
            
            # 生成健康状态评估
            health_status = self._assess_system_health(gpu_status, system_info)
            
            return {
                'success': True,
                'data': {
                    'timestamp': datetime.now().isoformat(),
                    'gpu_status': gpu_status,
                    'system_info': system_info,
                    'nvidia_smi': nvidia_smi,
                    'summary': {
                        'total_gpu_memory_gb': round(total_gpu_memory / 1024, 2),
                        'total_gpu_used_gb': round(total_gpu_used / 1024, 2),
                        'gpu_memory_usage_percent': round((total_gpu_used / total_gpu_memory) * 100, 2) if total_gpu_memory > 0 else 0,
                        'gpu_count': gpu_count,
                        'max_temperature': max_temperature,
                        'max_utilization': round(max_utilization, 2),
                        'health_status': health_status
                    }
                }
            }
        except Exception as e:
            self.logger.error(f"获取全面状态失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _assess_system_health(self, gpu_status: Dict, system_info: Dict) -> str:
        """评估系统健康状态"""
        try:
            if not gpu_status['success'] or not system_info['success']:
                return 'unknown'
            
            # GPU健康评估
            gpu_health_issues = []
            if gpu_status['data']['gpus']:
                for gpu in gpu_status['data']['gpus']:
                    if gpu['temperature'] > 80:
                        gpu_health_issues.append(f"GPU {gpu['id']} 温度过高: {gpu['temperature']}°C")
                    if gpu['load'] > 90:
                        gpu_health_issues.append(f"GPU {gpu['id']} 利用率过高: {gpu['load']:.1f}%")
                    if gpu['memory_percent'] > 90:
                        gpu_health_issues.append(f"GPU {gpu['id']} 内存使用率过高: {gpu['memory_percent']:.1f}%")
            
            # 系统健康评估
            system_health_issues = []
            if system_info['data']['memory']['percent'] > 90:
                system_health_issues.append(f"系统内存使用率过高: {system_info['data']['memory']['percent']:.1f}%")
            if system_info['data']['cpu_percent'] > 90:
                system_health_issues.append(f"CPU使用率过高: {system_info['data']['cpu_percent']:.1f}%")
            
            # 综合评估
            if gpu_health_issues or system_health_issues:
                return 'warning'
            else:
                return 'healthy'
                
        except Exception as e:
            self.logger.error(f"系统健康评估失败: {str(e)}")
            return 'unknown'
    
    def get_gpu_processes(self) -> Dict[str, Any]:
        """获取GPU进程信息"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-compute-apps=pid,process_name,gpu_name,used_memory', 
                 '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                processes = []
                
                for line in lines:
                    if line.strip():
                        parts = [part.strip() for part in line.split(',')]
                        if len(parts) >= 4:
                            processes.append({
                                'pid': int(parts[0]) if parts[0].isdigit() else parts[0],
                                'process_name': parts[1],
                                'gpu_name': parts[2],
                                'used_memory_mb': int(parts[3]) if parts[3].isdigit() else 0
                            })
                
                return {
                    'success': True,
                    'data': {
                        'processes': processes,
                        'process_count': len(processes),
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"获取GPU进程信息失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def monitor_gpu_usage_history(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """监控GPU使用历史"""
        try:
            import time
            
            history_data = []
            interval_seconds = 10  # 每10秒记录一次
            total_records = (duration_minutes * 60) // interval_seconds
            
            for i in range(total_records):
                gpu_status = self.get_gpu_status()
                if gpu_status['success']:
                    history_data.append({
                        'timestamp': datetime.now().isoformat(),
                        'gpus': gpu_status['data']['gpus']
                    })
                
                if i < total_records - 1:  # 不是最后一次记录
                    time.sleep(interval_seconds)
            
            # 计算统计信息
            stats = self._calculate_usage_stats(history_data)
            
            return {
                'success': True,
                'data': {
                    'history': history_data,
                    'statistics': stats,
                    'duration_minutes': duration_minutes,
                    'records_count': len(history_data),
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"GPU使用历史监控失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_usage_stats(self, history_data: List[Dict]) -> Dict[str, Any]:
        """计算使用统计信息"""
        if not history_data:
            return {}
        
        try:
            # 收集所有GPU的数据
            gpu_usage_data = {}
            gpu_memory_data = {}
            gpu_temperature_data = {}
            
            for record in history_data:
                timestamp = record['timestamp']
                for gpu in record['gpus']:
                    gpu_id = gpu['id']
                    
                    if gpu_id not in gpu_usage_data:
                        gpu_usage_data[gpu_id] = []
                        gpu_memory_data[gpu_id] = []
                        gpu_temperature_data[gpu_id] = []
                    
                    gpu_usage_data[gpu_id].append(gpu['load'])
                    gpu_memory_data[gpu_id].append(gpu['memory_percent'])
                    gpu_temperature_data[gpu_id].append(gpu['temperature'])
            
            # 计算统计信息
            stats = {}
            for gpu_id in gpu_usage_data:
                stats[f'gpu_{gpu_id}'] = {
                    'usage': {
                        'min': min(gpu_usage_data[gpu_id]),
                        'max': max(gpu_usage_data[gpu_id]),
                        'avg': sum(gpu_usage_data[gpu_id]) / len(gpu_usage_data[gpu_id])
                    },
                    'memory': {
                        'min': min(gpu_memory_data[gpu_id]),
                        'max': max(gpu_memory_data[gpu_id]),
                        'avg': sum(gpu_memory_data[gpu_id]) / len(gpu_memory_data[gpu_id])
                    },
                    'temperature': {
                        'min': min(gpu_temperature_data[gpu_id]),
                        'max': max(gpu_temperature_data[gpu_id]),
                        'avg': sum(gpu_temperature_data[gpu_id]) / len(gpu_temperature_data[gpu_id])
                    }
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"计算使用统计失败: {str(e)}")
            return {}
    
    def set_gpu_alert(self, gpu_id: int, alert_type: str, threshold: float, callback_func=None) -> bool:
        """设置GPU警报"""
        try:
            # 这里可以实现GPU警报功能
            # 由于这是一个演示，我们只是记录设置
            self.logger.info(f"设置GPU {gpu_id} 警报: {alert_type} > {threshold}")
            return True
        except Exception as e:
            self.logger.error(f"设置GPU警报失败: {str(e)}")
            return False
    
    def get_power_consumption(self) -> Dict[str, Any]:
        """获取GPU功耗信息"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,power.draw,power.limit', 
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                power_data = []
                
                for line in lines:
                    if line.strip():
                        parts = [part.strip() for part in line.split(',')]
                        if len(parts) >= 4:
                            power_data.append({
                                'id': int(parts[0]),
                                'name': parts[1],
                                'power_draw_watts': float(parts[2]) if parts[2] != '[N/A]' else 0,
                                'power_limit_watts': float(parts[3]) if parts[3] != '[N/A]' else 0,
                                'power_usage_percent': round((float(parts[2]) / float(parts[3])) * 100, 2) if parts[2] != '[N/A]' and parts[3] != '[N/A]' and float(parts[3]) > 0 else 0
                            })
                
                return {
                    'success': True,
                    'data': {
                        'gpus': power_data,
                        'total_power_draw': sum([gpu['power_draw_watts'] for gpu in power_data]),
                        'total_power_limit': sum([gpu['power_limit_watts'] for gpu in power_data]),
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"获取GPU功耗信息失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
