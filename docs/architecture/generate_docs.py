#!/usr/bin/env python3
"""
架构文档生成器命令行工具

用于生成量化交易系统各层级的标准化文档。

使用方法:
    python generate_docs.py [layer_name]  # 生成指定层级的文档
    python generate_docs.py --all         # 生成所有层级的文档
    python generate_docs.py --list        # 列出所有可用层级
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from BackEnd.docs.architecture import DocumentationGenerator


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='生成量化交易系统架构文档',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python generate_docs.py core          # 生成core层级文档
  python generate_docs.py --all         # 生成所有层级文档
  python generate_docs.py --list        # 列出所有层级
        """
    )
    
    parser.add_argument(
        'layer',
        nargs='?',
        help='要生成文档的层级名称'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='生成所有层级的文档'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有可用的层级'
    )
    
    parser.add_argument(
        '--output-dir',
        default=None,
        help='输出目录，默认为各层级目录下'
    )
    
    args = parser.parse_args()
    
    # 初始化文档生成器
    generator = DocumentationGenerator(str(project_root))
    
    if args.list:
        list_available_layers(generator)
        return
    
    if args.all:
        generate_all_layers(generator, args.output_dir)
        return
    
    if args.layer:
        generate_single_layer(generator, args.layer, args.output_dir)
        return
    
    # 如果没有指定参数，显示帮助信息
    parser.print_help()


def list_available_layers(generator):
    """列出所有可用的层级"""
    print("可用的层级:")
    print("-" * 40)
    
    for layer_name in generator.layer_categories.keys():
        layer_path = generator.project_root / layer_name
        if layer_path.exists():
            category = generator.layer_categories[layer_name].value
            print(f"  {layer_name:<15} ({category})")
        else:
            print(f"  {layer_name:<15} (目录不存在)")


def generate_single_layer(generator, layer_name, output_dir):
    """生成单个层级的文档"""
    try:
        print(f"正在生成 {layer_name} 层级文档...")
        
        if output_dir:
            output_path = Path(output_dir) / f"{layer_name}_LAYER_GUIDE.md"
            file_path = generator.save_layer_documentation(layer_name, str(output_path))
        else:
            file_path = generator.save_layer_documentation(layer_name)
        
        print(f"✓ 文档已生成: {file_path}")
        
    except Exception as e:
        print(f"✗ 生成 {layer_name} 层级文档时出错: {e}")
        sys.exit(1)


def generate_all_layers(generator, output_dir):
    """生成所有层级的文档"""
    print("正在生成所有层级文档...")
    print("-" * 40)
    
    success_count = 0
    error_count = 0
    
    for layer_name in generator.layer_categories.keys():
        layer_path = generator.project_root / layer_name
        if not layer_path.exists():
            print(f"⚠ 跳过 {layer_name} (目录不存在)")
            continue
        
        try:
            if output_dir:
                output_path = Path(output_dir) / f"{layer_name}_LAYER_GUIDE.md"
                file_path = generator.save_layer_documentation(layer_name, str(output_path))
            else:
                file_path = generator.save_layer_documentation(layer_name)
            
            print(f"✓ {layer_name:<15} -> {file_path}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ {layer_name:<15} -> 错误: {e}")
            error_count += 1
    
    print("-" * 40)
    print(f"完成! 成功: {success_count}, 失败: {error_count}")


if __name__ == '__main__':
    main()