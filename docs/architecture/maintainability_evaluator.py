"""
可维护性评估器

分析代码复杂度和耦合度，识别重构机会和改进点，提供代码组织和结构优化建议。
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class MaintainabilityIssueType(Enum):
    """可维护性问题类型枚举"""
    HIGH_COMPLEXITY = "高复杂度"
    TIGHT_COUPLING = "紧耦合"
    LONG_METHOD = "方法过长"
    LARGE_CLASS = "类过大"
    DUPLICATE_CODE = "重复代码"
    POOR_NAMING = "命名不规范"
    MISSING_DOCUMENTATION = "缺少文档"
    DEEP_NESTING = "嵌套过深"


@dataclass
class MaintainabilityIssue:
    """可维护性问题数据模型"""
    issue_type: MaintainabilityIssueType
    severity: int  # 1-10严重程度
    file_path: str
    line_number: int
    description: str
    suggestion: str
    code_snippet: str
    refactoring_effort: str  # 重构工作量估计


@dataclass
class ComplexityMetrics:
    """复杂度指标"""
    cyclomatic_complexity: int
    cognitive_complexity: int
    nesting_depth: int
    method_count: int
    class_count: int
    lines_of_code: int
    maintainability_index: float  # 0-100可维护性指数


@dataclass
class CouplingMetrics:
    """耦合度指标"""
    afferent_coupling: int  # 传入耦合
    efferent_coupling: int  # 传出耦合
    instability: float  # 不稳定性 (0-1)
    abstractness: float  # 抽象性 (0-1)
    distance_from_main_sequence: float  # 距离主序列的距离
    coupling_between_objects: int  # 对象间耦合


class MaintainabilityEvaluator:
    """
    可维护性评估器
    
    分析代码复杂度和耦合度，识别重构机会和改进点。
    """
    
    def __init__(self):
        """初始化可维护性评估器"""
        self.issue_patterns = self._initialize_issue_patterns()
        
    def evaluate_maintainability(self, layer_path: str) -> Dict[str, Any]:
        """
        评估层级的可维护性
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            包含可维护性评估结果的字典
        """
        layer_path = Path(layer_path)
        python_files = self._get_python_files(layer_path)
        
        maintainability_issues = []
        complexity_metrics = {}
        coupling_metrics = {}
        file_analysis = {}
        
        for file_path in python_files:
            try:
                # 分析单个文件
                file_issues = self._analyze_file_maintainability(file_path)
                file_complexity = self._calculate_file_complexity(file_path)
                file_coupling = self._calculate_file_coupling(file_path, python_files)
                
                relative_path = str(file_path.relative_to(layer_path))
                
                if file_issues:
                    maintainability_issues.extend(file_issues)
                    file_analysis[relative_path] = file_issues
                
                complexity_metrics[relative_path] = file_complexity
                coupling_metrics[relative_path] = file_coupling
                
            except Exception as e:
                print(f"分析文件 {file_path} 可维护性时出错: {e}")
        
        # 按严重程度排序
        maintainability_issues.sort(key=lambda x: x.severity, reverse=True)
        
        # 生成可维护性摘要
        maintainability_summary = self._generate_maintainability_summary(
            maintainability_issues, complexity_metrics, coupling_metrics
        )
        
        return {
            'maintainability_issues': [self._issue_to_dict(issue) for issue in maintainability_issues],
            'complexity_metrics': complexity_metrics,
            'coupling_metrics': coupling_metrics,
            'file_analysis': file_analysis,
            'maintainability_summary': maintainability_summary,
            'refactoring_priorities': self._get_refactoring_priorities(maintainability_issues),
            'maintainability_score': self._calculate_maintainability_score(
                maintainability_issues, complexity_metrics, coupling_metrics
            )
        }
    
    def generate_maintainability_suggestions(self, layer_path: str) -> List[str]:
        """
        生成可维护性改进建议
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            可维护性改进建议列表
        """
        evaluation = self.evaluate_maintainability(layer_path)
        suggestions = []
        
        # 基于高严重程度问题的建议
        high_priority_issues = [
            issue for issue in evaluation['maintainability_issues']
            if issue['severity'] >= 7
        ]
        
        for issue in high_priority_issues[:5]:
            suggestions.append(f"修复{issue['issue_type']}: {issue['suggestion']}")
        
        # 基于复杂度指标的建议
        complexity_suggestions = self._generate_complexity_suggestions(
            evaluation['complexity_metrics']
        )
        suggestions.extend(complexity_suggestions[:3])
        
        # 基于耦合度指标的建议
        coupling_suggestions = self._generate_coupling_suggestions(
            evaluation['coupling_metrics']
        )
        suggestions.extend(coupling_suggestions[:3])
        
        return suggestions[:10]
    
    def _analyze_file_maintainability(self, file_path: Path) -> List[MaintainabilityIssue]:
        """分析单个文件的可维护性问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # 检查各种可维护性问题
            issues.extend(self._check_complexity_issues(tree, lines, str(file_path)))
            issues.extend(self._check_coupling_issues(tree, lines, str(file_path)))
            issues.extend(self._check_method_length_issues(tree, lines, str(file_path)))
            issues.extend(self._check_class_size_issues(tree, lines, str(file_path)))
            issues.extend(self._check_naming_issues(tree, lines, str(file_path)))
            issues.extend(self._check_documentation_issues(tree, lines, str(file_path)))
            
        except Exception as e:
            print(f"解析文件 {file_path} 时出错: {e}")
        
        return issues
    
    def _calculate_file_complexity(self, file_path: Path) -> ComplexityMetrics:
        """计算文件复杂度指标"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # 计算各种复杂度指标
            cyclomatic = self._calculate_cyclomatic_complexity(tree)
            cognitive = self._calculate_cognitive_complexity(tree)
            nesting = self._calculate_max_nesting_depth(tree)
            method_count = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
            class_count = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            loc = len(lines)
            
            # 计算可维护性指数 (0-100)
            maintainability_index = self._calculate_maintainability_index(
                cyclomatic, loc, method_count, class_count
            )
            
            return ComplexityMetrics(
                cyclomatic_complexity=cyclomatic,
                cognitive_complexity=cognitive,
                nesting_depth=nesting,
                method_count=method_count,
                class_count=class_count,
                lines_of_code=loc,
                maintainability_index=maintainability_index
            )
            
        except Exception:
            return ComplexityMetrics(0, 0, 0, 0, 0, 0, 100.0)
    
    def _calculate_file_coupling(self, file_path: Path, all_files: List[Path]) -> CouplingMetrics:
        """计算文件耦合度指标"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 计算传入和传出耦合
            afferent = self._calculate_afferent_coupling(file_path, all_files)
            efferent = self._calculate_efferent_coupling(tree)
            
            # 计算不稳定性 I = Ce / (Ca + Ce)
            instability = efferent / (afferent + efferent) if (afferent + efferent) > 0 else 0
            
            # 计算抽象性
            abstractness = self._calculate_abstractness(tree)
            
            # 计算距离主序列的距离 D = |A + I - 1|
            distance = abs(abstractness + instability - 1)
            
            # 计算对象间耦合
            cbo = self._calculate_coupling_between_objects(tree)
            
            return CouplingMetrics(
                afferent_coupling=afferent,
                efferent_coupling=efferent,
                instability=instability,
                abstractness=abstractness,
                distance_from_main_sequence=distance,
                coupling_between_objects=cbo
            )
            
        except Exception:
            return CouplingMetrics(0, 0, 0.0, 0.0, 0.0, 0)
    
    def _check_complexity_issues(self, tree: ast.AST, lines: List[str], file_path: str) -> List[MaintainabilityIssue]:
        """检查复杂度相关问题"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_function_complexity(node)
                if complexity > 10:
                    issues.append(MaintainabilityIssue(
                        issue_type=MaintainabilityIssueType.HIGH_COMPLEXITY,
                        severity=min(10, 5 + complexity // 5),
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"函数 {node.name} 的圈复杂度为 {complexity}，超过建议值10",
                        suggestion="考虑将函数拆分为更小的函数或简化逻辑",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        refactoring_effort="中等"
                    ))
        
        return issues
    
    def _check_coupling_issues(self, tree: ast.AST, lines: List[str], file_path: str) -> List[MaintainabilityIssue]:
        """检查耦合度相关问题"""
        issues = []
        
        # 检查导入数量
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
        
        if len(imports) > 15:
            issues.append(MaintainabilityIssue(
                issue_type=MaintainabilityIssueType.TIGHT_COUPLING,
                severity=6,
                file_path=file_path,
                line_number=1,
                description=f"文件导入了 {len(imports)} 个模块，可能存在过度耦合",
                suggestion="考虑重构以减少依赖，或将功能拆分到多个文件",
                code_snippet="# 导入语句过多",
                refactoring_effort="高"
            ))
        
        return issues
    
    def _check_method_length_issues(self, tree: ast.AST, lines: List[str], file_path: str) -> List[MaintainabilityIssue]:
        """检查方法长度问题"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 计算函数行数
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 20
                func_lines = end_line - node.lineno + 1
                
                if func_lines > 50:
                    issues.append(MaintainabilityIssue(
                        issue_type=MaintainabilityIssueType.LONG_METHOD,
                        severity=7,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"函数 {node.name} 有 {func_lines} 行，超过建议的50行",
                        suggestion="将长函数拆分为多个较小的函数",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        refactoring_effort="中等"
                    ))
        
        return issues
    
    def _check_class_size_issues(self, tree: ast.AST, lines: List[str], file_path: str) -> List[MaintainabilityIssue]:
        """检查类大小问题"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 计算类中的方法数量
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                
                if len(methods) > 20:
                    issues.append(MaintainabilityIssue(
                        issue_type=MaintainabilityIssueType.LARGE_CLASS,
                        severity=6,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"类 {node.name} 有 {len(methods)} 个方法，可能职责过多",
                        suggestion="考虑将类拆分或应用单一职责原则",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        refactoring_effort="高"
                    ))
        
        return issues
    
    def _check_naming_issues(self, tree: ast.AST, lines: List[str], file_path: str) -> List[MaintainabilityIssue]:
        """检查命名规范问题"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not self._is_valid_function_name(node.name):
                    issues.append(MaintainabilityIssue(
                        issue_type=MaintainabilityIssueType.POOR_NAMING,
                        severity=3,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"函数名 {node.name} 不符合命名规范",
                        suggestion="使用小写字母和下划线的命名方式",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        refactoring_effort="低"
                    ))
        
        return issues
    
    def _check_documentation_issues(self, tree: ast.AST, lines: List[str], file_path: str) -> List[MaintainabilityIssue]:
        """检查文档相关问题"""
        issues = []
        
        # 检查模块级文档
        if not ast.get_docstring(tree):
            issues.append(MaintainabilityIssue(
                issue_type=MaintainabilityIssueType.MISSING_DOCUMENTATION,
                severity=4,
                file_path=file_path,
                line_number=1,
                description="缺少模块级文档字符串",
                suggestion="添加模块级docstring说明模块用途",
                code_snippet="# 文件开头缺少文档",
                refactoring_effort="低"
            ))
        
        # 检查函数文档
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                if not ast.get_docstring(node):
                    issues.append(MaintainabilityIssue(
                        issue_type=MaintainabilityIssueType.MISSING_DOCUMENTATION,
                        severity=3,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"公共函数 {node.name} 缺少文档字符串",
                        suggestion="添加函数docstring说明参数、返回值和用途",
                        code_snippet=self._get_code_snippet(lines, node.lineno),
                        refactoring_effort="低"
                    ))
        
        return issues
    
    # 辅助方法实现
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
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """计算认知复杂度"""
        # 简化实现，实际应该考虑嵌套层级
        complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += 1
        
        return complexity
    
    def _calculate_max_nesting_depth(self, tree: ast.AST) -> int:
        """计算最大嵌套深度"""
        def _get_depth(node, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    child_depth = _get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = _get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        return _get_depth(tree)
    
    def _calculate_maintainability_index(self, cyclomatic: int, loc: int, 
                                       method_count: int, class_count: int) -> float:
        """计算可维护性指数"""
        # 简化的可维护性指数计算
        base_score = 100
        
        # 基于复杂度的扣分
        complexity_penalty = min(cyclomatic * 2, 30)
        
        # 基于代码行数的扣分
        loc_penalty = min(loc / 10, 20)
        
        # 基于方法数量的扣分
        method_penalty = min(method_count, 15)
        
        score = base_score - complexity_penalty - loc_penalty - method_penalty
        return max(0, min(100, score))
    
    def _calculate_afferent_coupling(self, file_path: Path, all_files: List[Path]) -> int:
        """计算传入耦合（有多少文件依赖这个文件）"""
        count = 0
        file_name = file_path.stem
        
        for other_file in all_files:
            if other_file == file_path:
                continue
            
            try:
                with open(other_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单检查是否导入了这个文件
                if file_name in content:
                    count += 1
            except Exception:
                pass
        
        return count
    
    def _calculate_efferent_coupling(self, tree: ast.AST) -> int:
        """计算传出耦合（这个文件依赖多少其他文件）"""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        return len(imports)
    
    def _calculate_abstractness(self, tree: ast.AST) -> float:
        """计算抽象性（抽象类和接口的比例）"""
        total_classes = 0
        abstract_classes = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                total_classes += 1
                
                # 检查是否是抽象类（简化检查）
                if any('ABC' in base.id if isinstance(base, ast.Name) else False 
                      for base in node.bases):
                    abstract_classes += 1
        
        return abstract_classes / total_classes if total_classes > 0 else 0
    
    def _calculate_coupling_between_objects(self, tree: ast.AST) -> int:
        """计算对象间耦合"""
        # 简化实现：统计类之间的引用
        coupling = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    coupling += 1
        
        return coupling
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """计算单个函数的复杂度"""
        complexity = 1
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _is_valid_function_name(self, name: str) -> bool:
        """检查函数名是否符合规范"""
        # Python函数名应该是小写字母和下划线
        return name.islower() and '_' in name or name.islower()
    
    def _generate_maintainability_summary(self, issues: List[MaintainabilityIssue], 
                                        complexity_metrics: Dict, 
                                        coupling_metrics: Dict) -> Dict[str, Any]:
        """生成可维护性摘要"""
        if not issues:
            return {
                'total_issues': 0,
                'severity_distribution': {},
                'issue_type_distribution': {},
                'overall_maintainability_score': 10
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
        
        # 计算总体可维护性评分
        avg_severity = sum(issue.severity for issue in issues) / len(issues)
        overall_score = max(1, 10 - int(avg_severity))
        
        # 计算平均复杂度
        avg_complexity = 0
        if complexity_metrics:
            avg_maintainability_index = sum(
                m.maintainability_index for m in complexity_metrics.values()
            ) / len(complexity_metrics)
            avg_complexity = 100 - avg_maintainability_index
        
        return {
            'total_issues': len(issues),
            'severity_distribution': severity_dist,
            'issue_type_distribution': type_dist,
            'average_severity': round(avg_severity, 2),
            'overall_maintainability_score': overall_score,
            'average_complexity_score': round(avg_complexity, 2),
            'critical_issues': len([i for i in issues if i.severity >= 8]),
            'high_priority_issues': len([i for i in issues if i.severity >= 6])
        }
    
    def _get_refactoring_priorities(self, issues: List[MaintainabilityIssue]) -> List[Dict[str, Any]]:
        """获取重构优先级"""
        # 按严重程度和重构工作量排序
        def priority_score(issue):
            effort_weights = {'低': 1, '中等': 2, '高': 3}
            effort_weight = effort_weights.get(issue.refactoring_effort, 2)
            return issue.severity / effort_weight
        
        sorted_issues = sorted(issues, key=priority_score, reverse=True)
        
        priorities = []
        for i, issue in enumerate(sorted_issues[:5]):
            priorities.append({
                'priority': i + 1,
                'issue_type': issue.issue_type.value,
                'severity': issue.severity,
                'description': issue.description,
                'suggestion': issue.suggestion,
                'refactoring_effort': issue.refactoring_effort,
                'file_path': issue.file_path,
                'line_number': issue.line_number
            })
        
        return priorities
    
    def _calculate_maintainability_score(self, issues: List[MaintainabilityIssue],
                                       complexity_metrics: Dict,
                                       coupling_metrics: Dict) -> float:
        """计算总体可维护性评分 (0-10)"""
        base_score = 10.0
        
        # 基于问题数量和严重程度的扣分
        if issues:
            avg_severity = sum(issue.severity for issue in issues) / len(issues)
            issue_penalty = min(avg_severity / 2, 4.0)
            base_score -= issue_penalty
        
        # 基于复杂度的扣分
        if complexity_metrics:
            avg_maintainability_index = sum(
                m.maintainability_index for m in complexity_metrics.values()
            ) / len(complexity_metrics)
            complexity_penalty = (100 - avg_maintainability_index) / 20
            base_score -= complexity_penalty
        
        # 基于耦合度的扣分
        if coupling_metrics:
            avg_instability = sum(
                m.instability for m in coupling_metrics.values()
            ) / len(coupling_metrics)
            coupling_penalty = avg_instability * 2
            base_score -= coupling_penalty
        
        return max(0.0, min(10.0, base_score))
    
    def _generate_complexity_suggestions(self, complexity_metrics: Dict) -> List[str]:
        """基于复杂度指标生成建议"""
        suggestions = []
        
        high_complexity_files = [
            (file, metrics) for file, metrics in complexity_metrics.items()
            if metrics.maintainability_index < 50
        ]
        
        if high_complexity_files:
            suggestions.append("重构高复杂度文件以提高可维护性")
        
        high_nesting_files = [
            (file, metrics) for file, metrics in complexity_metrics.items()
            if metrics.nesting_depth > 4
        ]
        
        if high_nesting_files:
            suggestions.append("减少代码嵌套深度，考虑提前返回或函数拆分")
        
        return suggestions
    
    def _generate_coupling_suggestions(self, coupling_metrics: Dict) -> List[str]:
        """基于耦合度指标生成建议"""
        suggestions = []
        
        high_coupling_files = [
            (file, metrics) for file, metrics in coupling_metrics.items()
            if metrics.efferent_coupling > 10
        ]
        
        if high_coupling_files:
            suggestions.append("减少文件间的依赖关系，考虑依赖注入或接口抽象")
        
        unstable_files = [
            (file, metrics) for file, metrics in coupling_metrics.items()
            if metrics.instability > 0.8
        ]
        
        if unstable_files:
            suggestions.append("提高不稳定模块的抽象性或减少其依赖")
        
        return suggestions
    
    def _issue_to_dict(self, issue: MaintainabilityIssue) -> Dict[str, Any]:
        """将可维护性问题转换为字典"""
        return {
            'issue_type': issue.issue_type.value,
            'severity': issue.severity,
            'file_path': issue.file_path,
            'line_number': issue.line_number,
            'description': issue.description,
            'suggestion': issue.suggestion,
            'code_snippet': issue.code_snippet,
            'refactoring_effort': issue.refactoring_effort
        }
    
    def _initialize_issue_patterns(self) -> Dict[str, Any]:
        """初始化问题模式"""
        return {
            'complexity_thresholds': {
                'cyclomatic': 10,
                'cognitive': 15,
                'nesting': 4
            },
            'size_thresholds': {
                'method_lines': 50,
                'class_methods': 20,
                'file_lines': 500
            },
            'coupling_thresholds': {
                'imports': 15,
                'efferent': 10,
                'instability': 0.8
            }
        }