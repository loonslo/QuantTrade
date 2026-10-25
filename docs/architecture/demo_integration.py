#!/usr/bin/env python3
"""
文档生成器集成功能演示

展示任务1完成的功能：
1. 集成可维护性评估器和性能优化器到主文档生成流程
2. 实现文档质量验证机制  
3. 添加错误处理和日志记录
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def demonstrate_integration():
    """演示完整的集成功能"""
    print("文档生成器集成功能演示")
    print("=" * 50)
    
    from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator
    
    # 初始化文档生成器
    generator = DocumentationGenerator(str(project_root))
    print("✓ 文档生成器初始化完成")
    
    # 选择一个层级进行演示
    layer_name = 'utils'
    print(f"\n正在为 {layer_name} 层级生成文档...")
    
    try:
        # 生成完整文档（包含所有集成功能）
        documentation = generator.generate_layer_documentation(layer_name)
        
        print(f"✓ 文档生成完成，总长度: {len(documentation)} 字符")
        
        # 显示文档的主要章节
        print("\n文档包含的主要章节:")
        sections = ['层级概述', '目录结构', '核心功能', '架构分析', '优化建议', '使用指南']
        for section in sections:
            if section in documentation:
                print(f"  ✓ {section}")
            else:
                print(f"  ✗ {section} (缺失)")
        
        # 验证文档质量
        print("\n执行文档质量验证...")
        validation_result = generator.validate_generated_document(
            documentation, f"{layer_name}/LAYER_GUIDE.md"
        )
        
        quality_metrics = validation_result['quality_metrics']
        print(f"  - 总体质量评分: {quality_metrics['overall_score']:.2f}/1.0")
        print(f"  - 完整性评分: {quality_metrics['completeness_score']:.2f}/1.0")
        print(f"  - 格式评分: {quality_metrics['format_score']:.2f}/1.0")
        print(f"  - 内容评分: {quality_metrics['content_score']:.2f}/1.0")
        print(f"  - 发现问题: {quality_metrics['total_issues']} 个")
        print(f"  - 严重问题: {quality_metrics['critical_issues']} 个")
        print(f"  - 验证通过: {'是' if validation_result['is_valid'] else '否'}")
        
        # 显示改进建议
        if validation_result.get('recommendations'):
            print("\n改进建议:")
            for i, rec in enumerate(validation_result['recommendations'][:3], 1):
                print(f"  {i}. {rec}")
        
        # 显示可维护性分析结果
        print("\n可维护性分析结果:")
        maintainability_result = generator.maintainability_evaluator.evaluate_maintainability(str(project_root / layer_name))
        summary = maintainability_result['maintainability_summary']
        print(f"  - 总体可维护性评分: {summary['overall_maintainability_score']}/10")
        print(f"  - 发现问题: {summary['total_issues']} 个")
        print(f"  - 严重问题: {summary['critical_issues']} 个")
        print(f"  - 高优先级问题: {summary['high_priority_issues']} 个")
        
        # 显示性能分析结果
        print("\n性能分析结果:")
        performance_result = generator.performance_analyzer.analyze_performance_bottlenecks(str(project_root / layer_name))
        perf_summary = performance_result['performance_summary']
        print(f"  - 总体性能评分: {perf_summary['overall_score']}/10")
        print(f"  - 发现问题: {perf_summary['total_issues']} 个")
        print(f"  - 严重问题: {perf_summary['critical_issues']} 个")
        print(f"  - 高优先级问题: {perf_summary['high_priority_issues']} 个")
        
        # 显示资源使用分析
        resource_analysis = performance_result.get('resource_usage_analysis', {})
        resource_summary = resource_analysis.get('resource_summary', {})
        if resource_summary:
            print(f"  - 资源使用强度: {resource_summary.get('overall_intensity', 0):.2f}/1.0")
            if resource_summary.get('most_intensive_resource'):
                print(f"  - 主要资源瓶颈: {resource_summary['most_intensive_resource']}")
        
        # 检查错误日志
        error_log = generator.get_error_log()
        print(f"\n错误处理状态:")
        print(f"  - 记录的错误数量: {len(error_log)}")
        if error_log:
            print("  - 最近的错误:")
            for error in error_log[-3:]:  # 显示最近3个错误
                print(f"    * {error['layer']}: {error['error'][:50]}...")
        else:
            print("  - 没有记录到错误")
        
        print(f"\n✓ {layer_name} 层级文档生成和验证完成！")
        
        # 可选：保存文档到文件
        save_choice = input("\n是否保存生成的文档到文件？(y/n): ").lower().strip()
        if save_choice == 'y':
            output_path = generator.save_layer_documentation(layer_name)
            print(f"✓ 文档已保存到: {output_path}")
        
    except Exception as e:
        print(f"✗ 文档生成失败: {e}")
        import traceback
        traceback.print_exc()

def demonstrate_error_handling():
    """演示错误处理功能"""
    print("\n" + "=" * 50)
    print("错误处理功能演示")
    
    from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator
    
    generator = DocumentationGenerator(str(project_root))
    
    # 测试不存在的层级
    print("\n测试不存在的层级处理...")
    try:
        generator.generate_layer_documentation('nonexistent_layer')
        print("✗ 应该抛出异常")
    except ValueError as e:
        print(f"✓ 正确捕获异常: {e}")
    
    # 测试错误文档生成
    print("\n测试错误文档生成...")
    error_doc = generator._generate_error_document("test_layer", "演示错误信息")
    print("✓ 错误文档生成成功")
    print("错误文档预览:")
    print("-" * 30)
    print(error_doc[:200] + "...")
    print("-" * 30)

if __name__ == "__main__":
    demonstrate_integration()
    demonstrate_error_handling()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print("\n主要功能已完成:")
    print("✓ 1. 可维护性评估器集成")
    print("✓ 2. 性能分析器集成") 
    print("✓ 3. 文档质量验证机制")
    print("✓ 4. 错误处理和日志记录")
    print("✓ 5. 完整的文档生成流程")