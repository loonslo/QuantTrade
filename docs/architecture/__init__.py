"""
架构文档生成器包

为量化交易系统的各个层级生成标准化的架构文档。

主要组件:
- DocumentationGenerator: 文档生成器主类
- LayerAnalyzer: 层级分析器
- DocumentationTemplate: 文档模板引擎
- LayerInfo: 层级信息数据模型
- DocumentationContent: 文档内容数据模型
"""

from .documentation_generator import (
    DocumentationGenerator,
    LayerInfo,
    DocumentationContent,
    LayerCategory
)
from .layer_analyzer import LayerAnalyzer
from .documentation_template import DocumentationTemplate

__all__ = [
    'DocumentationGenerator',
    'LayerAnalyzer', 
    'DocumentationTemplate',
    'LayerInfo',
    'DocumentationContent',
    'LayerCategory'
]

__version__ = '1.0.0'