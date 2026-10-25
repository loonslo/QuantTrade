"""
文档质量验证器

验证生成的文档的完整性、格式正确性和内容质量。
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ValidationIssueType(Enum):
    """验证问题类型枚举"""
    MISSING_SECTION = "缺少章节"
    EMPTY_SECTION = "空章节"
    INVALID_MARKDOWN = "Markdown格式错误"
    BROKEN_LINK = "链接失效"
    MISSING_METADATA = "缺少元数据"
    CONTENT_TOO_SHORT = "内容过短"
    INCONSISTENT_FORMAT = "格式不一致"


@dataclass
class ValidationIssue:
    """验证问题数据模型"""
    issue_type: ValidationIssueType
    severity: int  # 1-10严重程度
    line_number: int
    description: str
    suggestion: str
    section: str


@dataclass
class DocumentQuality:
    """文档质量指标"""
    completeness_score: float  # 0-1完整性评分
    format_score: float  # 0-1格式评分
    content_score: float  # 0-1内容评分
    overall_score: float  # 0-1总体评分
    total_issues: int
    critical_issues: int


class DocumentValidator:
    """
    文档质量验证器
    
    验证文档的完整性、格式正确性和内容质量。
    """
    
    def __init__(self):
        """初始化文档验证器"""
        self.required_sections = [
            "层级概述",
            "目录结构", 
            "核心功能",
            "架构分析",
            "优化建议",
            "使用指南"
        ]
        
        self.markdown_patterns = {
            'header': r'^#{1,6}\s+.+$',
            'list_item': r'^\s*[-*+]\s+.+$',
            'numbered_list': r'^\s*\d+\.\s+.+$',
            'code_block': r'^```[\w]*$',
            'link': r'\[([^\]]+)\]\(([^)]+)\)',
            'bold': r'\*\*([^*]+)\*\*',
            'italic': r'\*([^*]+)\*'
        }
    
    def validate_document(self, document_content: str, document_path: Optional[str] = None) -> Dict[str, Any]:
        """
        验证文档质量
        
        Args:
            document_content: 文档内容
            document_path: 文档路径（可选）
            
        Returns:
            包含验证结果的字典
        """
        lines = document_content.split('\n')
        
        # 执行各种验证
        validation_issues = []
        validation_issues.extend(self._validate_completeness(lines))
        validation_issues.extend(self._validate_markdown_format(lines))
        validation_issues.extend(self._validate_content_quality(lines))
        validation_issues.extend(self._validate_section_structure(lines))
        
        # 计算质量指标
        quality_metrics = self._calculate_quality_metrics(lines, validation_issues)
        
        # 生成验证摘要
        validation_summary = self._generate_validation_summary(validation_issues, quality_metrics)
        
        return {
            'validation_issues': [self._issue_to_dict(issue) for issue in validation_issues],
            'quality_metrics': self._quality_to_dict(quality_metrics),
            'validation_summary': validation_summary,
            'recommendations': self._generate_recommendations(validation_issues, quality_metrics),
            'is_valid': quality_metrics.overall_score >= 0.7,
            'document_path': document_path
        }
    
    def validate_section_completeness(self, document_content: str) -> bool:
        """
        验证文档章节完整性
        
        Args:
            document_content: 文档内容
            
        Returns:
            是否包含所有必需章节
        """
        content_lower = document_content.lower()
        
        for section in self.required_sections:
            section_patterns = [
                f"#{section.lower()}",
                f"## {section.lower()}",
                f"### {section.lower()}",
                section.lower()
            ]
            
            if not any(pattern in content_lower for pattern in section_patterns):
                return False
        
        return True
    
    def validate_markdown_syntax(self, document_content: str) -> List[ValidationIssue]:
        """
        验证Markdown语法正确性
        
        Args:
            document_content: 文档内容
            
        Returns:
            Markdown语法问题列表
        """
        lines = document_content.split('\n')
        issues = []
        
        code_block_open = False
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # 检查代码块
            if line_stripped.startswith('```'):
                code_block_open = not code_block_open
                continue
            
            # 在代码块内部跳过检查
            if code_block_open:
                continue
            
            # 检查标题格式
            if line_stripped.startswith('#'):
                if not re.match(self.markdown_patterns['header'], line_stripped):
                    issues.append(ValidationIssue(
                        issue_type=ValidationIssueType.INVALID_MARKDOWN,
                        severity=5,
                        line_number=i,
                        description=f"标题格式不正确: {line_stripped[:50]}",
                        suggestion="标题应该以#开头，后跟空格和标题文本",
                        section="格式检查"
                    ))
            
            # 检查列表格式
            if line_stripped.startswith(('-', '*', '+')):
                if not re.match(self.markdown_patterns['list_item'], line_stripped):
                    issues.append(ValidationIssue(
                        issue_type=ValidationIssueType.INVALID_MARKDOWN,
                        severity=3,
                        line_number=i,
                        description=f"列表项格式不正确: {line_stripped[:50]}",
                        suggestion="列表项应该以-、*或+开头，后跟空格",
                        section="格式检查"
                    ))
        
        # 检查未闭合的代码块
        if code_block_open:
            issues.append(ValidationIssue(
                issue_type=ValidationIssueType.INVALID_MARKDOWN,
                severity=8,
                line_number=len(lines),
                description="代码块未正确闭合",
                suggestion="确保每个```都有对应的闭合标记",
                section="格式检查"
            ))
        
        return issues
    
    def _validate_completeness(self, lines: List[str]) -> List[ValidationIssue]:
        """验证文档完整性"""
        issues = []
        content = '\n'.join(lines).lower()
        
        # 检查必需章节
        for section in self.required_sections:
            section_found = False
            section_patterns = [
                f"# {section.lower()}",
                f"## {section.lower()}",
                f"### {section.lower()}"
            ]
            
            for pattern in section_patterns:
                if pattern in content:
                    section_found = True
                    break
            
            if not section_found:
                issues.append(ValidationIssue(
                    issue_type=ValidationIssueType.MISSING_SECTION,
                    severity=8,
                    line_number=1,
                    description=f"缺少必需章节: {section}",
                    suggestion=f"添加 {section} 章节",
                    section="完整性检查"
                ))
        
        return issues
    
    def _validate_markdown_format(self, lines: List[str]) -> List[ValidationIssue]:
        """验证Markdown格式"""
        return self.validate_markdown_syntax('\n'.join(lines))
    
    def _validate_content_quality(self, lines: List[str]) -> List[ValidationIssue]:
        """验证内容质量"""
        issues = []
        
        # 检查文档长度
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) < 20:
            issues.append(ValidationIssue(
                issue_type=ValidationIssueType.CONTENT_TOO_SHORT,
                severity=6,
                line_number=1,
                description=f"文档内容过短，只有 {len(non_empty_lines)} 行有效内容",
                suggestion="增加更多详细说明和示例",
                section="内容质量"
            ))
        
        # 检查空章节
        current_section = None
        section_content_lines = 0
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # 检测章节标题
            if line_stripped.startswith('#'):
                # 检查上一个章节是否为空
                if current_section and section_content_lines == 0:
                    issues.append(ValidationIssue(
                        issue_type=ValidationIssueType.EMPTY_SECTION,
                        severity=7,
                        line_number=i-1,
                        description=f"章节 '{current_section}' 没有内容",
                        suggestion="为章节添加相关内容或删除空章节",
                        section="内容质量"
                    ))
                
                current_section = line_stripped
                section_content_lines = 0
            elif line_stripped:
                section_content_lines += 1
        
        # 检查最后一个章节
        if current_section and section_content_lines == 0:
            issues.append(ValidationIssue(
                issue_type=ValidationIssueType.EMPTY_SECTION,
                severity=7,
                line_number=len(lines),
                description=f"章节 '{current_section}' 没有内容",
                suggestion="为章节添加相关内容或删除空章节",
                section="内容质量"
            ))
        
        return issues
    
    def _validate_section_structure(self, lines: List[str]) -> List[ValidationIssue]:
        """验证章节结构"""
        issues = []
        
        header_levels = []
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            if line_stripped.startswith('#'):
                # 计算标题级别
                level = 0
                for char in line_stripped:
                    if char == '#':
                        level += 1
                    else:
                        break
                
                header_levels.append((i, level))
        
        # 检查标题层级是否合理
        for i in range(1, len(header_levels)):
            prev_line, prev_level = header_levels[i-1]
            curr_line, curr_level = header_levels[i]
            
            # 标题级别跳跃过大
            if curr_level > prev_level + 1:
                issues.append(ValidationIssue(
                    issue_type=ValidationIssueType.INCONSISTENT_FORMAT,
                    severity=4,
                    line_number=curr_line,
                    description=f"标题级别跳跃过大，从 H{prev_level} 跳到 H{curr_level}",
                    suggestion="使用连续的标题级别，避免跳级",
                    section="结构检查"
                ))
        
        return issues
    
    def _calculate_quality_metrics(self, lines: List[str], issues: List[ValidationIssue]) -> DocumentQuality:
        """计算文档质量指标"""
        total_lines = len([line for line in lines if line.strip()])
        
        # 完整性评分
        missing_sections = len([issue for issue in issues 
                              if issue.issue_type == ValidationIssueType.MISSING_SECTION])
        completeness_score = max(0, 1 - (missing_sections / len(self.required_sections)))
        
        # 格式评分
        format_issues = len([issue for issue in issues 
                           if issue.issue_type in [ValidationIssueType.INVALID_MARKDOWN, 
                                                 ValidationIssueType.INCONSISTENT_FORMAT]])
        format_score = max(0, 1 - (format_issues / max(total_lines / 10, 1)))
        
        # 内容评分
        content_issues = len([issue for issue in issues 
                            if issue.issue_type in [ValidationIssueType.EMPTY_SECTION,
                                                   ValidationIssueType.CONTENT_TOO_SHORT]])
        content_score = max(0, 1 - (content_issues / max(len(self.required_sections), 1)))
        
        # 总体评分
        overall_score = (completeness_score * 0.4 + format_score * 0.3 + content_score * 0.3)
        
        # 统计问题数量
        critical_issues = len([issue for issue in issues if issue.severity >= 7])
        
        return DocumentQuality(
            completeness_score=completeness_score,
            format_score=format_score,
            content_score=content_score,
            overall_score=overall_score,
            total_issues=len(issues),
            critical_issues=critical_issues
        )
    
    def _generate_validation_summary(self, issues: List[ValidationIssue], 
                                   quality_metrics: DocumentQuality) -> Dict[str, Any]:
        """生成验证摘要"""
        # 按问题类型分组
        issue_type_counts = {}
        for issue in issues:
            issue_type = issue.issue_type.value
            issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + 1
        
        # 按严重程度分组
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        return {
            'overall_quality': self._get_quality_level(quality_metrics.overall_score),
            'completeness_quality': self._get_quality_level(quality_metrics.completeness_score),
            'format_quality': self._get_quality_level(quality_metrics.format_score),
            'content_quality': self._get_quality_level(quality_metrics.content_score),
            'issue_type_distribution': issue_type_counts,
            'severity_distribution': severity_counts,
            'validation_passed': quality_metrics.overall_score >= 0.7
        }
    
    def _generate_recommendations(self, issues: List[ValidationIssue], 
                                quality_metrics: DocumentQuality) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于质量指标的建议
        if quality_metrics.completeness_score < 0.8:
            recommendations.append("补充缺失的文档章节以提高完整性")
        
        if quality_metrics.format_score < 0.8:
            recommendations.append("修复Markdown格式问题以提高可读性")
        
        if quality_metrics.content_score < 0.8:
            recommendations.append("丰富章节内容，避免空章节")
        
        # 基于高优先级问题的建议
        critical_issues = [issue for issue in issues if issue.severity >= 7]
        for issue in critical_issues[:3]:  # 前3个最严重的问题
            recommendations.append(f"修复{issue.issue_type.value}: {issue.suggestion}")
        
        # 通用建议
        if quality_metrics.overall_score < 0.5:
            recommendations.append("文档质量较低，建议全面重写")
        elif quality_metrics.overall_score < 0.7:
            recommendations.append("文档需要改进，重点关注内容完整性和格式规范")
        
        return recommendations[:5]  # 限制建议数量
    
    def _get_quality_level(self, score: float) -> str:
        """获取质量等级描述"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.8:
            return "良好"
        elif score >= 0.7:
            return "合格"
        elif score >= 0.5:
            return "需要改进"
        else:
            return "不合格"
    
    def _issue_to_dict(self, issue: ValidationIssue) -> Dict[str, Any]:
        """将验证问题转换为字典"""
        return {
            'issue_type': issue.issue_type.value,
            'severity': issue.severity,
            'line_number': issue.line_number,
            'description': issue.description,
            'suggestion': issue.suggestion,
            'section': issue.section
        }
    
    def _quality_to_dict(self, quality: DocumentQuality) -> Dict[str, Any]:
        """将质量指标转换为字典"""
        return {
            'completeness_score': round(quality.completeness_score, 3),
            'format_score': round(quality.format_score, 3),
            'content_score': round(quality.content_score, 3),
            'overall_score': round(quality.overall_score, 3),
            'total_issues': quality.total_issues,
            'critical_issues': quality.critical_issues
        }