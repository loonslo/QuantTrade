"""
性能优化分析器

分析代码性能瓶颈，生成具体的性能优化建议。
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class PerformanceIssueType(Enum):
    """性能问题类型枚举"""
    MEMORY_LEAK = "内存泄漏"
    CPU_INTENSIVE = "CPU密集型操作"
    IO_BLOCKING = "IO阻塞"
    INEFFICIENT_ALGORITHM = "低效算法"
    RESOURCE_WASTE = "资源浪费"
    SYNCHRONIZATION_ISSUE = "同步问题"
    DATABASE_QUERY = "数据库查询问题"
    NETWORK_LATENCY = "网络延迟"


@dataclass
class PerformanceIssue:
    """性能问题数据模型"""
    issue_type: PerformanceIssueType
    severity: int  # 1-10严重程度
    file_path: str
    line_number: int
    description: str
    suggestion: str
    code_snippet: str
    estimated_impact: str  # 预估性能影响


@dataclass
class ResourceUsagePattern:
    """资源使用模式"""
    pattern_type: str
    frequency: int
    resource_type: str  # memory, cpu, io, network
    usage_intensity: float  # 0-1使用强度
    optimization_potential: float  # 0-1优化潜力


class PerformanceAnalyzer:
    """
    性能优化分析器
    
    识别潜在的性能瓶颈，分析资源使用模式，生成具体的性能优化建议。
    """
    
    def __init__(self):
        """初始化性能分析器"""
        self.performance_patterns = self._initialize_performance_patterns()
        self.resource_patterns = self._initialize_resource_patterns()
        
    def analyze_performance_bottlenecks(self, layer_path: str) -> Dict[str, Any]:
        """
        分析层级中的性能瓶颈
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            包含性能瓶颈分析结果的字典
        """
        layer_path = Path(layer_path)
        python_files = self._get_python_files(layer_path)
        
        performance_issues = []
        file_analysis = {}
        
        for file_path in python_files:
            try:
                file_issues = self._analyze_file_performance(file_path)
                if file_issues:
                    relative_path = str(file_path.relative_to(layer_path))
                    file_analysis[relative_path] = file_issues
                    performance_issues.extend(file_issues)
            except Exception as e:
                print(f"分析文件 {file_path} 性能时出错: {e}")
        
        # 按严重程度排序
        performance_issues.sort(key=lambda x: x.severity, reverse=True)
        
        # 生成性能摘要
        performance_summary = self._generate_performance_summary(performance_issues)
        
        return {
            'performance_issues': [self._issue_to_dict(issue) for issue in performance_issues],
            'file_analysis': file_analysis,
            'performance_summary': performance_summary,
            'optimization_priorities': self._get_optimization_priorities(performance_issues),
            'resource_usage_analysis': self.analyze_resource_usage_patterns(layer_path)
        }
    
    def analyze_resource_usage_patterns(self, layer_path: str) -> Dict[str, Any]:
        """
        分析资源使用模式
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            资源使用模式分析结果
        """
        layer_path = Path(layer_path)
        python_files = self._get_python_files(layer_path)
        
        resource_patterns = []
        memory_usage = []
        cpu_usage = []
        io_operations = []
        network_operations = []
        
        for file_path in python_files:
            try:
                patterns = self._analyze_file_resource_patterns(file_path)
                resource_patterns.extend(patterns)
                
                # 分类资源使用
                for pattern in patterns:
                    if pattern.resource_type == 'memory':
                        memory_usage.append(pattern)
                    elif pattern.resource_type == 'cpu':
                        cpu_usage.append(pattern)
                    elif pattern.resource_type == 'io':
                        io_operations.append(pattern)
                    elif pattern.resource_type == 'network':
                        network_operations.append(pattern)
                        
            except Exception as e:
                print(f"分析文件 {file_path} 资源使用时出错: {e}")
        
        return {
            'memory_usage_patterns': [self._pattern_to_dict(p) for p in memory_usage],
            'cpu_usage_patterns': [self._pattern_to_dict(p) for p in cpu_usage],
            'io_operation_patterns': [self._pattern_to_dict(p) for p in io_operations],
            'network_operation_patterns': [self._pattern_to_dict(p) for p in network_operations],
            'resource_summary': self._generate_resource_summary(resource_patterns),
            'optimization_recommendations': self._generate_resource_optimization_recommendations(resource_patterns)
        }
    
    def generate_performance_optimization_suggestions(self, layer_path: str) -> List[str]:
        """
        生成具体的性能优化建议
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            性能优化建议列表
        """
        performance_analysis = self.analyze_performance_bottlenecks(layer_path)
        resource_analysis = self.analyze_resource_usage_patterns(layer_path)
        
        suggestions = []
        
        # 基于性能问题的建议
        high_priority_issues = [
            issue for issue in performance_analysis['performance_issues']
            if issue['severity'] >= 7
        ]
        
        for issue in high_priority_issues[:5]:  # 限制最重要的5个问题
            suggestions.append(f"修复{issue['issue_type']}: {issue['suggestion']}")
        
        # 基于资源使用的建议
        resource_suggestions = resource_analysis.get('optimization_recommendations', [])
        suggestions.extend(resource_suggestions[:3])  # 添加前3个资源优化建议
        
        # 通用性能优化建议
        general_suggestions = self._generate_general_performance_suggestions(layer_path)
        suggestions.extend(general_suggestions)
        
        return suggestions[:10]  # 限制总建议数量
    
    def _analyze_file_performance(self, file_path: Path) -> List[PerformanceIssue]:
        """分析单个文件的性能问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # 检查各种性能问题
            issues.extend(self._check_memory_issues(tree, lines, str(file_path)))
            issues.extend(self._check_cpu_intensive_operations(tree, lines, str(file_path)))
            issues.extend(self._check_io_blocking_operations(tree, lines, str(file_path)))
            issues.extend(self._check_inefficient_algorithms(tree, lines, str(file_path)))
            issues.extend(self._check_resource_waste(tree, lines, str(file_path)))
            
        except Exception as e:
            print(f"解析文件 {file_path} 时出错: {e}")
        
        return issues
    
    def _check_memory_issues(self, tree: ast.AST, lines: List[str], file_path: str) -> List[PerformanceIssue]:
        """检查内存相关问题"""
        issues = []
        
        for node in ast.walk(tree):
            # 检查大列表创建
            if isinstance(node, ast.ListComp):
                if self._is_potentially_large_list_comprehension(node):
                    issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.MEMORY_LEAK,
                        severity=6,
                        file_path=file_path,
                        line_number=node.lineno,
                        description="大型列表推导式可能消耗大量内存",
                        suggestion="考虑使用生成器表达式或分批处理",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        estimated_impact="可能减少50-80%内存使用"
                    ))
            
            # 检查循环中的对象创建
            if isinstance(node, (ast.For, ast.While)):
                object_creations = self._find_object_creations_in_loop(node)
                if object_creations > 3:
                    issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.MEMORY_LEAK,
                        severity=7,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"循环中创建了{object_creations}个对象，可能导致内存压力",
                        suggestion="将对象创建移到循环外部或使用对象池",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        estimated_impact="可能减少30-60%内存分配"
                    ))
        
        return issues
    
    def _check_cpu_intensive_operations(self, tree: ast.AST, lines: List[str], file_path: str) -> List[PerformanceIssue]:
        """检查CPU密集型操作"""
        issues = []
        
        for node in ast.walk(tree):
            # 检查嵌套循环
            if isinstance(node, (ast.For, ast.While)):
                nesting_depth = self._calculate_loop_nesting_depth(node)
                if nesting_depth >= 3:
                    issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.CPU_INTENSIVE,
                        severity=8,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"嵌套循环深度为{nesting_depth}，可能导致性能问题",
                        suggestion="考虑算法优化或使用向量化操作",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        estimated_impact="可能提升10-100倍性能"
                    ))
            
            # 检查递归函数
            if isinstance(node, ast.FunctionDef):
                if self._is_recursive_function(node):
                    issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.CPU_INTENSIVE,
                        severity=6,
                        file_path=file_path,
                        line_number=node.lineno,
                        description="递归函数可能导致栈溢出或性能问题",
                        suggestion="考虑使用迭代实现或添加记忆化",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        estimated_impact="可能避免栈溢出并提升性能"
                    ))
        
        return issues
    
    def _check_io_blocking_operations(self, tree: ast.AST, lines: List[str], file_path: str) -> List[PerformanceIssue]:
        """检查IO阻塞操作"""
        issues = []
        
        for node in ast.walk(tree):
            # 检查文件操作
            if isinstance(node, ast.Call):
                if self._is_blocking_io_operation(node):
                    issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.IO_BLOCKING,
                        severity=7,
                        file_path=file_path,
                        line_number=node.lineno,
                        description="同步IO操作可能阻塞程序执行",
                        suggestion="考虑使用异步IO或线程池",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        estimated_impact="可能提升并发性能50-200%"
                    ))
        
        return issues
    
    def _check_inefficient_algorithms(self, tree: ast.AST, lines: List[str], file_path: str) -> List[PerformanceIssue]:
        """检查低效算法"""
        issues = []
        
        for node in ast.walk(tree):
            # 检查线性搜索
            if isinstance(node, ast.For):
                if self._is_linear_search_pattern(node):
                    issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.INEFFICIENT_ALGORITHM,
                        severity=6,
                        file_path=file_path,
                        line_number=node.lineno,
                        description="使用线性搜索，时间复杂度为O(n)",
                        suggestion="考虑使用字典、集合或二分搜索",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        estimated_impact="可能从O(n)优化到O(1)或O(log n)"
                    ))
        
        return issues
    
    def _check_resource_waste(self, tree: ast.AST, lines: List[str], file_path: str) -> List[PerformanceIssue]:
        """检查资源浪费"""
        issues = []
        
        for node in ast.walk(tree):
            # 检查未使用的变量
            if isinstance(node, ast.Assign):
                if self._is_unused_variable(node, tree):
                    issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.RESOURCE_WASTE,
                        severity=3,
                        file_path=file_path,
                        line_number=node.lineno,
                        description="创建了未使用的变量",
                        suggestion="删除未使用的变量以节省内存",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        estimated_impact="减少内存使用和提升代码可读性"
                    ))
        
        return issues
    
    def _analyze_file_resource_patterns(self, file_path: Path) -> List[ResourceUsagePattern]:
        """分析文件的资源使用模式"""
        patterns = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 分析内存使用模式
            patterns.extend(self._analyze_memory_patterns(tree))
            
            # 分析CPU使用模式
            patterns.extend(self._analyze_cpu_patterns(tree))
            
            # 分析IO模式
            patterns.extend(self._analyze_io_patterns(tree))
            
            # 分析网络模式
            patterns.extend(self._analyze_network_patterns(tree))
            
        except Exception as e:
            print(f"分析文件 {file_path} 资源模式时出错: {e}")
        
        return patterns
    
    def _analyze_memory_patterns(self, tree: ast.AST) -> List[ResourceUsagePattern]:
        """分析内存使用模式"""
        patterns = []
        
        # 统计大数据结构创建
        large_structures = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.List, ast.Dict, ast.Set)):
                if len(node.elts if hasattr(node, 'elts') else node.keys) > 100:
                    large_structures += 1
        
        if large_structures > 0:
            patterns.append(ResourceUsagePattern(
                pattern_type="大数据结构创建",
                frequency=large_structures,
                resource_type="memory",
                usage_intensity=min(large_structures / 10, 1.0),
                optimization_potential=0.7
            ))
        
        return patterns
    
    def _analyze_cpu_patterns(self, tree: ast.AST) -> List[ResourceUsagePattern]:
        """分析CPU使用模式"""
        patterns = []
        
        # 统计计算密集型操作
        compute_operations = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While, ast.ListComp)):
                compute_operations += 1
        
        if compute_operations > 5:
            patterns.append(ResourceUsagePattern(
                pattern_type="计算密集型操作",
                frequency=compute_operations,
                resource_type="cpu",
                usage_intensity=min(compute_operations / 20, 1.0),
                optimization_potential=0.6
            ))
        
        return patterns
    
    def _analyze_io_patterns(self, tree: ast.AST) -> List[ResourceUsagePattern]:
        """分析IO使用模式"""
        patterns = []
        
        # 统计文件操作
        io_operations = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if self._is_io_operation(node):
                    io_operations += 1
        
        if io_operations > 0:
            patterns.append(ResourceUsagePattern(
                pattern_type="文件IO操作",
                frequency=io_operations,
                resource_type="io",
                usage_intensity=min(io_operations / 10, 1.0),
                optimization_potential=0.8
            ))
        
        return patterns
    
    def _analyze_network_patterns(self, tree: ast.AST) -> List[ResourceUsagePattern]:
        """分析网络使用模式"""
        patterns = []
        
        # 统计网络操作
        network_operations = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if self._is_network_operation(node):
                    network_operations += 1
        
        if network_operations > 0:
            patterns.append(ResourceUsagePattern(
                pattern_type="网络请求操作",
                frequency=network_operations,
                resource_type="network",
                usage_intensity=min(network_operations / 5, 1.0),
                optimization_potential=0.9
            ))
        
        return patterns
    
    def _generate_performance_summary(self, issues: List[PerformanceIssue]) -> Dict[str, Any]:
        """生成性能分析摘要"""
        if not issues:
            return {
                'total_issues': 0,
                'severity_distribution': {},
                'issue_type_distribution': {},
                'overall_score': 10
            }
        
        # 按严重程度分布
        severity_dist = {}
        for issue in issues:
            severity_dist[issue.severity] = severity_dist.get(issue.severity, 0) + 1
        
        # 按问题类型分布
        type_dist = {}
        for issue in issues:
            issue_type = issue.issue_type.value
            type_dist[issue_type] = type_dist.get(issue_type, 0) + 1
        
        # 计算总体评分 (1-10)
        avg_severity = sum(issue.severity for issue in issues) / len(issues)
        overall_score = max(1, 10 - int(avg_severity))
        
        return {
            'total_issues': len(issues),
            'severity_distribution': severity_dist,
            'issue_type_distribution': type_dist,
            'average_severity': round(avg_severity, 2),
            'overall_score': overall_score,
            'critical_issues': len([i for i in issues if i.severity >= 8]),
            'high_priority_issues': len([i for i in issues if i.severity >= 6])
        }
    
    def _get_optimization_priorities(self, issues: List[PerformanceIssue]) -> List[Dict[str, Any]]:
        """获取优化优先级"""
        # 按严重程度和影响排序
        sorted_issues = sorted(issues, key=lambda x: (x.severity, len(x.estimated_impact)), reverse=True)
        
        priorities = []
        for i, issue in enumerate(sorted_issues[:5]):  # 前5个优先级
            priorities.append({
                'priority': i + 1,
                'issue_type': issue.issue_type.value,
                'severity': issue.severity,
                'description': issue.description,
                'suggestion': issue.suggestion,
                'estimated_impact': issue.estimated_impact
            })
        
        return priorities
    
    def _generate_resource_summary(self, patterns: List[ResourceUsagePattern]) -> Dict[str, Any]:
        """生成资源使用摘要"""
        if not patterns:
            return {}
        
        resource_types = {}
        total_intensity = 0
        total_optimization_potential = 0
        
        for pattern in patterns:
            resource_type = pattern.resource_type
            if resource_type not in resource_types:
                resource_types[resource_type] = {
                    'count': 0,
                    'total_intensity': 0,
                    'total_optimization_potential': 0
                }
            
            resource_types[resource_type]['count'] += 1
            resource_types[resource_type]['total_intensity'] += pattern.usage_intensity
            resource_types[resource_type]['total_optimization_potential'] += pattern.optimization_potential
            
            total_intensity += pattern.usage_intensity
            total_optimization_potential += pattern.optimization_potential
        
        # 计算平均值
        for resource_type in resource_types:
            count = resource_types[resource_type]['count']
            resource_types[resource_type]['avg_intensity'] = resource_types[resource_type]['total_intensity'] / count
            resource_types[resource_type]['avg_optimization_potential'] = resource_types[resource_type]['total_optimization_potential'] / count
        
        return {
            'resource_distribution': resource_types,
            'overall_intensity': total_intensity / len(patterns),
            'overall_optimization_potential': total_optimization_potential / len(patterns),
            'most_intensive_resource': max(resource_types.keys(), key=lambda x: resource_types[x]['avg_intensity']) if resource_types else None
        }
    
    def _generate_resource_optimization_recommendations(self, patterns: List[ResourceUsagePattern]) -> List[str]:
        """生成资源优化建议"""
        recommendations = []
        
        # 按优化潜力排序
        sorted_patterns = sorted(patterns, key=lambda x: x.optimization_potential, reverse=True)
        
        for pattern in sorted_patterns[:3]:  # 前3个最有潜力的
            if pattern.resource_type == 'memory':
                recommendations.append(f"优化{pattern.pattern_type}以减少内存使用")
            elif pattern.resource_type == 'cpu':
                recommendations.append(f"优化{pattern.pattern_type}以提升CPU效率")
            elif pattern.resource_type == 'io':
                recommendations.append(f"优化{pattern.pattern_type}以减少IO阻塞")
            elif pattern.resource_type == 'network':
                recommendations.append(f"优化{pattern.pattern_type}以减少网络延迟")
        
        return recommendations
    
    def _generate_general_performance_suggestions(self, layer_path: str) -> List[str]:
        """生成通用性能优化建议"""
        suggestions = []
        
        layer_path = Path(layer_path)
        python_files = self._get_python_files(layer_path)
        
        # 检查是否有性能测试
        has_performance_tests = any('performance' in f.name.lower() or 'benchmark' in f.name.lower() 
                                  for f in python_files)
        if not has_performance_tests:
            suggestions.append("添加性能测试和基准测试以监控性能变化")
        
        # 检查是否有缓存机制
        has_caching = any('cache' in f.name.lower() for f in python_files)
        if not has_caching:
            suggestions.append("考虑添加缓存机制以提升重复操作的性能")
        
        # 检查文件数量
        if len(python_files) > 50:
            suggestions.append("考虑模块化重构以提升代码组织和加载性能")
        
        return suggestions
    
    # 辅助方法
    def _get_python_files(self, directory: Path) -> List[Path]:
        """获取目录下所有Python文件"""
        python_files = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files
    
    def _get_code_snippet(self, lines: List[str], line_number: int, context: int = 2) -> str:
        """获取代码片段"""
        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)
        return '\n'.join(lines[start:end])
    
    def _issue_to_dict(self, issue: PerformanceIssue) -> Dict[str, Any]:
        """将性能问题转换为字典"""
        return {
            'issue_type': issue.issue_type.value,
            'severity': issue.severity,
            'file_path': issue.file_path,
            'line_number': issue.line_number,
            'description': issue.description,
            'suggestion': issue.suggestion,
            'code_snippet': issue.code_snippet,
            'estimated_impact': issue.estimated_impact
        }
    
    def _pattern_to_dict(self, pattern: ResourceUsagePattern) -> Dict[str, Any]:
        """将资源使用模式转换为字典"""
        return {
            'pattern_type': pattern.pattern_type,
            'frequency': pattern.frequency,
            'resource_type': pattern.resource_type,
            'usage_intensity': pattern.usage_intensity,
            'optimization_potential': pattern.optimization_potential
        }
    
    def _initialize_performance_patterns(self) -> Dict[str, Any]:
        """初始化性能模式"""
        return {
            'blocking_operations': ['open', 'read', 'write', 'requests.get', 'requests.post'],
            'memory_intensive': ['list', 'dict', 'set', 'pandas.DataFrame'],
            'cpu_intensive': ['for', 'while', 'map', 'filter', 'sorted']
        }
    
    def _initialize_resource_patterns(self) -> Dict[str, Any]:
        """初始化资源模式"""
        return {
            'io_operations': ['open', 'read', 'write', 'close'],
            'network_operations': ['requests', 'urllib', 'socket', 'http'],
            'database_operations': ['execute', 'query', 'select', 'insert']
        }
    
    # 具体检查方法的实现
    def _is_potentially_large_list_comprehension(self, node: ast.ListComp) -> bool:
        """检查是否是潜在的大型列表推导式"""
        # 简化实现：检查是否有嵌套循环或复杂条件
        return len(node.generators) > 1 or any(gen.ifs for gen in node.generators)
    
    def _find_object_creations_in_loop(self, node: ast.AST) -> int:
        """查找循环中的对象创建数量"""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                count += 1
        return count
    
    def _calculate_loop_nesting_depth(self, node: ast.AST) -> int:
        """计算循环嵌套深度"""
        max_depth = 0
        
        def _get_depth(n, current_depth=0):
            nonlocal max_depth
            if isinstance(n, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(n):
                _get_depth(child, current_depth)
        
        _get_depth(node)
        return max_depth
    
    def _is_recursive_function(self, node: ast.FunctionDef) -> bool:
        """检查是否是递归函数"""
        function_name = node.name
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id == function_name:
                    return True
        return False
    
    def _is_blocking_io_operation(self, node: ast.Call) -> bool:
        """检查是否是阻塞IO操作"""
        if isinstance(node.func, ast.Name):
            return node.func.id in ['open', 'read', 'write']
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr in ['read', 'write', 'get', 'post']
        return False
    
    def _is_linear_search_pattern(self, node: ast.For) -> bool:
        """检查是否是线性搜索模式"""
        # 简化实现：检查循环中是否有比较操作
        for child in ast.walk(node):
            if isinstance(child, ast.Compare):
                return True
        return False
    
    def _is_unused_variable(self, node: ast.Assign, tree: ast.AST) -> bool:
        """检查是否是未使用的变量"""
        # 简化实现：这里需要更复杂的作用域分析
        return False  # 暂时返回False，避免误报
    
    def _is_io_operation(self, node: ast.Call) -> bool:
        """检查是否是IO操作"""
        io_functions = ['open', 'read', 'write', 'close']
        if isinstance(node.func, ast.Name):
            return node.func.id in io_functions
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr in io_functions
        return False
    
    def _is_network_operation(self, node: ast.Call) -> bool:
        """检查是否是网络操作"""
        network_functions = ['get', 'post', 'put', 'delete', 'request']
        if isinstance(node.func, ast.Attribute):
            return node.func.attr in network_functions
        return False