#!/usr/bin/env python3
"""
README.md文档完成度验证脚本

验证所有11个层级的README.md文档是否已成功生成并符合要求。
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

# 项目根目录
project_root = Path(__file__).parent.parent.parent

def verify_readme_exists(layer_name: str) -> Tuple[bool, str]:
    """
    验证README.md文件是否存在
    
    Args:
        layer_name: 层级名称
        
    Returns:
        (是否存在, 文件路径)
    """
    readme_path = project_root / layer_name / "README.md"
    return readme_path.exists(), str(readme_path)

def verify_readme_content(readme_path: str) -> Dict[str, bool]:
    """
    验证README.md内容是否包含必需章节
    
    Args:
        readme_path: README.md文件路径
        
    Returns:
        各章节是否存在的字典
    """
    required_sections = {
        "层级概述": False,
        "目录结构": False,
        "核心功能": False,
        "架构分析": False,
        "代码优化建议": False,
        "使用指南": False,
        "相关层级": False
    }
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for section in required_sections.keys():
            if section in content:
                required_sections[section] = True
                
    except Exception as e:
        print(f"读取文件 {readme_path} 时出错: {e}")
    
    return required_sections

def get_file_stats(readme_path: str) -> Dict[str, any]:
    """
    获取文件统计信息
    
    Args:
        readme_path: README.md文件路径
        
    Returns:
        文件统计信息
    """
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {
            'file_size': len(content),
            'line_count': len(content.split('\n')),
            'word_count': len(content.split()),
            'char_count': len(content)
        }
    except Exception:
        return {
            'file_size': 0,
            'line_count': 0,
            'word_count': 0,
            'char_count': 0
        }

def main():
    """主验证函数"""
    print("🔍 开始验证README.md文档完成度...")
    print("=" * 60)
    
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
    
    # 验证结果统计
    total_layers = len(all_layers)
    existing_files = 0
    complete_docs = 0
    
    # 详细验证结果
    verification_results = []
    
    for layer_name in all_layers:
        print(f"\n📁 验证层级: {layer_name}")
        
        # 检查文件是否存在
        exists, file_path = verify_readme_exists(layer_name)
        
        if not exists:
            print(f"❌ README.md文件不存在")
            verification_results.append({
                'layer': layer_name,
                'exists': False,
                'sections': {},
                'stats': {},
                'complete': False
            })
            continue
        
        existing_files += 1
        print(f"✅ README.md文件存在: {file_path}")
        
        # 验证内容章节
        sections = verify_readme_content(file_path)
        missing_sections = [section for section, exists in sections.items() if not exists]
        
        if missing_sections:
            print(f"⚠️  缺少章节: {', '.join(missing_sections)}")
        else:
            print(f"✅ 所有必需章节都存在")
            complete_docs += 1
        
        # 获取文件统计
        stats = get_file_stats(file_path)
        print(f"📊 文件统计: {stats['line_count']} 行, {stats['word_count']} 词, {stats['file_size']} 字节")
        
        verification_results.append({
            'layer': layer_name,
            'exists': True,
            'sections': sections,
            'stats': stats,
            'complete': len(missing_sections) == 0
        })
    
    # 生成总结报告
    print("\n" + "=" * 60)
    print("📋 验证总结报告")
    print("=" * 60)
    
    print(f"📊 总体统计:")
    print(f"   - 总层级数: {total_layers}")
    print(f"   - 存在README.md: {existing_files}")
    print(f"   - 完整文档: {complete_docs}")
    print(f"   - 文件存在率: {(existing_files/total_layers*100):.1f}%")
    print(f"   - 文档完整率: {(complete_docs/total_layers*100):.1f}%")
    
    # 按类别统计
    layer_categories = {
        '核心层级': ['core', 'data', 'api'],
        '业务层级': ['strategies', 'user_strategies', 'analysis'],
        '支持层级': ['services', 'utils', 'config'],
        '扩展层级': ['optimization', 'docs']
    }
    
    print(f"\n📂 分类统计:")
    for category, layers in layer_categories.items():
        category_complete = sum(1 for result in verification_results 
                              if result['layer'] in layers and result['complete'])
        print(f"   - {category}: {category_complete}/{len(layers)} 完整")
    
    # 详细问题报告
    incomplete_layers = [result for result in verification_results if not result['complete']]
    if incomplete_layers:
        print(f"\n⚠️  需要改进的层级:")
        for result in incomplete_layers:
            layer = result['layer']
            if not result['exists']:
                print(f"   - {layer}: 文件不存在")
            else:
                missing = [section for section, exists in result['sections'].items() if not exists]
                if missing:
                    print(f"   - {layer}: 缺少章节 - {', '.join(missing)}")
    
    # 文件大小统计
    if existing_files > 0:
        total_size = sum(result['stats'].get('file_size', 0) for result in verification_results if result['exists'])
        avg_size = total_size / existing_files
        print(f"\n📏 文件大小统计:")
        print(f"   - 总大小: {total_size:,} 字节")
        print(f"   - 平均大小: {avg_size:.0f} 字节")
        
        # 最大和最小文件
        sizes = [(result['layer'], result['stats'].get('file_size', 0)) 
                for result in verification_results if result['exists']]
        sizes.sort(key=lambda x: x[1])
        
        if sizes:
            print(f"   - 最小文件: {sizes[0][0]} ({sizes[0][1]:,} 字节)")
            print(f"   - 最大文件: {sizes[-1][0]} ({sizes[-1][1]:,} 字节)")
    
    # 最终结论
    print(f"\n🎯 验证结论:")
    if existing_files == total_layers and complete_docs == total_layers:
        print("✅ 所有层级的README.md文档都已成功生成并包含所有必需章节！")
        print("🎉 任务2完成度: 100%")
    elif existing_files == total_layers:
        print("✅ 所有层级的README.md文件都已生成")
        print(f"⚠️  但有 {total_layers - complete_docs} 个文档缺少某些章节")
        print(f"📈 任务2完成度: {(complete_docs/total_layers*100):.1f}%")
    else:
        print(f"❌ 有 {total_layers - existing_files} 个层级缺少README.md文件")
        print(f"📈 任务2完成度: {(existing_files/total_layers*100):.1f}%")
    
    return existing_files == total_layers and complete_docs == total_layers

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)