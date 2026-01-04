import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

class ModelManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models_dir = "/home/a/ServiceEndFiles/Models"
        self.supported_formats = {
            '.bin', '.safetensors', '.onnx', '.pt', '.pth',
            'config.json', 'tokenizer.json', 'tokenizer_config.json'
        }
        
    def scan_local_models(self) -> Dict[str, Any]:
        """扫描本地模型目录"""
        try:
            models = []
            models_path = Path(self.models_dir)

            if not models_path.exists():
                models_path.mkdir(parents=True, exist_ok=True)

            for model_dir in models_path.iterdir():
                if model_dir.is_dir():
                    model_info = self._analyze_model_directory(model_dir)
                    if model_info:
                        models.append(model_info)
                        # print(model_info)
            # print(models)
            return {
                'success': True,
                'data': {
                    'models': models,
                    'total': len(models),
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"扫描本地模型失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _analyze_model_directory(self, model_dir: Path) -> Optional[Dict[str, Any]]:
        """分析模型目录"""
        try:
            model_info = {
                'name': model_dir.name,
                'path': str(model_dir),
                'type': 'local',
                'size': 0,
                'files': [],
                'has_config': False,
                'has_tokenizer': False,
                'model_format': None,
                'created_at': datetime.fromtimestamp(model_dir.stat().st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(model_dir.stat().st_mtime).isoformat()
            }
            
            total_size = 0
            for file_path in model_dir.rglob('*'):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    file_info = {
                        'name': file_path.name,
                        'path': str(file_path.relative_to(model_dir)),
                        'size': file_size,
                        'extension': file_path.suffix.lower()
                    }
                    model_info['files'].append(file_info)
                    # print(file_path.name)
                    # 检查配置文件
                    if file_path.name in ['config.json', 'generation_config.json']:
                        model_info['has_config'] = True
                    
                    # 检查分词器文件
                    if file_path.name in ['tokenizer.json', 'tokenizer_config.json', 'vocab.txt']:
                        model_info['has_tokenizer'] = True
                    
                    # 检测模型格式
                    if file_path.suffix.lower() in ['.bin', '.safetensors', '.onnx', '.pt', '.pth']:
                        model_info['model_format'] = file_path.suffix.lower()[1:]
            
            # raise Exception(f"test")
            
            model_info['size'] = total_size
            
            # 验证模型完整性
            if not model_info['has_config']:
                self.logger.warning(f"模型 {model_dir.name} 缺少配置文件")
                # print(model_)
            
            return model_info
            
        except Exception as e:
            self.logger.error(f"分析模型目录 {model_dir} 失败: {str(e)}")
            return None
    
    def import_model(self, model_path: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """导入模型"""
        try:
            model_path_obj = Path(model_path)
            
            if not model_path_obj.exists():
                return {
                    'success': False,
                    'error': f'模型路径不存在: {model_path}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 如果是文件路径，尝试找到对应的目录
            if model_path_obj.is_file():
                model_dir = model_path_obj.parent
            else:
                model_dir = model_path_obj
            
            # 分析模型
            model_info = self._analyze_model_directory(model_dir)
            if not model_info:
                return {
                    'success': False,
                    'error': '无法识别的模型格式',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 使用自定义名称或默认名称
            if model_name:
                model_info['name'] = model_name
            
            return {
                'success': True,
                'data': {
                    'model': model_info,
                    'message': f'模型 {model_info["name"]} 导入成功',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"导入模型失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_models_list(self) -> Dict[str, Any]:
        """获取所有模型列表"""
        try:
            result = self.scan_local_models()
            if result['success']:
                return result
            else:
                return {
                    'success': True,
                    'data': {
                        'models': [],
                        'total': 0,
                        'timestamp': datetime.now().isoformat()
                    }
                }
        except Exception as e:
            self.logger.error(f"获取模型列表失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_model_info(self, model_path: str) -> Dict[str, Any]:
        """获取指定模型信息"""
        try:
            model_path_obj = Path(model_path)
            if not model_path_obj.exists():
                return {
                    'success': False,
                    'error': '模型路径不存在',
                    'timestamp': datetime.now().isoformat()
                }
            
            if model_path_obj.is_file():
                model_dir = model_path_obj.parent
            else:
                model_dir = model_path_obj
            
            model_info = self._analyze_model_directory(model_dir)
            if not model_info:
                return {
                    'success': False,
                    'error': '无法分析模型信息',
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'success': True,
                'data': model_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取模型信息失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def remove_model(self, model_path: str) -> Dict[str, Any]:
        """移除模型"""
        try:
            model_path_obj = Path(model_path)
            if not model_path_obj.exists():
                return {
                    'success': False,
                    'error': '模型路径不存在',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 如果是本地模型目录，删除整个目录
            if model_path_obj.is_dir() and model_path_obj.exists():
                import shutil
                shutil.rmtree(model_path_obj)
                return {
                    'success': True,
                    'message': f'模型 {model_path} 已成功移除',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': '只能移除本地模型目录',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"移除模型失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def validate_model(self, model_path: str) -> bool:
        """验证模型路径是否有效"""
        try:
            model_path_obj = Path(model_path)
            if not model_path_obj.exists():
                return False
            
            if model_path_obj.is_dir():
                # 检查目录中是否有模型文件
                for file_path in model_path_obj.rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                        return True
                return False
            elif model_path_obj.is_file():
                # 检查文件是否是支持的格式
                return model_path_obj.suffix.lower() in self.supported_formats
            
            return False
            
        except Exception as e:
            self.logger.error(f"验证模型失败: {str(e)}")
            return False
