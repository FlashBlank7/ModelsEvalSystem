import os
from typing import Dict, Any
import logging

class HuggingFaceConfig:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mirror_url = "https://hf-mirror.com"
        self.setup_environment()
    
    def setup_environment(self):
        """设置 HuggingFace 环境变量"""
        try:
            # 设置镜像地址
            os.environ['HF_ENDPOINT'] = self.mirror_url
            os.environ['HF_HOME'] = os.path.join(os.getcwd(), '.cache', 'huggingface')
            os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.getcwd(), '.cache', 'transformers')
            os.environ['HF_HUB_CACHE'] = os.path.join(os.getcwd(), '.cache', 'hub')
            
            # 设置下载超时
            os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'
            os.environ['HF_HUB_ETAG_TIMEOUT'] = '10'
            
            self.logger.info(f"设置 HuggingFace 镜像地址: {self.mirror_url}")
            return True
        except Exception as e:
            self.logger.error(f"设置 HuggingFace 环境变量失败: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            'success': True,
            'data': {
                'mirror_url': self.mirror_url,
                'endpoint': os.environ.get('HF_ENDPOINT', ''),
                'cache_dir': os.environ.get('HF_HOME', ''),
                'download_timeout': os.environ.get('HF_HUB_DOWNLOAD_TIMEOUT', ''),
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """测试镜像连接"""
        try:
            import requests
            response = requests.get(f"{self.mirror_url}/api/models?sort=downloads&direction=-1&limit=1", timeout=10)
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'HuggingFace 镜像连接正常',
                    'timestamp': __import__('datetime').datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP状态码: {response.status_code}',
                    'timestamp': __import__('datetime').datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }

# 全局实例
hf_config = HuggingFaceConfig()