"""
架构文档生成器

为量化交易系统的各个层级生成标准化的LAYER_GUIDE.md文档。
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

from .maintainability_evaluator import MaintainabilityEvaluator
from .performance_optimizer import PerformanceAnalyzer
from .layer_analyzer import LayerAnalyzer
from .documentation_template import DocumentationTemplate
from .document_validator import DocumentValidator


class LayerCategory(Enum):
    """层级分类枚举"""
    CORE = "核心层级"
    BUSINESS = "业务层级" 
    SUPPORT = "支持层级"
    EXTENSION = "扩展层级"


@dataclass
class LayerInfo:
    """层级信息数据模型"""
    name: str
    path: str
    description: str
    category: LayerCategory
    dependencies: List[str]
    key_files: List[str]
    subdirectories: Dict[str, str]
    design_patterns: List[str]
    optimization_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['category'] = self.category.value
        return data


@dataclass 
class DocumentationContent:
    """文档内容数据模型"""
    layer_overview: str
    directory_structure: str
    core_functionality: str
    architectural_analysis: str
    optimization_suggestions: str
    usage_guide: str
    related_layers: List[str]


class DocumentationGenerator:
    """
    文档生成器主类
    
    负责协调整个文档生成流程，包括层级分析、内容生成和文档输出。
    """
    
    def __init__(self, project_root: str):
        """
        初始化文档生成器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root)
        self.layer_analyzer = LayerAnalyzer(project_root)
        self.template_engine = DocumentationTemplate()
        self.maintainability_evaluator = MaintainabilityEvaluator()
        self.performance_analyzer = PerformanceAnalyzer()
        self.document_validator = DocumentValidator()
        
        # 层级分类映射
        self.layer_categories = {
            'core': LayerCategory.CORE,
            'data': LayerCategory.CORE,
            'api': LayerCategory.CORE,
            'strategies': LayerCategory.BUSINESS,
            'user_strategies': LayerCategory.BUSINESS,
            'analysis': LayerCategory.BUSINESS,
            'services': LayerCategory.SUPPORT,
            'utils': LayerCategory.SUPPORT,
            'config': LayerCategory.SUPPORT,
            'optimization': LayerCategory.EXTENSION,
            'docs': LayerCategory.EXTENSION
        }
    
    def generate_layer_documentation(self, layer_name: str) -> str:
        """
        为指定层级生成完整的文档内容
        
        Args:
            layer_name: 层级名称
            
        Returns:
            生成的Markdown文档内容
        """
        layer_path = self.project_root / layer_name
        
        if not layer_path.exists():
            raise ValueError(f"层级目录不存在: {layer_path}")
        
        # 分析层级信息
        layer_info = self._analyze_layer(layer_name, str(layer_path))
        
        # 生成文档内容
        content = self._generate_content(layer_info)
        
        # 渲染最终文档
        generated_doc = self.template_engine.render_template(layer_info, content)
        
        # 验证文档质量
        validation_result = self.document_validator.validate_document(
            generated_doc, f"{layer_name}/LAYER_GUIDE.md"
        )
        
        # 如果验证失败，添加质量报告
        if not validation_result['is_valid']:
            quality_report = self._generate_quality_report(validation_result)
            generated_doc += f"\n\n---\n\n## 文档质量报告\n\n{quality_report}"
        
        return generated_doc
    
    def generate_all_layers_documentation(self) -> Dict[str, str]:
        """
        为所有层级生成文档
        
        Returns:
            层级名称到文档内容的映射
        """
        results = {}
        
        for layer_name in self.layer_categories.keys():
            layer_path = self.project_root / layer_name
            if layer_path.exists():
                try:
                    results[layer_name] = self.generate_layer_documentation(layer_name)
                except Exception as e:
                    self._add_error_handling_and_logging(layer_name, "文档生成", e)
                    results[layer_name] = self._generate_error_document(layer_name, str(e))
        
        return results
    
    def save_layer_documentation(self, layer_name: str, output_path: Optional[str] = None) -> str:
        """
        生成并保存层级文档到文件
        
        Args:
            layer_name: 层级名称
            output_path: 输出文件路径，默认为层级目录下的LAYER_GUIDE.md
            
        Returns:
            保存的文件路径
        """
        documentation = self.generate_layer_documentation(layer_name)
        
        if output_path is None:
            output_path = self.project_root / layer_name / "LAYER_GUIDE.md"
        else:
            output_path = Path(output_path)
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文档
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        return str(output_path)
    
    def _analyze_layer(self, layer_name: str, layer_path: str) -> LayerInfo:
        """分析层级信息"""
        # 分析依赖关系
        dependencies_analysis = self.layer_analyzer.analyze_dependencies(layer_path)
        dependencies = dependencies_analysis.get('internal_dependencies', []) if isinstance(dependencies_analysis, dict) else []
        
        # 分析设计模式
        patterns_analysis = self.layer_analyzer.identify_design_patterns(layer_path)
        design_patterns = list(patterns_analysis.get('design_patterns', {}).keys()) if isinstance(patterns_analysis, dict) else []
        
        return LayerInfo(
            name=layer_name,
            path=layer_path,
            description=self.layer_analyzer.get_layer_description(layer_path),
            category=self.layer_categories.get(layer_name, LayerCategory.SUPPORT),
            dependencies=dependencies,
            key_files=self.layer_analyzer.get_key_files(layer_path),
            subdirectories=self.layer_analyzer.analyze_subdirectories(layer_path),
            design_patterns=design_patterns,
            optimization_suggestions=self.layer_analyzer.generate_optimization_suggestions(layer_path)
        )
    
    def _generate_content(self, layer_info: LayerInfo) -> DocumentationContent:
        """生成文档内容"""
        # 集成可维护性和性能分析
        maintainability_analysis = self.maintainability_evaluator.evaluate_maintainability(layer_info.path)
        performance_analysis = self.performance_analyzer.analyze_performance_bottlenecks(layer_info.path)
        
        # 合并优化建议
        enhanced_suggestions = self._generate_enhanced_optimization_suggestions(
            layer_info.optimization_suggestions,
            maintainability_analysis,
            performance_analysis,
            layer_info.path
        )
        
        return DocumentationContent(
            layer_overview=self._generate_layer_overview(layer_info),
            directory_structure=self.layer_analyzer.generate_directory_tree(layer_info.path),
            core_functionality=self._generate_core_functionality(layer_info),
            architectural_analysis=self._generate_enhanced_architectural_analysis(
                layer_info, maintainability_analysis, performance_analysis
            ),
            optimization_suggestions=enhanced_suggestions,
            usage_guide=self._generate_usage_guide(layer_info),
            related_layers=self._get_related_layers(layer_info)
        )
    
    def _generate_layer_overview(self, layer_info: LayerInfo) -> str:
        """生成层级概述"""
        return f"""
{layer_info.description}

**层级类别**: {layer_info.category.value}
**主要职责**: {self._get_primary_responsibilities(layer_info.name)}
        """.strip()
    
    def _generate_core_functionality(self, layer_info: LayerInfo) -> str:
        """生成核心功能说明"""
        # 基础实现，后续可以通过代码分析增强
        return f"本层级包含 {len(layer_info.key_files)} 个关键文件和 {len(layer_info.subdirectories)} 个子目录。"
    
    def _generate_architectural_analysis(self, layer_info: LayerInfo) -> str:
        """生成架构分析"""
        analysis = []
        
        if layer_info.design_patterns:
            analysis.append(f"**设计模式**: {', '.join(layer_info.design_patterns)}")
        
        if layer_info.dependencies:
            analysis.append(f"**依赖关系**: {', '.join(layer_info.dependencies)}")
        
        return "\n\n".join(analysis) if analysis else "待分析"
    
    def _format_optimization_suggestions(self, suggestions: List[str]) -> str:
        """格式化优化建议"""
        if not suggestions:
            return "暂无优化建议"
        
        formatted = []
        for i, suggestion in enumerate(suggestions, 1):
            formatted.append(f"{i}. {suggestion}")
        
        return "\n".join(formatted)
    
    def _generate_usage_guide(self, layer_info: LayerInfo) -> str:
        """生成使用指南"""
        return f"请参考 {layer_info.name} 层级中的关键文件和接口进行开发。"
    
    def _get_related_layers(self, layer_info: LayerInfo) -> List[str]:
        """获取相关层级"""
        return layer_info.dependencies
    
    def _get_primary_responsibilities(self, layer_name: str) -> str:
        """获取层级主要职责"""
        responsibilities = {
            'core': '提供系统核心抽象和接口定义',
            'data': '处理数据获取、存储和管理',
            'api': '提供REST API和WebSocket接口服务',
            'strategies': '实现交易策略逻辑',
            'user_strategies': '支持用户自定义策略',
            'analysis': '提供性能分析和技术分析功能',
            'services': '提供业务服务和工具组件',
            'utils': '提供通用工具和辅助函数',
            'config': '管理系统配置和参数',
            'optimization': '提供策略优化算法和工具',
            'docs': '维护项目文档和说明'
        }
        return responsibilities.get(layer_name, '待定义')
    
    def _generate_enhanced_architectural_analysis(self, layer_info: LayerInfo, 
                                                maintainability_analysis: Dict, 
                                                performance_analysis: Dict) -> str:
        """生成增强的架构分析"""
        analysis = []
        
        # 基础架构分析
        if layer_info.design_patterns:
            analysis.append(f"**设计模式**: {', '.join(layer_info.design_patterns)}")
        
        if layer_info.dependencies:
            analysis.append(f"**依赖关系**: {', '.join(layer_info.dependencies)}")
        
        # 可维护性分析
        maintainability_summary = maintainability_analysis.get('maintainability_summary', {})
        if maintainability_summary:
            score = maintainability_summary.get('overall_maintainability_score', 0)
            total_issues = maintainability_summary.get('total_issues', 0)
            analysis.append(f"**可维护性评分**: {score}/10 (发现 {total_issues} 个问题)")
            
            # 复杂度指标
            complexity_metrics = maintainability_analysis.get('complexity_metrics', {})
            if complexity_metrics:
                avg_complexity = sum(m.cyclomatic_complexity for m in complexity_metrics.values()) / len(complexity_metrics)
                analysis.append(f"**平均圈复杂度**: {avg_complexity:.1f}")
            
            # 耦合度指标
            coupling_metrics = maintainability_analysis.get('coupling_metrics', {})
            if coupling_metrics:
                avg_coupling = sum(m.efferent_coupling for m in coupling_metrics.values()) / len(coupling_metrics)
                analysis.append(f"**平均传出耦合**: {avg_coupling:.1f}")
        
        # 性能分析
        performance_summary = performance_analysis.get('performance_summary', {})
        if performance_summary:
            total_issues = performance_summary.get('total_issues', 0)
            critical_issues = performance_summary.get('critical_issues', 0)
            analysis.append(f"**性能问题**: {total_issues} 个 (其中 {critical_issues} 个严重)")
            
            # 资源使用分析
            resource_analysis = performance_analysis.get('resource_usage_analysis', {})
            if resource_analysis:
                resource_summary = resource_analysis.get('resource_summary', {})
                if resource_summary:
                    most_intensive = resource_summary.get('most_intensive_resource')
                    if most_intensive:
                        analysis.append(f"**主要资源瓶颈**: {most_intensive}")
                    
                    overall_intensity = resource_summary.get('overall_intensity', 0)
                    analysis.append(f"**资源使用强度**: {overall_intensity:.2f}/1.0")
        
        return "\n\n".join(analysis) if analysis else "待分析"
    
    def _generate_enhanced_optimization_suggestions(self, base_suggestions: List[str],
                                                  maintainability_analysis: Dict,
                                                  performance_analysis: Dict,
                                                  layer_path: str = '') -> str:
        """生成增强的优化建议"""
        all_suggestions = []
        
        # 基础优化建议
        all_suggestions.extend(base_suggestions)
        
        # 可维护性优化建议
        maintainability_suggestions = self.maintainability_evaluator.generate_maintainability_suggestions(layer_path)
        if maintainability_suggestions:
            all_suggestions.append("### 可维护性优化")
            all_suggestions.extend([f"- {suggestion}" for suggestion in maintainability_suggestions[:5]])
        
        # 性能优化建议
        performance_suggestions = self.performance_analyzer.generate_performance_optimization_suggestions(layer_path)
        if performance_suggestions:
            all_suggestions.append("### 性能优化")
            all_suggestions.extend([f"- {suggestion}" for suggestion in performance_suggestions[:5]])
        
        # 格式化输出
        if not all_suggestions:
            return "暂无优化建议"
        
        formatted = []
        for i, suggestion in enumerate(all_suggestions, 1):
            if suggestion.startswith('###'):
                formatted.append(f"\n{suggestion}")
            elif suggestion.startswith('- '):
                formatted.append(suggestion)
            else:
                formatted.append(f"{i}. {suggestion}")
        
        return "\n".join(formatted)
    
    def _format_maintainability_metrics(self, complexity_metrics: Dict, coupling_metrics: Dict) -> str:
        """格式化可维护性指标输出"""
        if not complexity_metrics and not coupling_metrics:
            return "无可维护性指标数据"
        
        output = []
        
        if complexity_metrics:
            output.append("#### 复杂度指标")
            for file_path, metrics in list(complexity_metrics.items())[:5]:  # 显示前5个文件
                output.append(f"- **{file_path}**:")
                output.append(f"  - 圈复杂度: {metrics.cyclomatic_complexity}")
                output.append(f"  - 认知复杂度: {metrics.cognitive_complexity}")
                output.append(f"  - 可维护性指数: {metrics.maintainability_index:.1f}/100")
        
        if coupling_metrics:
            output.append("\n#### 耦合度指标")
            for file_path, metrics in list(coupling_metrics.items())[:5]:  # 显示前5个文件
                output.append(f"- **{file_path}**:")
                output.append(f"  - 传出耦合: {metrics.efferent_coupling}")
                output.append(f"  - 不稳定性: {metrics.instability:.2f}")
                output.append(f"  - 抽象性: {metrics.abstractness:.2f}")
        
        return "\n".join(output)
    
    def _format_performance_analysis(self, resource_patterns: Dict) -> str:
        """格式化性能分析结果"""
        if not resource_patterns:
            return "无性能分析数据"
        
        output = []
        
        # 内存使用模式
        memory_patterns = resource_patterns.get('memory_usage_patterns', [])
        if memory_patterns:
            output.append("#### 内存使用模式")
            for pattern in memory_patterns[:3]:
                output.append(f"- {pattern['pattern_type']}: 频率 {pattern['frequency']}, 强度 {pattern['usage_intensity']:.2f}")
        
        # CPU使用模式
        cpu_patterns = resource_patterns.get('cpu_usage_patterns', [])
        if cpu_patterns:
            output.append("\n#### CPU使用模式")
            for pattern in cpu_patterns[:3]:
                output.append(f"- {pattern['pattern_type']}: 频率 {pattern['frequency']}, 强度 {pattern['usage_intensity']:.2f}")
        
        # IO操作模式
        io_patterns = resource_patterns.get('io_operation_patterns', [])
        if io_patterns:
            output.append("\n#### IO操作模式")
            for pattern in io_patterns[:3]:
                output.append(f"- {pattern['pattern_type']}: 频率 {pattern['frequency']}, 强度 {pattern['usage_intensity']:.2f}")
        
        return "\n".join(output)
    
    def _generate_quality_report(self, validation_result: Dict[str, Any]) -> str:
        """生成文档质量报告"""
        quality_metrics = validation_result['quality_metrics']
        validation_summary = validation_result['validation_summary']
        
        report = []
        
        # 质量评分
        report.append("### 质量评分")
        report.append(f"- **总体质量**: {validation_summary['overall_quality']} ({quality_metrics['overall_score']:.2f})")
        report.append(f"- **完整性**: {validation_summary['completeness_quality']} ({quality_metrics['completeness_score']:.2f})")
        report.append(f"- **格式规范**: {validation_summary['format_quality']} ({quality_metrics['format_score']:.2f})")
        report.append(f"- **内容质量**: {validation_summary['content_quality']} ({quality_metrics['content_score']:.2f})")
        
        # 问题统计
        report.append("\n### 问题统计")
        report.append(f"- **总问题数**: {quality_metrics['total_issues']}")
        report.append(f"- **严重问题**: {quality_metrics['critical_issues']}")
        
        # 改进建议
        recommendations = validation_result.get('recommendations', [])
        if recommendations:
            report.append("\n### 改进建议")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. {rec}")
        
        return "\n".join(report)
    
    def validate_generated_document(self, document_content: str, document_path: str = None) -> Dict[str, Any]:
        """
        验证生成的文档质量
        
        Args:
            document_content: 文档内容
            document_path: 文档路径
            
        Returns:
            验证结果字典
        """
        try:
            return self.document_validator.validate_document(document_content, document_path)
        except Exception as e:
            return {
                'validation_issues': [],
                'quality_metrics': {
                    'completeness_score': 0.0,
                    'format_score': 0.0,
                    'content_score': 0.0,
                    'overall_score': 0.0,
                    'total_issues': 1,
                    'critical_issues': 1
                },
                'validation_summary': {
                    'overall_quality': '验证失败',
                    'validation_passed': False
                },
                'recommendations': [f"文档验证过程中出现错误: {str(e)}"],
                'is_valid': False,
                'error': str(e)
            }
    
    def _add_error_handling_and_logging(self, layer_name: str, operation: str, error: Exception) -> None:
        """添加错误处理和日志记录"""
        error_message = f"在 {layer_name} 层级执行 {operation} 操作时发生错误: {str(error)}"
        
        # 这里可以添加日志记录逻辑
        print(f"[ERROR] {error_message}")
        
        # 可以添加错误统计和报告
        if not hasattr(self, '_error_log'):
            self._error_log = []
        
        self._error_log.append({
            'timestamp': datetime.now().isoformat(),
            'layer': layer_name,
            'operation': operation,
            'error': str(error),
            'error_type': type(error).__name__
        })
    
    def get_error_log(self) -> List[Dict[str, Any]]:
        """获取错误日志"""
        return getattr(self, '_error_log', [])
    
    def _generate_error_document(self, layer_name: str, error_message: str) -> str:
        """生成错误文档"""
        return f"""# {layer_name} 层级架构文档

## 错误信息

生成文档时发生错误: {error_message}

请检查层级目录结构和文件权限。

---

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""