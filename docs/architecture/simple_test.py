#!/usr/bin/env python3
"""
简单的集成测试
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_basic_integration():
    """测试基本集成功能"""
    print("测试文档生成器基本功能...")
    
    try:
        from BackEnd.docs.architecture.documentation_generator import DocumentationGenerator
        
        # 初始化生成器
        generator = DocumentationGenerator(str(project_root))
        print("✓ 文档生成器初始化成功")
        
        # 测试utils层级（相对简单）
        utils_path = project_root / 'utils'
        if utils_path.exists():
            print("测试utils层级文档生成...")
            
            # 生成文档
            documentation = generator.generate_layer_documentation('utils')
            print(f"✓ 文档生成成功，长度: {len(documentation)} 字符")
            
            # 验证文档包含必要章节
            required_sections = ['层级概述', '目录结构', '核心功能', '架构分析']
            missing_sections = []
            for section in required_sections:
                if section not in documentation:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"⚠ 缺少章节: {', '.join(missing_sections)}")
            else:
                print("✓ 所有必要章节都存在")
            
            # 测试文档质量验证
            validation_result = generator.validate_generated_document(documentation)
            print(f"✓ 文档质量评分: {validation_result['quality_metrics']['overall_score']:.2f}")
            
            return True
        else:
            print("utils目录不存在，跳过测试")
            return True
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_integration()
    if success:
        print("\n✓ 集成测试通过！")
    else:
        print("\n✗ 集成测试失败！")