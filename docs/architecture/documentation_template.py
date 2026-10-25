"""
文档模板引擎

负责渲染标准化的LAYER_GUIDE.md文档模板。
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .documentation_generator import LayerInfo, DocumentationContent


class DocumentationTemplate:
    """
    文档模板引擎
    
    负责将层级信息和内容数据渲染为标准化的Markdown文档。
    """
    
    TEMPLATE_SECTIONS = [
        "layer_overview",
        "directory_structure", 
        "core_functionality",
        "architectural_analysis",
        "optimization_suggestions",
        "usage_guide",
        "related_layers"
    ]
    
    def __init__(self, template_path: Optional[str] = None):
        """
        初始化模板引擎
        
        Args:
            template_path: 自定义模板文件路径，默认使用内置模板
        """
        self.template_path = template_path
        self._load_template()
    
    def render_template(self, layer_info: 'LayerInfo', content: 'DocumentationContent') -> str:
        """
        渲染文档模板
        
        Args:
            layer_info: 层级信息
            content: 文档内容
            
        Returns:
            渲染后的Markdown文档
        """
        # 准备模板变量
        template_vars = self._prepare_template_variables(layer_info, content)
        
        # 渲染模板
        rendered_content = self._render_with_variables(self.template_content, template_vars)
        
        return rendered_content
    
    def _load_template(self):
        """加载模板内容"""
        if self.template_path and Path(self.template_path).exists():
            # 加载自定义模板
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.template_content = f.read()
        else:
            # 使用内置模板
            self.template_content = self._get_default_template()
    
    def _get_default_template(self) -> str:
        """获取默认模板内容"""
        return """# {layer_name} 层级架构文档

## 1. 层级概述

{layer_overview}

## 2. 目录结构

```
{directory_structure}
```

### 关键文件说明

{key_files_description}

### 子目录说明

{subdirectories_description}

## 3. 核心功能

{core_functionality}

### 主要模块

{main_modules}

### 关键接口

{key_interfaces}

## 4. 架构分析

### 设计模式

{design_patterns}

### 依赖关系

{dependencies}

### 数据流

{data_flow}

### 层级交互

{layer_interactions}

## 5. 代码优化建议

### 性能优化

{performance_optimizations}

### 可维护性改进

{maintainability_improvements}

### 最佳实践

{best_practices}

## 6. 使用指南

### 开发者指南

{developer_guide}

### 扩展指南

{extension_guide}

### 常见用例

{common_use_cases}

## 7. 相关层级

{related_layers}

---

*本文档由架构文档生成器自动生成，最后更新时间: {last_updated}*"""
    
    def _prepare_template_variables(self, layer_info: 'LayerInfo', content: 'DocumentationContent') -> Dict[str, str]:
        """准备模板变量"""
        variables = {
            # 基本信息
            'layer_name': layer_info.name.title(),
            'layer_overview': content.layer_overview,
            'directory_structure': content.directory_structure,
            'core_functionality': content.core_functionality,
            'architectural_analysis': content.architectural_analysis,
            'optimization_suggestions': content.optimization_suggestions,
            'usage_guide': content.usage_guide,
            'related_layers': self._format_related_layers(content.related_layers),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # 详细信息
            'key_files_description': self._format_key_files(layer_info.key_files),
            'subdirectories_description': self._format_subdirectories(layer_info.subdirectories),
            'main_modules': self._format_main_modules(layer_info.key_files),
            'key_interfaces': self._format_key_interfaces(layer_info),
            'design_patterns': self._format_design_patterns(layer_info.design_patterns),
            'dependencies': self._format_dependencies(layer_info.dependencies),
            'data_flow': self._generate_data_flow_description(layer_info),
            'layer_interactions': self._generate_layer_interactions(layer_info),
            'performance_optimizations': self._extract_performance_suggestions(layer_info.optimization_suggestions),
            'maintainability_improvements': self._extract_maintainability_suggestions(layer_info.optimization_suggestions),
            'best_practices': self._generate_best_practices(layer_info),
            'developer_guide': self._generate_developer_guide(layer_info),
            'extension_guide': self._generate_extension_guide(layer_info),
            'common_use_cases': self._generate_common_use_cases(layer_info)
        }
        
        return variables
    
    def _render_with_variables(self, template: str, variables: Dict[str, str]) -> str:
        """使用变量渲染模板"""
        rendered = template
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            rendered = rendered.replace(placeholder, str(value))
        
        # 清理未替换的占位符
        rendered = re.sub(r'\{[^}]+\}', '待完善', rendered)
        
        return rendered
    
    def _format_key_files(self, key_files: list) -> str:
        """格式化关键文件说明"""
        if not key_files:
            return "暂无关键文件"
        
        descriptions = []
        for file_path in key_files[:10]:  # 限制显示数量
            file_name = Path(file_path).name
            description = self._get_file_description(file_name)
            descriptions.append(f"- `{file_path}`: {description}")
        
        return "\n".join(descriptions)
    
    def _format_subdirectories(self, subdirectories: Dict[str, str]) -> str:
        """格式化子目录说明"""
        if not subdirectories:
            return "暂无子目录"
        
        descriptions = []
        for dir_name, description in subdirectories.items():
            descriptions.append(f"- `{dir_name}/`: {description}")
        
        return "\n".join(descriptions)
    
    def _format_main_modules(self, key_files: list) -> str:
        """格式化主要模块"""
        if not key_files:
            return "暂无主要模块"
        
        modules = []
        for file_path in key_files[:5]:  # 只显示前5个
            module_name = Path(file_path).stem
            if module_name != '__init__':
                modules.append(f"- **{module_name}**: {self._get_module_description(module_name)}")
        
        return "\n".join(modules) if modules else "暂无主要模块"
    
    def _format_key_interfaces(self, layer_info: 'LayerInfo') -> str:
        """格式化关键接口"""
        # 基于文件名推断接口
        interfaces = []
        for file_path in layer_info.key_files:
            file_name = Path(file_path).stem
            if any(keyword in file_name.lower() for keyword in ['interface', 'base', 'abstract']):
                interfaces.append(f"- **{file_name}**: 定义{layer_info.name}层级的核心接口")
        
        return "\n".join(interfaces) if interfaces else "暂无明确的接口定义"
    
    def _format_design_patterns(self, patterns: list) -> str:
        """格式化设计模式"""
        if not patterns:
            return "暂未识别到明确的设计模式"
        
        # 过滤掉非设计模式的项目
        valid_patterns = []
        for pattern in patterns:
            if isinstance(pattern, str) and not pattern.startswith(('design_', 'architectural_', 'file_', 'pattern_')):
                valid_patterns.append(pattern)
        
        if not valid_patterns:
            return "暂未识别到明确的设计模式"
        
        formatted = []
        for pattern in valid_patterns:
            formatted.append(f"- **{pattern}**: 用于{self._get_pattern_description(pattern)}")
        
        return "\n".join(formatted)
    
    def _format_dependencies(self, dependencies: list) -> str:
        """格式化依赖关系"""
        if not dependencies:
            return "无直接层级依赖"
        
        # 过滤掉非层级名称的依赖
        valid_dependencies = []
        layer_names = ['core', 'data', 'api', 'strategies', 'user_strategies', 'analysis', 
                      'services', 'utils', 'config', 'optimization', 'docs']
        
        for dep in dependencies:
            if isinstance(dep, str) and dep in layer_names:
                valid_dependencies.append(dep)
        
        if not valid_dependencies:
            return "无直接层级依赖"
        
        formatted = []
        for dep in valid_dependencies:
            formatted.append(f"- **{dep}**: {self._get_dependency_description(dep)}")
        
        return "\n".join(formatted)
    
    def _format_related_layers(self, related_layers: list) -> str:
        """格式化相关层级"""
        if not related_layers:
            return "暂无直接相关层级"
        
        # 过滤掉非层级名称的项目
        valid_layers = []
        layer_names = ['core', 'data', 'api', 'strategies', 'user_strategies', 'analysis', 
                      'services', 'utils', 'config', 'optimization', 'docs']
        
        for layer in related_layers:
            if isinstance(layer, str) and layer in layer_names:
                valid_layers.append(layer)
        
        if not valid_layers:
            return "暂无直接相关层级"
        
        formatted = []
        for layer in valid_layers:
            formatted.append(f"- **{layer}**: {self._get_layer_relationship_description(layer)}")
        
        return "\n".join(formatted)
    
    def _generate_data_flow_description(self, layer_info: 'LayerInfo') -> str:
        """生成数据流描述"""
        layer_name = layer_info.name
        
        data_flows = {
            'data': '数据从外部API获取 → 数据验证 → 数据存储 → 提供给其他层级',
            'api': '接收HTTP请求 → 参数验证 → 调用业务层 → 返回响应',
            'core': '定义数据结构 → 提供抽象接口 → 被其他层级实现',
            'strategies': '接收市场数据 → 策略计算 → 生成交易信号 → 输出决策',
            'analysis': '获取历史数据 → 技术分析计算 → 生成分析报告 → 可视化展示'
        }
        
        return data_flows.get(layer_name, f'{layer_name}层级的数据流向待分析')
    
    def _generate_layer_interactions(self, layer_info: 'LayerInfo') -> str:
        """生成层级交互描述"""
        interactions = []
        
        for dep in layer_info.dependencies:
            interaction = f"- 与 **{dep}** 层级: {self._get_interaction_description(layer_info.name, dep)}"
            interactions.append(interaction)
        
        return "\n".join(interactions) if interactions else "暂无明确的层级交互"
    
    def _extract_performance_suggestions(self, suggestions: list) -> str:
        """提取性能优化建议"""
        performance_keywords = ['性能', '优化', '缓存', '并发', '异步', '内存', '速度']
        
        performance_suggestions = []
        for suggestion in suggestions:
            if any(keyword in suggestion for keyword in performance_keywords):
                performance_suggestions.append(f"- {suggestion}")
        
        if not performance_suggestions:
            performance_suggestions = ["- 考虑添加缓存机制提高数据访问速度", "- 优化数据库查询性能"]
        
        return "\n".join(performance_suggestions)
    
    def _extract_maintainability_suggestions(self, suggestions: list) -> str:
        """提取可维护性建议"""
        maintainability_keywords = ['维护', '重构', '拆分', '文档', '测试', '接口']
        
        maintainability_suggestions = []
        for suggestion in suggestions:
            if any(keyword in suggestion for keyword in maintainability_keywords):
                maintainability_suggestions.append(f"- {suggestion}")
        
        if not maintainability_suggestions:
            maintainability_suggestions = ["- 添加单元测试提高代码质量", "- 完善代码文档和注释"]
        
        return "\n".join(maintainability_suggestions)
    
    def _generate_best_practices(self, layer_info: 'LayerInfo') -> str:
        """生成最佳实践建议"""
        layer_name = layer_info.name
        
        best_practices = {
            'data': [
                "使用数据验证确保数据质量",
                "实现数据缓存机制提高访问效率",
                "采用连接池管理数据库连接"
            ],
            'api': [
                "实现统一的错误处理机制",
                "使用中间件处理跨切面关注点",
                "添加API版本控制支持"
            ],
            'core': [
                "定义清晰的接口契约",
                "使用抽象基类确保一致性",
                "避免循环依赖"
            ]
        }
        
        practices = best_practices.get(layer_name, [
            "遵循单一职责原则",
            "保持代码简洁和可读性",
            "添加适当的错误处理"
        ])
        
        return "\n".join([f"- {practice}" for practice in practices])
    
    def _generate_developer_guide(self, layer_info: 'LayerInfo') -> str:
        """生成开发者指南"""
        return f"""
开发 {layer_info.name} 层级时，请遵循以下指导原则：

1. **代码组织**: 将相关功能组织在同一模块中
2. **接口设计**: 保持接口简洁和一致性
3. **错误处理**: 实现适当的异常处理机制
4. **文档编写**: 为公共接口添加详细文档
5. **测试覆盖**: 编写单元测试确保代码质量
        """.strip()
    
    def _generate_extension_guide(self, layer_info: 'LayerInfo') -> str:
        """生成扩展指南"""
        return f"""
扩展 {layer_info.name} 层级功能时：

1. **继承现有接口**: 遵循已定义的抽象接口
2. **配置管理**: 通过配置文件管理新功能参数
3. **向后兼容**: 确保新功能不破坏现有API
4. **性能考虑**: 评估新功能对系统性能的影响
        """.strip()
    
    def _generate_common_use_cases(self, layer_info: 'LayerInfo') -> str:
        """生成常见用例"""
        layer_name = layer_info.name
        
        use_cases = {
            'data': [
                "获取实时市场数据",
                "存储历史交易数据",
                "数据清洗和验证"
            ],
            'api': [
                "提供REST API接口",
                "WebSocket实时数据推送",
                "用户认证和授权"
            ],
            'strategies': [
                "实现技术分析策略",
                "风险管理和仓位控制",
                "策略回测和优化"
            ]
        }
        
        cases = use_cases.get(layer_name, [f"{layer_name}层级的常见使用场景"])
        
        return "\n".join([f"- {case}" for case in cases])
    
    # 辅助方法
    def _get_file_description(self, file_name: str) -> str:
        """获取文件描述"""
        descriptions = {
            '__init__.py': '模块初始化文件',
            'main.py': '主程序入口',
            'app.py': '应用程序主文件',
            'config.py': '配置管理',
            'settings.py': '设置参数',
            'models.py': '数据模型定义',
            'views.py': '视图层实现',
            'utils.py': '工具函数',
            'exceptions.py': '异常定义',
            'constants.py': '常量定义'
        }
        
        return descriptions.get(file_name, '功能模块文件')
    
    def _get_module_description(self, module_name: str) -> str:
        """获取模块描述"""
        if 'manager' in module_name.lower():
            return '管理器模块，负责资源管理和协调'
        elif 'service' in module_name.lower():
            return '服务模块，提供业务逻辑实现'
        elif 'interface' in module_name.lower():
            return '接口定义模块'
        elif 'base' in module_name.lower():
            return '基础类定义模块'
        else:
            return f'{module_name}功能模块'
    
    def _get_pattern_description(self, pattern: str) -> str:
        """获取设计模式描述"""
        descriptions = {
            '单例模式': '确保类只有一个实例',
            '工厂模式': '创建对象的统一接口',
            '策略模式': '算法的封装和切换',
            '观察者模式': '对象间的松耦合通信',
            '抽象基类模式': '定义统一的接口规范'
        }
        
        return descriptions.get(pattern, '特定的设计实现')
    
    def _get_dependency_description(self, dependency: str) -> str:
        """获取依赖描述"""
        descriptions = {
            'core': '使用核心接口和抽象',
            'data': '获取和存储数据',
            'utils': '使用通用工具函数',
            'config': '读取配置参数',
            'services': '调用业务服务'
        }
        
        return descriptions.get(dependency, f'依赖{dependency}层级的功能')
    
    def _get_layer_relationship_description(self, layer: str) -> str:
        """获取层级关系描述"""
        return f'与{layer}层级存在功能依赖或协作关系'
    
    def _get_interaction_description(self, source_layer: str, target_layer: str) -> str:
        """获取交互描述"""
        interactions = {
            ('api', 'data'): '通过API接口访问数据服务',
            ('strategies', 'data'): '获取市场数据进行策略计算',
            ('analysis', 'data'): '获取历史数据进行分析',
            ('services', 'core'): '实现核心接口定义的服务'
        }
        
        return interactions.get((source_layer, target_layer), f'调用{target_layer}层级的功能')