import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging
import requests
from datasets import load_dataset, Dataset, DatasetDict

class DatasetManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.datasets_dir = "/home/a/ServiceEndFiles/Datasets"
        self.popular_datasets = {
            'wikitext': {
                'name': 'WikiText',
                'description': '维基百科文本数据集',
                'type': 'text_generation',
                'hf_path': 'wikitext',
                'size': 'large'
            },
            'c4': {
                'name': 'C4',
                'description': 'Colossal Clean Crawled Corpus',
                'type': 'text_generation',
                'hf_path': 'c4',
                'size': 'large'
            },
            'pile': {
                'name': 'The Pile',
                'description': '多源文本数据集',
                'type': 'text_generation',
                'hf_path': 'EleutherAI/pile',
                'size': 'large'
            },
            'openwebtext': {
                'name': 'OpenWebText',
                'description': '开源网页文本',
                'type': 'text_generation',
                'hf_path': 'openwebtext',
                'size': 'medium'
            },
            'bookcorpus': {
                'name': 'BookCorpus',
                'description': '书籍语料库',
                'type': 'text_generation',
                'hf_path': 'bookcorpus',
                'size': 'medium'
            },
            'glue': {
                'name': 'GLUE',
                'description': '通用语言理解评估基准',
                'type': 'classification',
                'hf_path': 'glue',
                'size': 'small'
            },
            'squad': {
                'name': 'SQuAD',
                'description': '斯坦福问答数据集',
                'type': 'qa',
                'hf_path': 'squad',
                'size': 'medium'
            }
        }
        
        # 确保数据集目录存在
        os.makedirs(self.datasets_dir, exist_ok=True)
        
    def get_available_datasets(self) -> Dict[str, Any]:
        """获取可用数据集列表"""
        try:
            datasets = []
            for dataset_key, dataset_info in self.popular_datasets.items():
                dataset_info_copy = dataset_info.copy()
                dataset_info_copy['key'] = dataset_key
                datasets.append(dataset_info_copy)
            
            return {
                'success': True,
                'data': {
                    'datasets': datasets,
                    'total': len(datasets),
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"获取数据集列表失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def validate_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """验证数据集"""
        try:
            # 检查是否为内置数据集
            if dataset_name in self.popular_datasets:
                return {
                    'success': True,
                    'data': {
                        'dataset_key': dataset_name,
                        'dataset_info': self.popular_datasets[dataset_name],
                        'is_valid': True,
                        'message': f'数据集 {dataset_name} 验证通过',
                        'timestamp': datetime.now().isoformat()
                    }
                }
            
            # 检查是否为本地数据集
            local_dataset_path = Path(self.datasets_dir) / dataset_name
            if local_dataset_path.exists():
                return {
                    'success': True,
                    'data': {
                        'dataset_key': dataset_name,
                        'dataset_info': {
                            'name': dataset_name,
                            'description': '本地数据集',
                            'type': 'text_generation',
                            'path': str(local_dataset_path),
                            'size': 'unknown'
                        },
                        'is_valid': True,
                        'is_local': True,
                        'message': f'本地数据集 {dataset_name} 验证通过',
                        'timestamp': datetime.now().isoformat()
                    }
                }
            
            return {
                'success': False,
                'error': f'数据集 {dataset_name} 未找到',
                'available_datasets': list(self.popular_datasets.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"验证数据集失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def download_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """下载数据集"""
        try:
            if dataset_name not in self.popular_datasets:
                return {
                    'success': False,
                    'error': f'不支持的数据集: {dataset_name}',
                    'available_datasets': list(self.popular_datasets.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            
            dataset_info = self.popular_datasets[dataset_name]
            
            # 创建数据集下载任务
            return {
                'success': True,
                'data': {
                    'dataset_key': dataset_name,
                    'dataset_info': dataset_info,
                    'download_url': f"https://hf-mirror.com/datasets/{dataset_info['hf_path']}",
                    'message': f'开始下载数据集 {dataset_name}',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"下载数据集失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def create_custom_dataset(self, dataset_name: str, data_type: str = 'text_generation') -> Dict[str, Any]:
        """创建自定义数据集"""
        try:
            dataset_path = Path(self.datasets_dir) / dataset_name
            
            if dataset_path.exists():
                return {
                    'success': False,
                    'error': f'数据集 {dataset_name} 已存在',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 创建数据集目录和基本信息
            dataset_path.mkdir(parents=True, exist_ok=True)
            
            dataset_config = {
                'name': dataset_name,
                'type': data_type,
                'created_at': datetime.now().isoformat(),
                'path': str(dataset_path),
                'description': f'用户创建的数据集: {dataset_name}'
            }
            
            # 保存数据集配置
            with open(dataset_path / 'dataset_config.json', 'w', encoding='utf-8') as f:
                json.dump(dataset_config, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'data': {
                    'dataset': dataset_config,
                    'message': f'自定义数据集 {dataset_name} 创建成功',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"创建自定义数据集失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_dataset_samples(self, dataset_name: str, max_samples: int = 5) -> Dict[str, Any]:
        """获取数据集样本"""
        try:
            # 对于内置数据集，返回示例
            if dataset_name in self.popular_datasets:
                dataset_info = self.popular_datasets[dataset_name]
                
                # 返回示例数据格式
                sample_data = {
                    'text_generation': [
                        "This is a sample text for language model training.",
                        "Here is another example of text data.",
                        "Machine learning models require large amounts of text.",
                        "Natural language processing is a fascinating field.",
                        "Large language models have shown impressive capabilities."
                    ],
                    'classification': [
                        {"text": "This is positive sentiment.", "label": 1},
                        {"text": "This is negative sentiment.", "label": 0},
                        {"text": "This is neutral sentiment.", "label": 2}
                    ],
                    'qa': [
                        {
                            "question": "What is the capital of France?",
                            "answer": "Paris",
                            "context": "France is a country in Europe. Its capital is Paris."
                        }
                    ]
                }
                
                sample_type = dataset_info['type']
                samples = sample_data.get(sample_type, sample_data['text_generation'])
                
                return {
                    'success': True,
                    'data': {
                        'dataset_name': dataset_name,
                        'dataset_type': sample_type,
                        'samples': samples[:max_samples],
                        'total_samples_available': len(samples),
                        'message': f'返回数据集 {dataset_name} 的样本',
                        'timestamp': datetime.now().isoformat()
                    }
                }
            
            return {
                'success': False,
                'error': f'数据集 {dataset_name} 不支持样本获取',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取数据集样本失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
