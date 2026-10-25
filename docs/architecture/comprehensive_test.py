#!/usr/bin/env python3
"""
全面测试文档生成核心功能

验证任务1的所有要求：
- 集成可维护性评估器和性能优化器到主文档生成流程
- 实现文档质量验证机制
- 添加错误处理和日志记录
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_maintainability_integration():
    """测试可维护性评估器集成"""
    print("1. 测试可维护性评估器集成...")
    
    try:
        from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator
        
        generator = DocumentationGenerator(str(project_root))
        
        # 直接测试可维护性评估器
        maintainability_result = generator.maintainability_evaluator.evaluate_maintainability(str(project_root / 'utils'))
        
        # 验证返回结果包含必要字段
        required_fields = ['maintainability_issues', 'complexity_metrics', 'coupling_metrics', 'maintainability_summary']
        for field in required_fields:
            assert field in maintainability_result, f"缺少字段: {field}"
        
        print("✓ 可维护性评估器集成成功")
        print(f"  - 发现问题: {maintainability_result['maintainability_summary']['total_issues']} 个")
        print(f"  - 总体评分: {maintainability_result['maintainability_score']:.2f}/10")
        
        return True
        
    except Exception as e:
        print(f"✗ 可维护性评估器集成失败: {e}")
        return False

def test_performance_analyzer_integration():
    """测试性能分析器集成"""
    print("\n2. 测试性能分析器集成...")
    
    try:
        from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator
        
        generator = DocumentationGenerator(str(project_root))
        
        # 直接测试性能分析器
        performance_result = generator.performance_analyzer.analyze_performance_bottlenecks(str(project_root / 'utils'))
        
        # 验证返回结果包含必要字段
        required_fields = ['performance_issues', 'performance_summary', 'resource_usage_analysis']
        for field in required_fields:
            assert field in performance_result, f"缺少字段: {field}"
        
        print("✓ 性能分析器集成成功")
        print(f"  - 发现问题: {performance_result['performance_summary']['total_issues']} 个")
        print(f"  - 总体评分: {performance_result['performance_summary']['overall_score']}/10")
        
        return True
        
    except Exception as e:
        print(f"✗ 性能分析器集成失败: {e}")
        return False

def test_document_quality_validation():
    """测试文档质量验证机制"""
    print("\n3. 测试文档质量验证机制...")
    
    try:
        from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator
        
        generator = DocumentationGenerator(str(project_root))
        
        # 测试完整文档验证
        test_document = """# 测试层级架构文档

## 层级概述
这是一个测试层级。

## 目录结构
```
test/
├── __init__.py
└── main.py
```

## 核心功能
提供测试功能。

## 架构分析
使用简单的架构模式。

## 优化建议
1. 添加更多测试
2. 改进文档

## 使用指南
按照标准流程使用。
"""
        
        validation_result = generator.validate_generated_document(test_document, "test/LAYER_GUIDE.md")
        
        # 验证返回结果包含必要字段
        required_fields = ['validation_issues', 'quality_metrics', 'validation_summary', 'is_valid']
        for field in required_fields:
            assert field in validation_result, f"缺少字段: {field}"
        
        print("✓ 文档质量验证机制正常")
        print(f"  - 质量评分: {validation_result['quality_metrics']['overall_score']:.2f}")
        print(f"  - 验证通过: {'是' if validation_result['is_valid'] else '否'}")
        print(f"  - 发现问题: {validation_result['quality_metrics']['total_issues']} 个")
        
        return True
        
    except Exception as e:
        print(f"✗ 文档质量验证失败: {e}")
        return False

def test_error_handling_and_logging():
    """测试错误处理和日志记录"""
    print("\n4. 测试错误处理和日志记录...")
    
    try:
        from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator
        
        generator = DocumentationGenerator(str(project_root))
        
        # 测试不存在的层级
        try:
            generator.generate_layer_documentation('nonexistent_layer')
            print("✗ 应该抛出异常但没有")
            return False
        except ValueError as e:
            print("✓ 正确处理不存在的层级错误")
        
        # 测试错误日志功能
        error_log = generator.get_error_log()
        print(f"✓ 错误日志功能正常，当前错误数: {len(error_log)}")
        
        # 测试生成错误文档
        error_doc = generator._generate_error_document("test_layer", "测试错误")
        assert "错误信息" in error_doc, "错误文档格式不正确"
        print("✓ 错误文档生成功能正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误处理和日志记录测试失败: {e}")
        return False

def test_integrated_workflow():
    """测试完整的集成工作流"""
    print("\n5. 测试完整的集成工作流...")
    
    try:
        from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator
        
        generator = DocumentationGenerator(str(project_root))
        
        # 生成完整文档（包含所有集成组件）
        documentation = generator.generate_layer_documentation('utils')
        
        # 验证文档包含可维护性和性能分析结果
        assert "可维护性" in documentation or "复杂度" in documentation, "文档中缺少可维护性分析"
        assert "性能" in documentation or "优化" in documentation, "文档中缺少性能分析"
        
        # 验证文档质量报告
        if "文档质量报告" in documentation:
            print("✓ 文档包含质量报告")
        
        print("✓ 完整集成工作流正常")
        print(f"  - 生成文档长度: {len(documentation)} 字符")
        
        return True
        
    except Exception as e:
        print(f"✗ 完整集成工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始全面测试文档生成核心功能...")
    print("=" * 60)
    
    tests = [
        test_maintainability_integration,
        test_performance_analyzer_integration,
        test_document_quality_validation,
        test_error_handling_and_logging,
        test_integrated_workflow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！文档生成核心功能完善完成")
        return True
    else:
        print("✗ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)