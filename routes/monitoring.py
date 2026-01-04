from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging

from services.gpu_monitor import GPUMonitor

router = APIRouter()
gpu_monitor = GPUMonitor()

@router.get("/gpu/status")
async def get_gpu_status():
    """获取GPU状态"""
    try:
        result = gpu_monitor.get_gpu_status()
        return result
    except Exception as e:
        logging.error(f"获取GPU状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gpu/comprehensive")
async def get_comprehensive_status():
    """获取全面系统状态"""
    try:
        result = gpu_monitor.get_comprehensive_status()
        return result
    except Exception as e:
        logging.error(f"获取全面状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gpu/processes")
async def get_gpu_processes():
    """获取GPU进程信息"""
    try:
        result = gpu_monitor.get_gpu_processes()
        return result
    except Exception as e:
        logging.error(f"获取GPU进程失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gpu/power")
async def get_power_consumption():
    """获取GPU功耗信息"""
    try:
        result = gpu_monitor.get_power_consumption()
        return result
    except Exception as e:
        logging.error(f"获取GPU功耗失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gpu/monitor/history")
async def monitor_gpu_history(duration_minutes: int = 60):
    """监控GPU使用历史"""
    try:
        result = gpu_monitor.monitor_gpu_usage_history(duration_minutes)
        return result  
    except Exception as e:
        logging.error(f"监控GPU历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gpu/alert")
async def set_gpu_alert(
    temperature_threshold: float = None,    
    memory_threshold: float = None,
    utilization_threshold: float = None,
    power_threshold: float = None
):
    """设置GPU监控告警"""
    try:
        result = gpu_monitor.set_gpu_alert(
            temperature_threshold, memory_threshold, 
            utilization_threshold, power_threshold
        )
        return result
    except Exception as e:
        logging.error(f"设置GPU告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/info")
async def get_system_info():
    """获取系统信息"""
    try:
        result = gpu_monitor.get_system_info()
        return result
    except Exception as e:
        logging.error(f"获取系统信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nvidia-smi")
async def get_nvidia_smi_output():
    """获取nvidia-smi输出"""
    try:
        result = gpu_monitor.get_nvidia_smi_output()
        return result
    except Exception as e:
        logging.error(f"获取nvidia-smi输出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_system_health():
    """获取系统健康状态"""
    try:
        comprehensive_status = gpu_monitor.get_comprehensive_status()
        if comprehensive_status['success']:
            health_data = comprehensive_status['data']['summary']['health_status']
            return {
                'success': True,
                'data': health_data
            }
        else:
            return {
                'success': False,
                'error': comprehensive_status.get('error', '无法获取系统健康状态')
            }
    except Exception as e:
        logging.error(f"获取系统健康状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_monitoring_summary():
    """获取监控摘要"""
    try:
        gpu_status = gpu_monitor.get_gpu_status()
        system_info = gpu_monitor.get_system_info()
        nvidia_smi = gpu_monitor.get_nvidia_smi_output()
        
        # 计算摘要信息
        summary = {
            'timestamp': gpu_status.get('timestamp', ''),
            'gpu_available': gpu_status.get('success', False),
            'gpu_count': 0,
            'total_memory_gb': 0,
            'memory_usage_percent': 0,
            'max_temperature': 0,
            'max_utilization': 0,
            'system_healthy': True
        }
        
        if gpu_status.get('success') and 'data' in gpu_status:
            gpus = gpu_status['data']['gpus']
            summary['gpu_count'] = len(gpus)
            
            total_memory = 0
            total_used_memory = 0
            max_temp = 0
            max_util = 0
            
            for gpu in gpus:
                total_memory += gpu.get('memory_total', 0)
                total_used_memory += gpu.get('memory_used', 0)
                max_temp = max(max_temp, gpu.get('temperature', 0))
                max_util = max(max_util, gpu.get('load', 0))
            
            summary['total_memory_gb'] = round(total_memory / 1024, 2)
            summary['memory_usage_percent'] = round((total_used_memory / total_memory) * 100, 2) if total_memory > 0 else 0
            summary['max_temperature'] = max_temp
            summary['max_utilization'] = round(max_util, 2)
            
            # 简单的健康判断
            summary['system_healthy'] = max_temp < 85 and max_util < 95
        
        return {
            'success': True,
            'data': summary
        }
    except Exception as e:
        logging.error(f"获取监控摘要失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
