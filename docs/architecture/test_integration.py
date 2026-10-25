#!/usr/bin/env python3
"""
测试文档生成器集成功能

验证可维护性评估器、性能分析器和文档质量验证器的集成。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator


def test_documentation_generation():
    """测试文档生成功能"""
    print("开始测试文档生成器集成功能...")
    
    # 初始化文档生成器
    generator = DocumentationGenerator(str(project_root))
    
    # 测试层级列表
    test_layers = ['core', 'data', 'api', 'utils']
    
    for layer_name in test_layers:
        layer_path = project_root / layer_name
        if layer_path.exists():
            print(f"\n测试 {layer_name} 层级...")
            
            try:
                # 生成文档
                documentation = generator.generate_layer_documentation(layer_name)
                
                # 验证文档质量
                validation_result = generator.validate_generated_document(
                    documentation, f"{layer_name}/LAYER_GUIDE.md"
                )
                
                print(f"✓ {layer_name} 层级文档生成成功")
                print(f"  - 文档长度: {len(documentation)} 字符")
                print(f"  - 质量评分: {validation_result['quality_metrics']['overall_score']:.2f}")
                print(f"  - 验证通过: {'是' if validation_result['is_valid'] else '否'}")
                
                if validation_result['quality_metrics']['total_issues'] > 0:
                    print(f"  - 发现问题: {validation_result['quality_metrics']['total_issues']} 个")
                
            except Exception as e:
                print(f"✗ {layer_name} 层级文档生成失败: {e}")
        else:
            print(f"跳过 {layer_name} 层级（目录不存在）")
    
    # 检查错误日志
    error_log = generator.get_error_log()
    if error_log:
        print(f"\n发现 {len(error_log)} 个错误:")
        for error in error_log:
            print(f"  - {error['layer']}: {error['error']}")
    else:
        print("\n✓ 没有发现错误")
    
    print("\n测试完成!")


def test_individual_components():
    """测试各个组件的独立功能"""
    print("\n开始测试各个组件...")
    
    generator = DocumentationGenerator(str(project_root))
    
    # 测试可维护性评估器
    print("\n测试可维护性评估器...")
    try:
        maintainability_result = generator.maintainability_evaluator.evaluate_maintainability(str(project_root / 'core'))
        print(f"✓ 可维护性评估完成，发现 {maintainability_result['maintainability_summary']['total_issues']} 个问题")
    except Exception as e:
        print(f"✗ 可维护性评估失败: {e}")
    
    # 测试性能分析器
    print("\n测试性能分析器...")
    try:
        performance_result = generator.performance_analyzer.analyze_performance_bottlenecks(str(project_root / 'core'))
        print(f"✓ 性能分析完成，发现 {performance_result['performance_summary']['total_issues']} 个问题")
    except Exception as e:
        print(f"✗ 性能分析失败: {e}")
    
    # 测试文档验证器
    print("\n测试文档验证器...")
    try:
        test_doc = """# 测试文档
        
## 概述
这是一个测试文档。

## 详细内容
包含一些基本内容。
"""
        validation_result = generator.document_validator.validate_document(test_doc)
        print(f"✓ 文档验证完成，质量评分: {validation_result['quality_metrics']['overall_score']:.2f}")
    except Exception as e:
        print(f"✗ 文档验证失败: {e}")


if __name__ == "__main__":
    test_individual_components()
    test_documentation_generation()