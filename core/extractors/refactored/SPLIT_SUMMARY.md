# Extractors 拆分总结

## 拆分统计

| 模块 | 项目数 | 说明 |
|------|--------|------|
| core_types | 1 | 核心类型 |
| backtrader_extractor | 1 | Backtrader提取器 |
| generic_extractor | 3 | 通用提取器 |
| equity_builder | 1 | 权益构建器 |
| equity_fallback | 1 | 权益降级构建器 |
| position_builder | 2 | 持仓构建器 |
| pnl_calculator | 1 | 盈亏计算器 |
| timeline_merger | 1 | 时间线合并器 |

## 文件结构

```
core/extractors/refactored/
├── __init__.py               # 模块初始化
├── main_extractor.py         # 主入口文件
├── core_types.py             # 核心类型
├── backtrader_extractor.py   # Backtrader提取器
├── generic_extractor.py      # 通用提取器
├── equity_builder.py         # 权益构建器
├── equity_fallback.py        # 权益降级构建器
├── position_builder.py       # 持仓构建器
├── pnl_calculator.py         # 盈亏计算器
└── timeline_merger.py        # 时间线合并器
```

## 重构效果

- 原始文件: core/extractors.py (694行)
- 拆分后: 9个文件，平均77行/文件
- 改善: 代码可读性、可维护性、可测试性显著提升

## 下一步

1. 测试所有提取模块
2. 更新导入路径
3. 验证API兼容性
4. 添加单元测试

## 注意事项

- 确保所有提取逻辑保持不变
- 保持异常处理逻辑一致
- 测试所有提取功能正常工作
