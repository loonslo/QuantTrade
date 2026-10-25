"""
层级分析器

分析代码结构、依赖关系和设计模式，为文档生成提供数据支持。
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import importlib.util
from dataclasses import dataclass
from enum import Enum


class FileCategory(Enum):
    """文件分类枚举"""
    CORE_MODULE = "核心模块"
    SERVICE_MODULE = "服务模块"
    MODEL_MODULE = "数据模型"
    INTERFACE_MODULE = "接口定义"
    UTILITY_MODULE = "工具模块"
    CONFIG_FILE = "配置文件"
    TEST_FILE = "测试文件"
    DOCUMENTATION = "文档文件"
    SCRIPT_FILE = "脚本文件"
    DATA_FILE = "数据文件"
    UNKNOWN = "未知类型"


@dataclass
class FileAnalysis:
    """文件分析结果"""
    name: str
    path: str
    category: FileCategory
    purpose: str
    description: str
    complexity_score: int  # 1-10的复杂度评分
    dependencies: List[str]
    exports: List[str]
    key_functions: List[str]
    key_classes: List[str]
    lines_of_code: int
    documentation_coverage: float  # 0-1的文档覆盖率


class FilePurposeAnalyzer:
    """
    文件用途分析器
    
    基于文件名、内容和结构分析文件的用途和重要性。
    """
    
    def __init__(self):
        """初始化文件用途分析器"""
        self.python_extensions = {'.py'}
        self.config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'}
        self.doc_extensions = {'.md', '.rst', '.txt'}
        self.data_extensions = {'.csv', '.db', '.sqlite', '.sql'}
        
        # 文件名模式到类别的映射
        self.filename_patterns = {
            FileCategory.CORE_MODULE: [
                r'__init__\.py$',
                r'main\.py$',
                r'app\.py$',
                r'.*_core\.py$',
                r'.*_engine\.py$',
                r'.*_runner\.py$'
            ],
            FileCategory.SERVICE_MODULE: [
                r'.*_service\.py$',
                r'.*_manager\.py$',
                r'.*_handler\.py$',
                r'.*_processor\.py$',
                r'.*_provider\.py$'
            ],
            FileCategory.MODEL_MODULE: [
                r'.*_model\.py$',
                r'.*_models\.py$',
                r'.*_schema\.py$',
                r'.*_schemas\.py$',
                r'models\.py$'
            ],
            FileCategory.INTERFACE_MODULE: [
                r'.*_interface\.py$',
                r'.*_interfaces\.py$',
                r'.*_base\.py$',
                r'.*_abstract\.py$',
                r'.*_protocol\.py$'
            ],
            FileCategory.UTILITY_MODULE: [
                r'.*_utils\.py$',
                r'.*_util\.py$',
                r'.*_helper\.py$',
                r'.*_helpers\.py$',
                r'utils\.py$',
                r'helpers\.py$'
            ],
            FileCategory.CONFIG_FILE: [
                r'.*config.*\.(json|yaml|yml|toml|ini|cfg)$',
                r'settings\.(json|yaml|yml|toml|ini|cfg)$',
                r'.*_config\.py$',
                r'settings\.py$'
            ],
            FileCategory.TEST_FILE: [
                r'test_.*\.py$',
                r'.*_test\.py$',
                r'.*_tests\.py$',
                r'tests\.py$'
            ],
            FileCategory.DOCUMENTATION: [
                r'README\.md$',
                r'.*\.md$',
                r'.*\.rst$',
                r'.*\.txt$'
            ],
            FileCategory.SCRIPT_FILE: [
                r'run_.*\.py$',
                r'.*_script\.py$',
                r'setup\.py$',
                r'install\.py$'
            ],
            FileCategory.DATA_FILE: [
                r'.*\.(csv|db|sqlite|sql)$'
            ]
        }
    
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """
        分析单个文件的用途和特征
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件分析结果
        """
        category = self._categorize_file(file_path)
        purpose = self._determine_purpose(file_path, category)
        description = self._generate_description(file_path, category)
        
        # 对Python文件进行深度分析
        if file_path.suffix == '.py':
            code_analysis = self._analyze_python_code(file_path)
        else:
            code_analysis = {
                'complexity_score': 1,
                'dependencies': [],
                'exports': [],
                'key_functions': [],
                'key_classes': [],
                'lines_of_code': self._count_lines(file_path),
                'documentation_coverage': 0.0
            }
        
        return FileAnalysis(
            name=file_path.name,
            path=str(file_path),
            category=category,
            purpose=purpose,
            description=description,
            **code_analysis
        )
    
    def analyze_directory_files(self, directory: Path) -> List[FileAnalysis]:
        """
        分析目录中所有文件的用途
        
        Args:
            directory: 目录路径
            
        Returns:
            文件分析结果列表
        """
        analyses = []
        
        try:
            for item in directory.iterdir():
                if item.is_file() and not item.name.startswith('.'):
                    try:
                        analysis = self.analyze_file(item)
                        analyses.append(analysis)
                    except Exception as e:
                        print(f"分析文件 {item} 时出错: {e}")
        except (OSError, PermissionError):
            pass
        
        return analyses
    
    def generate_file_summary(self, analyses: List[FileAnalysis]) -> Dict[str, any]:
        """
        生成文件分析摘要
        
        Args:
            analyses: 文件分析结果列表
            
        Returns:
            分析摘要字典
        """
        if not analyses:
            return {}
        
        # 按类别统计
        category_counts = {}
        for analysis in analyses:
            category = analysis.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 计算平均复杂度
        avg_complexity = sum(a.complexity_score for a in analyses) / len(analyses)
        
        # 找出最重要的文件
        important_files = sorted(analyses, key=lambda x: x.complexity_score, reverse=True)[:5]
        
        # 统计总代码行数
        total_lines = sum(a.lines_of_code for a in analyses)
        
        return {
            'total_files': len(analyses),
            'category_distribution': category_counts,
            'average_complexity': round(avg_complexity, 2),
            'total_lines_of_code': total_lines,
            'most_important_files': [
                {
                    'name': f.name,
                    'category': f.category.value,
                    'complexity': f.complexity_score,
                    'purpose': f.purpose
                }
                for f in important_files
            ]
        }
    
    def _categorize_file(self, file_path: Path) -> FileCategory:
        """根据文件名和扩展名分类文件"""
        file_name = file_path.name.lower()
        
        # 检查文件名模式
        for category, patterns in self.filename_patterns.items():
            for pattern in patterns:
                if re.search(pattern, file_name, re.IGNORECASE):
                    return category
        
        # 基于扩展名的默认分类
        ext = file_path.suffix.lower()
        if ext in self.python_extensions:
            return FileCategory.CORE_MODULE
        elif ext in self.config_extensions:
            return FileCategory.CONFIG_FILE
        elif ext in self.doc_extensions:
            return FileCategory.DOCUMENTATION
        elif ext in self.data_extensions:
            return FileCategory.DATA_FILE
        
        return FileCategory.UNKNOWN
    
    def _determine_purpose(self, file_path: Path, category: FileCategory) -> str:
        """确定文件的具体用途"""
        file_name = file_path.name.lower()
        
        # 特定文件名的用途
        specific_purposes = {
            '__init__.py': '模块初始化和接口导出',
            'main.py': '程序主入口点',
            'app.py': '应用程序启动文件',
            'setup.py': 'Python包安装配置',
            'requirements.txt': 'Python依赖声明',
            'readme.md': '项目说明文档',
            'config.py': '配置参数定义',
            'settings.py': '应用设置管理'
        }
        
        if file_name in specific_purposes:
            return specific_purposes[file_name]
        
        # 基于类别的通用用途
        category_purposes = {
            FileCategory.CORE_MODULE: '核心业务逻辑实现',
            FileCategory.SERVICE_MODULE: '服务层功能提供',
            FileCategory.MODEL_MODULE: '数据结构和模型定义',
            FileCategory.INTERFACE_MODULE: '接口和抽象类定义',
            FileCategory.UTILITY_MODULE: '通用工具函数提供',
            FileCategory.CONFIG_FILE: '配置参数存储',
            FileCategory.TEST_FILE: '单元测试和功能验证',
            FileCategory.DOCUMENTATION: '项目文档和说明',
            FileCategory.SCRIPT_FILE: '自动化脚本执行',
            FileCategory.DATA_FILE: '数据存储和管理'
        }
        
        return category_purposes.get(category, '通用文件功能')
    
    def _generate_description(self, file_path: Path, category: FileCategory) -> str:
        """生成文件的详细描述"""
        # 尝试从文件内容获取描述
        if file_path.suffix == '.py':
            docstring = self._extract_module_docstring(file_path)
            if docstring:
                return docstring.split('\n')[0]  # 取第一行作为描述
        
        # 基于文件名生成描述
        name_without_ext = file_path.stem
        
        # 处理常见的命名模式
        if '_' in name_without_ext:
            parts = name_without_ext.split('_')
            if len(parts) >= 2:
                return f"{parts[0]}相关的{parts[-1]}功能模块"
        
        return f"{category.value}文件"
    
    def _analyze_python_code(self, file_path: Path) -> Dict[str, any]:
        """分析Python代码文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 提取信息
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            imports = self._extract_imports(tree)
            
            # 计算复杂度
            complexity = self._calculate_complexity(tree, len(content.split('\n')))
            
            # 计算文档覆盖率
            doc_coverage = self._calculate_documentation_coverage(tree)
            
            return {
                'complexity_score': complexity,
                'dependencies': imports,
                'exports': functions + classes,
                'key_functions': functions[:10],  # 限制数量
                'key_classes': classes,
                'lines_of_code': len(content.split('\n')),
                'documentation_coverage': doc_coverage
            }
        
        except Exception:
            return {
                'complexity_score': 1,
                'dependencies': [],
                'exports': [],
                'key_functions': [],
                'key_classes': [],
                'lines_of_code': self._count_lines(file_path),
                'documentation_coverage': 0.0
            }
    
    def _extract_module_docstring(self, file_path: Path) -> Optional[str]:
        """提取模块的docstring"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            return ast.get_docstring(tree)
        
        except Exception:
            return None
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """提取导入的模块"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
        
        return list(set(imports))
    
    def _calculate_complexity(self, tree: ast.AST, line_count: int) -> int:
        """计算代码复杂度评分 (1-10)"""
        # 基础评分
        score = 1
        
        # 基于代码行数
        if line_count > 500:
            score += 3
        elif line_count > 200:
            score += 2
        elif line_count > 100:
            score += 1
        
        # 基于函数和类的数量
        functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        
        if functions > 20 or classes > 10:
            score += 2
        elif functions > 10 or classes > 5:
            score += 1
        
        # 基于嵌套深度
        max_depth = self._calculate_max_nesting_depth(tree)
        if max_depth > 4:
            score += 2
        elif max_depth > 2:
            score += 1
        
        return min(score, 10)
    
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
    
    def _calculate_documentation_coverage(self, tree: ast.AST) -> float:
        """计算文档覆盖率"""
        total_items = 0
        documented_items = 0
        
        # 检查模块级docstring
        if ast.get_docstring(tree):
            documented_items += 1
        total_items += 1
        
        # 检查函数和类的docstring
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                total_items += 1
                if ast.get_docstring(node):
                    documented_items += 1
        
        return documented_items / total_items if total_items > 0 else 0.0
    
    def _count_lines(self, file_path: Path) -> int:
        """计算文件行数"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except Exception:
            return 0


class LayerAnalyzer:
    """
    层级分析器
    
    负责分析层级的代码结构、依赖关系、设计模式等信息。
    """
    
    def __init__(self, project_root: str):
        """
        初始化层级分析器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root)
        self.python_extensions = {'.py'}
        self.config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini'}
        self.doc_extensions = {'.md', '.rst', '.txt'}
        self.file_purpose_analyzer = FilePurposeAnalyzer()
    
    def analyze_dependencies(self, layer_path: str) -> Dict[str, any]:
        """
        分析层级的依赖关系
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            包含详细依赖信息的字典
        """
        layer_path = Path(layer_path)
        
        # 获取所有Python文件
        python_files = self._get_python_files(layer_path)
        
        # 分析结果存储
        internal_dependencies = set()  # 项目内层级依赖
        external_dependencies = set()  # 外部库依赖
        file_dependencies = {}  # 每个文件的依赖详情
        dependency_graph = {}  # 依赖关系图
        
        for file_path in python_files:
            try:
                file_deps = self._analyze_file_dependencies(file_path)
                relative_path = str(file_path.relative_to(layer_path))
                file_dependencies[relative_path] = file_deps
                
                # 分类依赖
                internal_deps = self._filter_project_dependencies(file_deps['imports'])
                external_deps = file_deps['imports'] - internal_deps
                
                internal_dependencies.update(internal_deps)
                external_dependencies.update(external_deps)
                
                # 构建依赖图
                dependency_graph[relative_path] = {
                    'internal': list(internal_deps),
                    'external': list(external_deps),
                    'function_calls': file_deps.get('function_calls', []),
                    'class_usage': file_deps.get('class_usage', [])
                }
                
            except Exception as e:
                print(f"分析文件 {file_path} 依赖时出错: {e}")
        
        # 分析层级间调用关系
        inter_layer_calls = self._analyze_inter_layer_calls(layer_path, python_files)
        
        # 生成依赖强度分析
        dependency_strength = self._calculate_dependency_strength(dependency_graph)
        
        return {
            'internal_dependencies': sorted(list(internal_dependencies)),
            'external_dependencies': sorted(list(external_dependencies)),
            'file_dependencies': file_dependencies,
            'dependency_graph': dependency_graph,
            'inter_layer_calls': inter_layer_calls,
            'dependency_strength': dependency_strength,
            'circular_dependencies': self._detect_circular_dependencies(dependency_graph),
            'dependency_summary': {
                'total_internal': len(internal_dependencies),
                'total_external': len(external_dependencies),
                'most_dependent_files': self._get_most_dependent_files(file_dependencies),
                'coupling_score': self._calculate_coupling_score(dependency_graph)
            }
        }
    
    def identify_design_patterns(self, layer_path: str) -> Dict[str, any]:
        """
        识别层级中使用的设计模式
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            包含设计模式详细信息的字典
        """
        layer_path = Path(layer_path)
        python_files = self._get_python_files(layer_path)
        
        # 设计模式分析结果
        design_patterns = {}
        architectural_patterns = {}
        file_pattern_details = {}
        
        for file_path in python_files:
            try:
                relative_path = str(file_path.relative_to(layer_path))
                
                # 分析设计模式
                file_design_patterns = self._identify_file_design_patterns(file_path)
                if file_design_patterns:
                    file_pattern_details[relative_path] = file_design_patterns
                    
                    # 汇总设计模式
                    for pattern_name, pattern_info in file_design_patterns.items():
                        if pattern_name not in design_patterns:
                            design_patterns[pattern_name] = {
                                'files': [],
                                'evidence': [],
                                'confidence': 0.0
                            }
                        design_patterns[pattern_name]['files'].append(relative_path)
                        design_patterns[pattern_name]['evidence'].extend(pattern_info['evidence'])
                        design_patterns[pattern_name]['confidence'] = max(
                            design_patterns[pattern_name]['confidence'], 
                            pattern_info['confidence']
                        )
                
            except Exception as e:
                print(f"分析文件 {file_path} 设计模式时出错: {e}")
        
        # 分析架构模式
        architectural_patterns = self._identify_architectural_patterns(layer_path, python_files)
        
        # 分析关键架构决策
        architectural_decisions = self._analyze_architectural_decisions(layer_path, python_files)
        
        return {
            'design_patterns': design_patterns,
            'architectural_patterns': architectural_patterns,
            'architectural_decisions': architectural_decisions,
            'file_pattern_details': file_pattern_details,
            'pattern_summary': {
                'total_patterns': len(design_patterns),
                'most_common_patterns': self._get_most_common_patterns(design_patterns),
                'pattern_complexity_score': self._calculate_pattern_complexity(design_patterns)
            }
        }
    
    def generate_optimization_suggestions(self, layer_path: str) -> List[str]:
        """
        生成代码优化建议
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            优化建议列表
        """
        suggestions = []
        layer_path = Path(layer_path)
        
        # 分析文件结构
        python_files = self._get_python_files(layer_path)
        
        # 检查文件数量和组织
        if len(python_files) > 20:
            suggestions.append("考虑将大型模块拆分为更小的子模块以提高可维护性")
        
        # 检查是否有__init__.py文件
        if not (layer_path / "__init__.py").exists():
            suggestions.append("添加__init__.py文件以明确模块接口")
        
        # 分析代码复杂度
        for file_path in python_files:
            try:
                file_suggestions = self._analyze_file_complexity(file_path)
                suggestions.extend(file_suggestions)
            except Exception as e:
                print(f"分析文件 {file_path} 复杂度时出错: {e}")
        
        # 检查文档覆盖率
        doc_files = self._get_documentation_files(layer_path)
        if not doc_files:
            suggestions.append("添加README.md或其他文档文件以提高代码可读性")
        
        return suggestions[:10]  # 限制建议数量
    
    def get_layer_description(self, layer_path: str) -> str:
        """
        获取层级描述
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            层级描述文本
        """
        layer_path = Path(layer_path)
        layer_name = layer_path.name
        
        # 尝试从README文件获取描述
        readme_files = ['README.md', 'readme.md', 'README.txt', 'readme.txt']
        for readme_file in readme_files:
            readme_path = layer_path / readme_file
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 提取第一段作为描述
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                return line
                except Exception:
                    pass
        
        # 尝试从__init__.py的docstring获取描述
        init_file = layer_path / "__init__.py"
        if init_file.exists():
            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    if ast.get_docstring(tree):
                        return ast.get_docstring(tree).split('\n')[0]
            except Exception:
                pass
        
        # 默认描述
        descriptions = {
            'core': '系统核心抽象和接口定义层',
            'data': '数据获取、存储和管理层',
            'api': 'REST API和WebSocket接口服务层',
            'strategies': '交易策略实现层',
            'user_strategies': '用户自定义策略层',
            'analysis': '性能分析和技术分析层',
            'services': '业务服务和工具组件层',
            'utils': '通用工具和辅助函数层',
            'config': '系统配置和参数管理层',
            'optimization': '策略优化算法和工具层',
            'docs': '项目文档和说明层'
        }
        
        return descriptions.get(layer_name, f'{layer_name}功能层')
    
    def get_key_files(self, layer_path: str) -> List[str]:
        """
        获取层级中的关键文件
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            关键文件路径列表
        """
        layer_path = Path(layer_path)
        key_files = []
        
        # 优先级文件模式
        priority_patterns = [
            r'__init__\.py$',
            r'main\.py$',
            r'app\.py$',
            r'.*_manager\.py$',
            r'.*_service\.py$',
            r'.*_interface\.py$',
            r'.*_base\.py$',
            r'config\.py$',
            r'settings\.py$'
        ]
        
        python_files = self._get_python_files(layer_path)
        
        # 按优先级排序
        for pattern in priority_patterns:
            for file_path in python_files:
                if re.search(pattern, file_path.name):
                    relative_path = file_path.relative_to(layer_path)
                    key_files.append(str(relative_path))
        
        # 添加其他重要文件
        for file_path in python_files:
            relative_path = file_path.relative_to(layer_path)
            if str(relative_path) not in key_files and len(key_files) < 10:
                key_files.append(str(relative_path))
        
        return key_files
    
    def analyze_subdirectories(self, layer_path: str) -> Dict[str, str]:
        """
        分析子目录结构和用途
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            子目录名称到描述的映射
        """
        layer_path = Path(layer_path)
        subdirs = {}
        
        for item in layer_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name != '__pycache__':
                description = self._get_directory_description(item)
                subdirs[item.name] = description
        
        return subdirs
    
    def scan_directory_structure(self, layer_path: str) -> Dict[str, any]:
        """
        扫描目录结构并生成层级化数据
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            包含目录结构信息的字典
        """
        layer_path = Path(layer_path)
        
        if not layer_path.exists():
            raise ValueError(f"目录不存在: {layer_path}")
        
        structure_data = {
            'name': layer_path.name,
            'path': str(layer_path),
            'type': 'directory',
            'size': self._get_directory_size(layer_path),
            'file_count': self._count_files_recursive(layer_path),
            'subdirectory_count': self._count_subdirectories(layer_path),
            'children': [],
            'file_types': self._analyze_file_types(layer_path),
            'key_files': self._identify_key_files(layer_path),
            'last_modified': self._get_last_modified(layer_path)
        }
        
        # 递归扫描子项目
        structure_data['children'] = self._scan_children(layer_path, max_depth=3)
        
        return structure_data
    
    def generate_directory_tree(self, layer_path: str, max_depth: int = 3, show_details: bool = False) -> str:
        """
        生成目录树结构
        
        Args:
            layer_path: 层级目录路径
            max_depth: 最大深度
            show_details: 是否显示详细信息（文件大小、类型等）
            
        Returns:
            目录树字符串
        """
        layer_path = Path(layer_path)
        tree_lines = []
        
        def _build_tree(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return
            
            items = sorted([item for item in path.iterdir() 
                          if not item.name.startswith('.') and item.name != '__pycache__'])
            
            # 分离目录和文件，目录优先显示
            directories = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]
            sorted_items = directories + files
            
            for i, item in enumerate(sorted_items):
                is_last = i == len(sorted_items) - 1
                current_prefix = "└── " if is_last else "├── "
                
                # 构建显示名称
                display_name = item.name
                if show_details:
                    if item.is_file():
                        file_size = self._format_file_size(item.stat().st_size)
                        file_type = self._get_file_type(item)
                        display_name += f" ({file_size}, {file_type})"
                    else:
                        file_count = self._count_files_in_directory(item)
                        display_name += f" ({file_count} files)"
                
                tree_lines.append(f"{prefix}{current_prefix}{display_name}")
                
                if item.is_dir() and depth < max_depth:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    _build_tree(item, next_prefix, depth + 1)
        
        # 添加根目录信息
        root_info = f"{layer_path.name}/"
        if show_details:
            total_files = self._count_files_recursive(layer_path)
            total_size = self._format_file_size(self._get_directory_size(layer_path))
            root_info += f" ({total_files} files, {total_size})"
        
        tree_lines.append(root_info)
        _build_tree(layer_path)
        
        return "\n".join(tree_lines)
    
    def _get_python_files(self, directory: Path) -> List[Path]:
        """获取目录下所有Python文件"""
        python_files = []
        for root, dirs, files in os.walk(directory):
            # 跳过隐藏目录和缓存目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if any(file.endswith(ext) for ext in self.python_extensions):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def _get_documentation_files(self, directory: Path) -> List[Path]:
        """获取目录下所有文档文件"""
        doc_files = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.doc_extensions):
                    doc_files.append(Path(root) / file)
        
        return doc_files
    
    def _analyze_file_dependencies(self, file_path: Path) -> Dict[str, any]:
        """分析单个文件的依赖关系"""
        result = {
            'imports': set(),
            'from_imports': {},
            'function_calls': [],
            'class_usage': [],
            'import_statements': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 分析导入语句
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        result['imports'].add(module_name)
                        result['import_statements'].append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        result['imports'].add(module_name)
                        
                        # 记录from import的详细信息
                        imported_items = [alias.name for alias in node.names]
                        if module_name not in result['from_imports']:
                            result['from_imports'][module_name] = []
                        result['from_imports'][module_name].extend(imported_items)
                        
                        result['import_statements'].append({
                            'type': 'from_import',
                            'module': node.module,
                            'items': imported_items,
                            'line': node.lineno
                        })
            
            # 分析函数调用和类使用
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._extract_function_name(node.func)
                    if func_name:
                        result['function_calls'].append(func_name)
                
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    # 可能的类使用
                    if node.id[0].isupper():  # 简单的类名检测
                        result['class_usage'].append(node.id)
        
        except Exception as e:
            # 如果AST解析失败，尝试正则表达式
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 基本的import匹配
                import_patterns = [
                    (r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import', 'from_import'),
                    (r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)', 'import')
                ]
                
                for pattern, import_type in import_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        module_name = match.split('.')[0]
                        result['imports'].add(module_name)
            
            except Exception:
                pass
        
        return result
    
    def _filter_project_dependencies(self, dependencies: Set[str]) -> Set[str]:
        """过滤出项目内的层级依赖"""
        project_layers = {
            'core', 'data', 'api', 'strategies', 'user_strategies',
            'analysis', 'services', 'utils', 'config', 'optimization', 'docs'
        }
        
        return dependencies.intersection(project_layers)
    
    def _identify_file_design_patterns(self, file_path: Path) -> Dict[str, Dict[str, any]]:
        """识别文件中的设计模式"""
        patterns = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 单例模式检测
            singleton_evidence = self._detect_singleton_pattern(content, tree)
            if singleton_evidence:
                patterns['单例模式'] = {
                    'confidence': singleton_evidence['confidence'],
                    'evidence': singleton_evidence['evidence'],
                    'description': '确保类只有一个实例并提供全局访问点'
                }
            
            # 工厂模式检测
            factory_evidence = self._detect_factory_pattern(content, tree)
            if factory_evidence:
                patterns['工厂模式'] = {
                    'confidence': factory_evidence['confidence'],
                    'evidence': factory_evidence['evidence'],
                    'description': '创建对象而不指定具体类'
                }
            
            # 策略模式检测
            strategy_evidence = self._detect_strategy_pattern(content, tree)
            if strategy_evidence:
                patterns['策略模式'] = {
                    'confidence': strategy_evidence['confidence'],
                    'evidence': strategy_evidence['evidence'],
                    'description': '定义算法族并使它们可互换'
                }
            
            # 观察者模式检测
            observer_evidence = self._detect_observer_pattern(content, tree)
            if observer_evidence:
                patterns['观察者模式'] = {
                    'confidence': observer_evidence['confidence'],
                    'evidence': observer_evidence['evidence'],
                    'description': '定义对象间一对多的依赖关系'
                }
            
            # 抽象基类模式检测
            abc_evidence = self._detect_abstract_base_class_pattern(content, tree)
            if abc_evidence:
                patterns['抽象基类模式'] = {
                    'confidence': abc_evidence['confidence'],
                    'evidence': abc_evidence['evidence'],
                    'description': '定义接口和抽象方法'
                }
            
            # 装饰器模式检测
            decorator_evidence = self._detect_decorator_pattern(content, tree)
            if decorator_evidence:
                patterns['装饰器模式'] = {
                    'confidence': decorator_evidence['confidence'],
                    'evidence': decorator_evidence['evidence'],
                    'description': '动态地给对象添加新功能'
                }
            
            # 适配器模式检测
            adapter_evidence = self._detect_adapter_pattern(content, tree)
            if adapter_evidence:
                patterns['适配器模式'] = {
                    'confidence': adapter_evidence['confidence'],
                    'evidence': adapter_evidence['evidence'],
                    'description': '使不兼容的接口能够协同工作'
                }
            
            # 建造者模式检测
            builder_evidence = self._detect_builder_pattern(content, tree)
            if builder_evidence:
                patterns['建造者模式'] = {
                    'confidence': builder_evidence['confidence'],
                    'evidence': builder_evidence['evidence'],
                    'description': '分步骤构建复杂对象'
                }
        
        except Exception:
            pass
        
        return patterns
    
    def _extract_function_name(self, node) -> Optional[str]:
        """从AST节点提取函数名"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._extract_function_name(node.value)}.{node.attr}" if node.value else node.attr
        return None
    
    def _analyze_inter_layer_calls(self, layer_path: Path, python_files: List[Path]) -> Dict[str, List[str]]:
        """分析层级间的调用关系"""
        inter_layer_calls = {}
        layer_name = layer_path.name
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找对其他层级的调用
                other_layers = ['core', 'data', 'api', 'strategies', 'user_strategies', 
                              'analysis', 'services', 'utils', 'config', 'optimization', 'docs']
                
                for other_layer in other_layers:
                    if other_layer != layer_name:
                        # 查找对其他层级的引用
                        pattern = rf'\b{other_layer}\.'
                        if re.search(pattern, content):
                            relative_path = str(file_path.relative_to(layer_path))
                            if relative_path not in inter_layer_calls:
                                inter_layer_calls[relative_path] = []
                            inter_layer_calls[relative_path].append(other_layer)
            
            except Exception:
                continue
        
        return inter_layer_calls
    
    def _calculate_dependency_strength(self, dependency_graph: Dict) -> Dict[str, int]:
        """计算依赖强度"""
        strength = {}
        
        for file_path, deps in dependency_graph.items():
            total_deps = len(deps['internal']) + len(deps['external'])
            strength[file_path] = total_deps
        
        return strength
    
    def _detect_circular_dependencies(self, dependency_graph: Dict) -> List[List[str]]:
        """检测循环依赖"""
        # 简化的循环依赖检测
        circular_deps = []
        
        # 这里实现一个简单的循环检测算法
        # 在实际项目中可能需要更复杂的图算法
        
        return circular_deps
    
    def _get_most_dependent_files(self, file_dependencies: Dict) -> List[Dict[str, any]]:
        """获取依赖最多的文件"""
        file_scores = []
        
        for file_path, deps in file_dependencies.items():
            total_deps = len(deps['imports'])
            file_scores.append({
                'file': file_path,
                'dependency_count': total_deps,
                'internal_deps': len(self._filter_project_dependencies(deps['imports'])),
                'external_deps': total_deps - len(self._filter_project_dependencies(deps['imports']))
            })
        
        # 按依赖数量排序
        file_scores.sort(key=lambda x: x['dependency_count'], reverse=True)
        return file_scores[:5]
    
    def _calculate_coupling_score(self, dependency_graph: Dict) -> float:
        """计算耦合度评分"""
        if not dependency_graph:
            return 0.0
        
        total_internal_deps = 0
        total_files = len(dependency_graph)
        
        for deps in dependency_graph.values():
            total_internal_deps += len(deps['internal'])
        
        # 简单的耦合度计算：平均每个文件的内部依赖数
        return total_internal_deps / total_files if total_files > 0 else 0.0
    
    def _detect_singleton_pattern(self, content: str, tree: ast.AST) -> Optional[Dict[str, any]]:
        """检测单例模式"""
        evidence = []
        confidence = 0.0
        
        # 检查常见的单例实现特征
        if '_instance' in content:
            evidence.append('使用_instance类变量')
            confidence += 0.3
        
        if '__new__' in content:
            evidence.append('重写__new__方法')
            confidence += 0.4
        
        if re.search(r'class.*Singleton', content, re.IGNORECASE):
            evidence.append('类名包含Singleton')
            confidence += 0.3
        
        # 检查单例装饰器
        if '@singleton' in content.lower():
            evidence.append('使用singleton装饰器')
            confidence += 0.5
        
        return {'confidence': min(confidence, 1.0), 'evidence': evidence} if evidence else None
    
    def _detect_factory_pattern(self, content: str, tree: ast.AST) -> Optional[Dict[str, any]]:
        """检测工厂模式"""
        evidence = []
        confidence = 0.0
        
        # 检查工厂方法特征
        if re.search(r'def\s+create_', content):
            evidence.append('包含create_开头的方法')
            confidence += 0.4
        
        if re.search(r'class.*Factory', content, re.IGNORECASE):
            evidence.append('类名包含Factory')
            confidence += 0.4
        
        if 'def make_' in content:
            evidence.append('包含make_开头的方法')
            confidence += 0.3
        
        # 检查抽象工厂特征
        if 'AbstractFactory' in content:
            evidence.append('使用AbstractFactory')
            confidence += 0.5
        
        return {'confidence': min(confidence, 1.0), 'evidence': evidence} if evidence else None
    
    def _detect_strategy_pattern(self, content: str, tree: ast.AST) -> Optional[Dict[str, any]]:
        """检测策略模式"""
        evidence = []
        confidence = 0.0
        
        # 检查策略模式特征
        if re.search(r'class.*Strategy', content, re.IGNORECASE):
            evidence.append('类名包含Strategy')
            confidence += 0.4
        
        if 'def execute' in content:
            evidence.append('包含execute方法')
            confidence += 0.3
        
        if 'def algorithm' in content:
            evidence.append('包含algorithm方法')
            confidence += 0.3
        
        # 检查策略接口
        if '@abstractmethod' in content and 'execute' in content:
            evidence.append('定义抽象的execute方法')
            confidence += 0.4
        
        return {'confidence': min(confidence, 1.0), 'evidence': evidence} if evidence else None
    
    def _detect_observer_pattern(self, content: str, tree: ast.AST) -> Optional[Dict[str, any]]:
        """检测观察者模式"""
        evidence = []
        confidence = 0.0
        
        # 检查观察者模式特征
        if 'def notify' in content:
            evidence.append('包含notify方法')
            confidence += 0.4
        
        if 'def subscribe' in content or 'def unsubscribe' in content:
            evidence.append('包含订阅/取消订阅方法')
            confidence += 0.4
        
        if re.search(r'class.*Observer', content, re.IGNORECASE):
            evidence.append('类名包含Observer')
            confidence += 0.3
        
        if 'observers' in content.lower():
            evidence.append('包含observers变量')
            confidence += 0.3
        
        return {'confidence': min(confidence, 1.0), 'evidence': evidence} if evidence else None
    
    def _detect_abstract_base_class_pattern(self, content: str, tree: ast.AST) -> Optional[Dict[str, any]]:
        """检测抽象基类模式"""
        evidence = []
        confidence = 0.0
        
        # 检查ABC特征
        if 'from abc import' in content or 'import abc' in content:
            evidence.append('导入abc模块')
            confidence += 0.4
        
        if '@abstractmethod' in content:
            evidence.append('使用@abstractmethod装饰器')
            confidence += 0.5
        
        if 'ABC' in content:
            evidence.append('继承ABC类')
            confidence += 0.4
        
        if re.search(r'class.*Base', content, re.IGNORECASE):
            evidence.append('类名包含Base')
            confidence += 0.2
        
        return {'confidence': min(confidence, 1.0), 'evidence': evidence} if evidence else None
    
    def _detect_decorator_pattern(self, content: str, tree: ast.AST) -> Optional[Dict[str, any]]:
        """检测装饰器模式"""
        evidence = []
        confidence = 0.0
        
        # 检查装饰器特征
        if re.search(r'def\s+\w+\s*\([^)]*\)\s*:', content) and 'def wrapper' in content:
            evidence.append('包含wrapper函数')
            confidence += 0.4
        
        if '@' in content and 'def ' in content:
            evidence.append('使用装饰器语法')
            confidence += 0.3
        
        if 'functools.wraps' in content:
            evidence.append('使用functools.wraps')
            confidence += 0.4
        
        if re.search(r'class.*Decorator', content, re.IGNORECASE):
            evidence.append('类名包含Decorator')
            confidence += 0.3
        
        return {'confidence': min(confidence, 1.0), 'evidence': evidence} if evidence else None
    
    def _detect_adapter_pattern(self, content: str, tree: ast.AST) -> Optional[Dict[str, any]]:
        """检测适配器模式"""
        evidence = []
        confidence = 0.0
        
        # 检查适配器特征
        if re.search(r'class.*Adapter', content, re.IGNORECASE):
            evidence.append('类名包含Adapter')
            confidence += 0.4
        
        if 'def adapt' in content:
            evidence.append('包含adapt方法')
            confidence += 0.3
        
        if 'adaptee' in content.lower():
            evidence.append('包含adaptee变量')
            confidence += 0.3
        
        return {'confidence': min(confidence, 1.0), 'evidence': evidence} if evidence else None
    
    def _detect_builder_pattern(self, content: str, tree: ast.AST) -> Optional[Dict[str, any]]:
        """检测建造者模式"""
        evidence = []
        confidence = 0.0
        
        # 检查建造者特征
        if re.search(r'class.*Builder', content, re.IGNORECASE):
            evidence.append('类名包含Builder')
            confidence += 0.4
        
        if 'def build' in content:
            evidence.append('包含build方法')
            confidence += 0.4
        
        if re.search(r'def\s+with_\w+', content):
            evidence.append('包含with_开头的方法')
            confidence += 0.3
        
        if 'def reset' in content:
            evidence.append('包含reset方法')
            confidence += 0.2
        
        return {'confidence': min(confidence, 1.0), 'evidence': evidence} if evidence else None
    
    def _identify_architectural_patterns(self, layer_path: Path, python_files: List[Path]) -> Dict[str, any]:
        """识别架构模式"""
        patterns = {}
        
        # 分层架构检测
        if self._detect_layered_architecture(layer_path):
            patterns['分层架构'] = {
                'confidence': 0.8,
                'evidence': ['目录结构体现分层设计'],
                'description': '将系统组织成层次结构，每层只与相邻层交互'
            }
        
        # MVC模式检测
        mvc_evidence = self._detect_mvc_pattern(layer_path, python_files)
        if mvc_evidence:
            patterns['MVC模式'] = mvc_evidence
        
        # 微服务架构检测
        microservice_evidence = self._detect_microservice_pattern(layer_path, python_files)
        if microservice_evidence:
            patterns['微服务架构'] = microservice_evidence
        
        # 仓储模式检测
        repository_evidence = self._detect_repository_pattern(python_files)
        if repository_evidence:
            patterns['仓储模式'] = repository_evidence
        
        return patterns
    
    def _detect_layered_architecture(self, layer_path: Path) -> bool:
        """检测分层架构"""
        # 检查是否存在典型的分层结构
        layer_indicators = ['api', 'service', 'data', 'core', 'utils']
        parent_dir = layer_path.parent
        
        existing_layers = 0
        for indicator in layer_indicators:
            if (parent_dir / indicator).exists():
                existing_layers += 1
        
        return existing_layers >= 3
    
    def _detect_mvc_pattern(self, layer_path: Path, python_files: List[Path]) -> Optional[Dict[str, any]]:
        """检测MVC模式"""
        evidence = []
        confidence = 0.0
        
        # 检查是否有model, view, controller相关文件
        has_model = any('model' in str(f).lower() for f in python_files)
        has_view = any('view' in str(f).lower() for f in python_files)
        has_controller = any('controller' in str(f).lower() or 'handler' in str(f).lower() for f in python_files)
        
        if has_model:
            evidence.append('包含模型相关文件')
            confidence += 0.3
        if has_view:
            evidence.append('包含视图相关文件')
            confidence += 0.3
        if has_controller:
            evidence.append('包含控制器相关文件')
            confidence += 0.4
        
        return {'confidence': confidence, 'evidence': evidence, 'description': '分离数据、视图和控制逻辑'} if evidence else None
    
    def _detect_microservice_pattern(self, layer_path: Path, python_files: List[Path]) -> Optional[Dict[str, any]]:
        """检测微服务架构"""
        evidence = []
        confidence = 0.0
        
        # 检查API相关特征
        has_api = any('api' in str(f).lower() for f in python_files)
        has_service = any('service' in str(f).lower() for f in python_files)
        has_routes = any('route' in str(f).lower() for f in python_files)
        
        if has_api and has_service:
            evidence.append('包含API和服务层')
            confidence += 0.4
        if has_routes:
            evidence.append('包含路由定义')
            confidence += 0.3
        
        return {'confidence': confidence, 'evidence': evidence, 'description': '将应用拆分为独立的服务'} if evidence else None
    
    def _detect_repository_pattern(self, python_files: List[Path]) -> Optional[Dict[str, any]]:
        """检测仓储模式"""
        evidence = []
        confidence = 0.0
        
        # 检查仓储模式特征
        has_repository = any('repository' in str(f).lower() for f in python_files)
        has_dao = any('dao' in str(f).lower() for f in python_files)
        
        if has_repository:
            evidence.append('包含Repository类')
            confidence += 0.5
        if has_dao:
            evidence.append('包含DAO类')
            confidence += 0.4
        
        return {'confidence': confidence, 'evidence': evidence, 'description': '封装数据访问逻辑'} if evidence else None
    
    def _analyze_architectural_decisions(self, layer_path: Path, python_files: List[Path]) -> List[Dict[str, any]]:
        """分析关键架构决策"""
        decisions = []
        
        # 分析技术栈选择
        tech_stack = self._analyze_tech_stack(python_files)
        if tech_stack:
            decisions.append({
                'decision': '技术栈选择',
                'details': tech_stack,
                'rationale': '基于项目需求和团队技能选择合适的技术栈'
            })
        
        # 分析数据存储策略
        storage_strategy = self._analyze_storage_strategy(python_files)
        if storage_strategy:
            decisions.append({
                'decision': '数据存储策略',
                'details': storage_strategy,
                'rationale': '根据数据特性和访问模式选择存储方案'
            })
        
        # 分析错误处理策略
        error_handling = self._analyze_error_handling_strategy(python_files)
        if error_handling:
            decisions.append({
                'decision': '错误处理策略',
                'details': error_handling,
                'rationale': '确保系统的健壮性和可维护性'
            })
        
        return decisions
    
    def _analyze_tech_stack(self, python_files: List[Path]) -> List[str]:
        """分析技术栈"""
        tech_stack = []
        
        # 分析常见的Python库使用
        common_libs = {
            'fastapi': 'FastAPI Web框架',
            'flask': 'Flask Web框架',
            'django': 'Django Web框架',
            'sqlalchemy': 'SQLAlchemy ORM',
            'pandas': 'Pandas数据处理',
            'numpy': 'NumPy数值计算',
            'requests': 'HTTP请求库',
            'asyncio': '异步编程',
            'pytest': '测试框架'
        }
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for lib, description in common_libs.items():
                    if lib in content.lower() and description not in tech_stack:
                        tech_stack.append(description)
            except Exception:
                continue
        
        return tech_stack
    
    def _analyze_storage_strategy(self, python_files: List[Path]) -> List[str]:
        """分析存储策略"""
        strategies = []
        
        storage_indicators = {
            'sqlite': 'SQLite轻量级数据库',
            'postgresql': 'PostgreSQL关系数据库',
            'mysql': 'MySQL关系数据库',
            'redis': 'Redis缓存数据库',
            'mongodb': 'MongoDB文档数据库',
            'json': 'JSON文件存储',
            'csv': 'CSV文件存储'
        }
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                for indicator, description in storage_indicators.items():
                    if indicator in content and description not in strategies:
                        strategies.append(description)
            except Exception:
                continue
        
        return strategies
    
    def _analyze_error_handling_strategy(self, python_files: List[Path]) -> List[str]:
        """分析错误处理策略"""
        strategies = []
        
        error_patterns = {
            'try:': '异常捕获处理',
            'logging': '日志记录',
            'raise': '异常抛出',
            'assert': '断言检查',
            'ValidationError': '数据验证',
            'HTTPException': 'HTTP异常处理'
        }
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in error_patterns.items():
                    if pattern in content and description not in strategies:
                        strategies.append(description)
            except Exception:
                continue
        
        return strategies
    
    def _get_most_common_patterns(self, design_patterns: Dict) -> List[Dict[str, any]]:
        """获取最常见的设计模式"""
        pattern_scores = []
        
        for pattern_name, pattern_info in design_patterns.items():
            score = len(pattern_info['files']) * pattern_info['confidence']
            pattern_scores.append({
                'pattern': pattern_name,
                'file_count': len(pattern_info['files']),
                'confidence': pattern_info['confidence'],
                'score': score
            })
        
        pattern_scores.sort(key=lambda x: x['score'], reverse=True)
        return pattern_scores[:5]
    
    def _calculate_pattern_complexity(self, design_patterns: Dict) -> float:
        """计算模式复杂度评分"""
        if not design_patterns:
            return 0.0
        
        total_score = 0.0
        pattern_weights = {
            '单例模式': 1.0,
            '工厂模式': 2.0,
            '策略模式': 2.5,
            '观察者模式': 3.0,
            '装饰器模式': 2.0,
            '适配器模式': 2.5,
            '建造者模式': 3.0,
            '抽象基类模式': 2.0
        }
        
        for pattern_name, pattern_info in design_patterns.items():
            weight = pattern_weights.get(pattern_name, 1.0)
            score = weight * pattern_info['confidence'] * len(pattern_info['files'])
            total_score += score
        
        return total_score / len(design_patterns)
    
    def _analyze_file_complexity(self, file_path: Path) -> List[str]:
        """分析文件复杂度并生成建议"""
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # 检查文件长度
            if len(lines) > 500:
                suggestions.append(f"文件 {file_path.name} 过长({len(lines)}行)，考虑拆分")
            
            # 检查函数复杂度（简单检查）
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if func_lines > 50:
                        suggestions.append(f"函数 {node.name} 过长，考虑重构")
        
        except Exception:
            pass
        
        return suggestions
    
    def _get_directory_description(self, directory: Path) -> str:
        """获取目录描述"""
        dir_name = directory.name
        
        # 常见目录描述
        descriptions = {
            'tests': '测试文件目录',
            'test': '测试文件目录',
            'models': '数据模型定义',
            'views': '视图层实现',
            'controllers': '控制器层实现',
            'services': '服务层实现',
            'utils': '工具函数',
            'helpers': '辅助函数',
            'config': '配置文件',
            'templates': '模板文件',
            'static': '静态资源',
            'migrations': '数据库迁移',
            'schemas': '数据模式定义',
            'middleware': '中间件',
            'routes': '路由定义',
            'api': 'API接口',
            'core': '核心功能',
            'base': '基础类定义',
            'interfaces': '接口定义',
            'exceptions': '异常定义',
            'constants': '常量定义',
            'enums': '枚举定义'
        }
        
        return descriptions.get(dir_name, f'{dir_name}相关功能')
    
    def _scan_children(self, directory: Path, max_depth: int = 3, current_depth: int = 0) -> List[Dict]:
        """递归扫描子目录和文件"""
        children = []
        
        if current_depth >= max_depth:
            return children
        
        try:
            items = sorted([item for item in directory.iterdir() 
                          if not item.name.startswith('.') and item.name != '__pycache__'])
            
            for item in items:
                child_data = {
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else self._get_directory_size(item),
                    'last_modified': item.stat().st_mtime
                }
                
                if item.is_file():
                    child_data.update({
                        'file_type': self._get_file_type(item),
                        'purpose': self._analyze_file_purpose(item)
                    })
                else:
                    child_data.update({
                        'file_count': self._count_files_in_directory(item),
                        'description': self._get_directory_description(item),
                        'children': self._scan_children(item, max_depth, current_depth + 1)
                    })
                
                children.append(child_data)
        
        except PermissionError:
            pass  # 跳过无权限访问的目录
        
        return children
    
    def _get_directory_size(self, directory: Path) -> int:
        """计算目录总大小"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    try:
                        file_path = Path(root) / file
                        total_size += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        continue
        except (OSError, PermissionError):
            pass
        return total_size
    
    def _count_files_recursive(self, directory: Path) -> int:
        """递归计算目录中的文件数量"""
        count = 0
        try:
            for root, dirs, files in os.walk(directory):
                # 跳过隐藏目录和缓存目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                count += len([f for f in files if not f.startswith('.')])
        except (OSError, PermissionError):
            pass
        return count
    
    def _count_subdirectories(self, directory: Path) -> int:
        """计算直接子目录数量"""
        count = 0
        try:
            for item in directory.iterdir():
                if item.is_dir() and not item.name.startswith('.') and item.name != '__pycache__':
                    count += 1
        except (OSError, PermissionError):
            pass
        return count
    
    def _count_files_in_directory(self, directory: Path) -> int:
        """计算目录中的直接文件数量"""
        count = 0
        try:
            for item in directory.iterdir():
                if item.is_file() and not item.name.startswith('.'):
                    count += 1
        except (OSError, PermissionError):
            pass
        return count
    
    def _analyze_file_types(self, directory: Path) -> Dict[str, int]:
        """分析目录中的文件类型分布"""
        file_types = {}
        try:
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                for file in files:
                    if not file.startswith('.'):
                        ext = Path(file).suffix.lower()
                        if not ext:
                            ext = 'no_extension'
                        file_types[ext] = file_types.get(ext, 0) + 1
        except (OSError, PermissionError):
            pass
        return file_types
    
    def _identify_key_files(self, directory: Path) -> List[str]:
        """识别目录中的关键文件"""
        key_files = []
        key_patterns = [
            r'__init__\.py$',
            r'main\.py$',
            r'app\.py$',
            r'.*_manager\.py$',
            r'.*_service\.py$',
            r'.*_interface\.py$',
            r'.*_base\.py$',
            r'config\.py$',
            r'settings\.py$',
            r'README\.md$',
            r'requirements\.txt$',
            r'setup\.py$'
        ]
        
        try:
            for item in directory.iterdir():
                if item.is_file():
                    for pattern in key_patterns:
                        if re.search(pattern, item.name, re.IGNORECASE):
                            key_files.append(item.name)
                            break
        except (OSError, PermissionError):
            pass
        
        return key_files
    
    def _get_last_modified(self, path: Path) -> float:
        """获取路径的最后修改时间"""
        try:
            return path.stat().st_mtime
        except (OSError, FileNotFoundError):
            return 0.0
    
    def _get_file_type(self, file_path: Path) -> str:
        """获取文件类型描述"""
        ext = file_path.suffix.lower()
        
        type_mapping = {
            '.py': 'Python源码',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.json': 'JSON配置',
            '.yaml': 'YAML配置',
            '.yml': 'YAML配置',
            '.toml': 'TOML配置',
            '.ini': 'INI配置',
            '.md': 'Markdown文档',
            '.rst': 'reStructuredText文档',
            '.txt': '文本文件',
            '.log': '日志文件',
            '.sql': 'SQL脚本',
            '.html': 'HTML文件',
            '.css': 'CSS样式',
            '.xml': 'XML文件',
            '.csv': 'CSV数据',
            '.db': '数据库文件',
            '.sqlite': 'SQLite数据库'
        }
        
        return type_mapping.get(ext, f'{ext[1:].upper()}文件' if ext else '未知类型')
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def _analyze_file_purpose(self, file_path: Path) -> str:
        """分析文件用途"""
        file_name = file_path.name.lower()
        
        # 基于文件名模式分析用途
        purpose_patterns = {
            r'__init__\.py$': '模块初始化文件',
            r'main\.py$': '程序入口文件',
            r'app\.py$': '应用程序主文件',
            r'.*_test\.py$': '单元测试文件',
            r'test_.*\.py$': '单元测试文件',
            r'.*_manager\.py$': '管理器类文件',
            r'.*_service\.py$': '服务类文件',
            r'.*_interface\.py$': '接口定义文件',
            r'.*_base\.py$': '基础类文件',
            r'.*_model\.py$': '数据模型文件',
            r'.*_schema\.py$': '数据模式文件',
            r'.*_config\.py$': '配置文件',
            r'.*_utils\.py$': '工具函数文件',
            r'.*_helper\.py$': '辅助函数文件',
            r'.*_exception\.py$': '异常定义文件',
            r'.*_constant\.py$': '常量定义文件',
            r'requirements\.txt$': 'Python依赖文件',
            r'setup\.py$': 'Python安装脚本',
            r'README\.md$': '项目说明文档',
            r'.*\.json$': 'JSON配置文件',
            r'.*\.yaml$': 'YAML配置文件',
            r'.*\.yml$': 'YAML配置文件',
            r'.*\.log$': '日志文件'
        }
        
        for pattern, purpose in purpose_patterns.items():
            if re.search(pattern, file_name):
                return purpose
        
        # 基于文件扩展名的通用用途
        ext = file_path.suffix.lower()
        ext_purposes = {
            '.py': 'Python源码文件',
            '.js': 'JavaScript脚本文件',
            '.html': 'HTML页面文件',
            '.css': 'CSS样式文件',
            '.sql': 'SQL脚本文件',
            '.md': 'Markdown文档文件',
            '.txt': '文本文档文件'
        }
        
        return ext_purposes.get(ext, '通用文件')
    
    def analyze_layer_files(self, layer_path: str) -> Dict[str, any]:
        """
        分析层级中所有文件的用途和特征
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            包含文件分析结果的字典
        """
        layer_path = Path(layer_path)
        
        if not layer_path.exists():
            raise ValueError(f"层级目录不存在: {layer_path}")
        
        # 分析所有文件
        file_analyses = self.file_purpose_analyzer.analyze_directory_files(layer_path)
        
        # 递归分析子目录
        subdirectory_analyses = {}
        for item in layer_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name != '__pycache__':
                try:
                    subdir_analyses = self.file_purpose_analyzer.analyze_directory_files(item)
                    if subdir_analyses:
                        subdirectory_analyses[item.name] = {
                            'files': subdir_analyses,
                            'summary': self.file_purpose_analyzer.generate_file_summary(subdir_analyses)
                        }
                except Exception as e:
                    print(f"分析子目录 {item} 时出错: {e}")
        
        # 生成摘要
        summary = self.file_purpose_analyzer.generate_file_summary(file_analyses)
        
        return {
            'layer_name': layer_path.name,
            'root_files': file_analyses,
            'subdirectories': subdirectory_analyses,
            'summary': summary,
            'analysis_timestamp': self._get_last_modified(layer_path)
        }
    
    def generate_file_purpose_report(self, layer_path: str) -> str:
        """
        生成文件用途分析报告
        
        Args:
            layer_path: 层级目录路径
            
        Returns:
            Markdown格式的分析报告
        """
        analysis_data = self.analyze_layer_files(layer_path)
        
        report_lines = []
        report_lines.append(f"# {analysis_data['layer_name']} 层级文件分析报告\n")
        
        # 摘要信息
        summary = analysis_data['summary']
        if summary:
            report_lines.append("## 摘要信息\n")
            report_lines.append(f"- **文件总数**: {summary['total_files']}")
            report_lines.append(f"- **代码总行数**: {summary['total_lines_of_code']}")
            report_lines.append(f"- **平均复杂度**: {summary['average_complexity']}/10")
            
            # 文件类别分布
            if summary['category_distribution']:
                report_lines.append("\n### 文件类别分布\n")
                for category, count in summary['category_distribution'].items():
                    report_lines.append(f"- **{category}**: {count} 个文件")
            
            # 重要文件
            if summary['most_important_files']:
                report_lines.append("\n### 重要文件\n")
                for file_info in summary['most_important_files']:
                    report_lines.append(f"- **{file_info['name']}** ({file_info['category']}) - {file_info['purpose']}")
        
        # 根目录文件详情
        if analysis_data['root_files']:
            report_lines.append("\n## 根目录文件详情\n")
            for file_analysis in analysis_data['root_files']:
                report_lines.append(f"### {file_analysis.name}\n")
                report_lines.append(f"- **类别**: {file_analysis.category.value}")
                report_lines.append(f"- **用途**: {file_analysis.purpose}")
                report_lines.append(f"- **描述**: {file_analysis.description}")
                report_lines.append(f"- **复杂度**: {file_analysis.complexity_score}/10")
                report_lines.append(f"- **代码行数**: {file_analysis.lines_of_code}")
                
                if file_analysis.key_classes:
                    report_lines.append(f"- **主要类**: {', '.join(file_analysis.key_classes)}")
                
                if file_analysis.key_functions:
                    functions_str = ', '.join(file_analysis.key_functions[:5])  # 限制显示数量
                    if len(file_analysis.key_functions) > 5:
                        functions_str += f" (共{len(file_analysis.key_functions)}个)"
                    report_lines.append(f"- **主要函数**: {functions_str}")
                
                report_lines.append("")
        
        # 子目录分析
        if analysis_data['subdirectories']:
            report_lines.append("## 子目录分析\n")
            for subdir_name, subdir_data in analysis_data['subdirectories'].items():
                report_lines.append(f"### {subdir_name}/\n")
                
                subdir_summary = subdir_data['summary']
                if subdir_summary:
                    report_lines.append(f"- **文件数量**: {subdir_summary['total_files']}")
                    report_lines.append(f"- **代码行数**: {subdir_summary['total_lines_of_code']}")
                    report_lines.append(f"- **平均复杂度**: {subdir_summary['average_complexity']}/10")
                    
                    # 子目录的文件类别分布
                    if subdir_summary['category_distribution']:
                        categories = ', '.join([f"{cat}({count})" for cat, count in subdir_summary['category_distribution'].items()])
                        report_lines.append(f"- **文件类别**: {categories}")
                
                report_lines.append("")
        
        return "\n".join(report_lines)