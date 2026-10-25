#!/usr/bin/env python3
"""
README.md文档生成脚本

为量化交易系统的各个层级生成标准化的README.md文档。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator


def generate_readme_for_layer(generator: DocumentationGenerator, layer_name: str) -> bool:
    """
    为指定层级生成README.md文档
    
    Args:
        generator: 文档生成器实例
        layer_name: 层级名称
        
    Returns:
        是否成功生成文档
    """
    try:
        layer_path = project_root / layer_name
        if not layer_path.exists():
            print(f"❌ 层级目录不存在: {layer_name}")
            return False
        
        print(f"📝 正在生成 {layer_name} 层级的README.md文档...")
        
        # 生成文档内容
        documentation = generator.generate_layer_documentation(layer_name)
        
        # 保存为README.md文件
        readme_path = layer_path / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        print(f"✅ 成功生成: {readme_path}")
        
        # 验证文档质量
        validation_result = generator.validate_generated_document(documentation, str(readme_path))
        if validation_result['is_valid']:
            print(f"✅ 文档质量验证通过")
        else:
            print(f"⚠️  文档质量验证发现问题: {validation_result.get('validation_summary', {}).get('overall_quality', '未知')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成 {layer_name} 层级文档时出错: {str(e)}")
        return False


def generate_core_layers_documentation():
    """生成核心层级文档 (任务2.1)"""
    print("🚀 开始生成核心层级文档...")
    
    # 初始化文档生成器
    generator = DocumentationGenerator(str(project_root))
    
    # 核心层级列表
    core_layers = ['core', 'data', 'api']
    
    success_count = 0
    for layer_name in core_layers:
        if generate_readme_for_layer(generator, layer_name):
            success_count += 1
    
    print(f"\n📊 核心层级文档生成完成: {success_count}/{len(core_layers)} 成功")
    return success_count == len(core_layers)


def generate_business_layers_documentation():
    """生成业务层级文档 (任务2.2)"""
    print("🚀 开始生成业务层级文档...")
    
    # 初始化文档生成器
    generator = DocumentationGenerator(str(project_root))
    
    # 业务层级列表
    business_layers = ['strategies', 'user_strategies', 'analysis']
    
    success_count = 0
    for layer_name in business_layers:
        if generate_readme_for_layer(generator, layer_name):
            success_count += 1
    
    print(f"\n📊 业务层级文档生成完成: {success_count}/{len(business_layers)} 成功")
    return success_count == len(business_layers)


def generate_support_layers_documentation():
    """生成支持层级文档 (任务2.3)"""
    print("🚀 开始生成支持层级文档...")
    
    # 初始化文档生成器
    generator = DocumentationGenerator(str(project_root))
    
    # 支持层级列表
    support_layers = ['services', 'utils', 'config']
    
    success_count = 0
    for layer_name in support_layers:
        if generate_readme_for_layer(generator, layer_name):
            success_count += 1
    
    print(f"\n📊 支持层级文档生成完成: {success_count}/{len(support_layers)} 成功")
    return success_count == len(support_layers)


def generate_extension_layers_documentation():
    """生成扩展层级文档 (任务2.4)"""
    print("🚀 开始生成扩展层级文档...")
    
    # 初始化文档生成器
    generator = DocumentationGenerator(str(project_root))
    
    # 扩展层级列表
    extension_layers = ['optimization', 'docs']
    
    success_count = 0
    for layer_name in extension_layers:
        if generate_readme_for_layer(generator, layer_name):
            success_count += 1
    
    print(f"\n📊 扩展层级文档生成完成: {success_count}/{len(extension_layers)} 成功")
    return success_count == len(extension_layers)


def generate_all_layers_documentation():
    """生成所有11个层级的README.md文档"""
    print("🚀 开始为所有11个层级生成README.md文档...")
    
    # 初始化文档生成器
    generator = DocumentationGenerator(str(project_root))
    
    # 所有层级列表
    all_layers = [
        # 核心层级
        'core', 'data', 'api',
        # 业务层级
        'strategies', 'user_strategies', 'analysis',
        # 支持层级
        'services', 'utils', 'config',
        # 扩展层级
        'optimization', 'docs'
    ]
    
    success_count = 0
    failed_layers = []
    
    for layer_name in all_layers:
        if generate_readme_for_layer(generator, layer_name):
            success_count += 1
        else:
            failed_layers.append(layer_name)
    
    print(f"\n📊 总体文档生成结果:")
    print(f"✅ 成功: {success_count}/{len(all_layers)} 个层级")
    
    if failed_layers:
        print(f"❌ 失败的层级: {', '.join(failed_layers)}")
    
    # 生成汇总报告
    generate_summary_report(all_layers, success_count, failed_layers)
    
    return success_count == len(all_layers)


def generate_summary_report(all_layers: list, success_count: int, failed_layers: list):
    """生成文档生成汇总报告"""
    report_path = project_root / "docs" / "architecture" / "README_GENERATION_REPORT.md"
    
    report_content = f"""# README.md文档生成报告

## 生成概况

- **生成时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **总层级数**: {len(all_layers)}
- **成功生成**: {success_count}
- **失败数量**: {len(failed_layers)}
- **成功率**: {(success_count/len(all_layers)*100):.1f}%

## 层级分类

### 核心层级 (Core Layers)
- core: 系统核心抽象和接口定义
- data: 数据获取、存储和管理
- api: REST API和WebSocket接口

### 业务层级 (Business Layers)
- strategies: 交易策略实现
- user_strategies: 用户自定义策略
- analysis: 性能分析和技术分析

### 支持层级 (Support Layers)
- services: 业务服务和工具
- utils: 通用工具和辅助函数
- config: 配置管理

### 扩展层级 (Extension Layers)
- optimization: 策略优化算法
- docs: 项目文档

## 生成结果

### 成功生成的层级
"""
    
    for layer in all_layers:
        if layer not in failed_layers:
            layer_path = project_root / layer / "README.md"
            status = "✅" if layer_path.exists() else "⚠️"
            report_content += f"- {status} **{layer}**: README.md已生成\n"
    
    if failed_layers:
        report_content += "\n### 失败的层级\n"
        for layer in failed_layers:
            report_content += f"- ❌ **{layer}**: 生成失败\n"
    
    report_content += f"""
## 文档标准化

所有生成的README.md文档都遵循以下标准化结构:

1. **层级概述** - 层级的主要职责和用途
2. **目录结构** - 详细的目录树和文件说明
3. **核心功能** - 主要功能模块和接口
4. **架构分析** - 设计模式、依赖关系、数据流
5. **代码优化建议** - 性能、可维护性、最佳实践建议
6. **使用指南** - 开发者如何使用该层级
7. **相关层级** - 与其他层级的交互关系

## 质量保证

- 所有文档都经过自动化质量验证
- 包含可维护性和性能分析结果
- 提供具体的优化建议和最佳实践

---

*本报告由架构文档生成器自动生成*
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📋 生成汇总报告: {report_path}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'core':
            generate_core_layers_documentation()
        elif command == 'business':
            generate_business_layers_documentation()
        elif command == 'support':
            generate_support_layers_documentation()
        elif command == 'extension':
            generate_extension_layers_documentation()
        elif command == 'all':
            generate_all_layers_documentation()
        else:
            print("❌ 未知命令。可用命令: core, business, support, extension, all")
            sys.exit(1)
    else:
        # 默认生成所有层级文档
        generate_all_layers_documentation()


if __name__ == "__main__":
    main()