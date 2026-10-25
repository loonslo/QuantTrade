# API变更日志

本文档记录了QuantTradeSys API的所有变更历史。

## 版本 v1.1.0

### 功能变更

- **/api/v1/market-data/***: 统一响应格式，添加success和message字段
  - 迁移指南: 响应数据现在包装在data字段中，请相应更新客户端代码

## 版本 v1.0.0

### 废弃功能

- **/klines**: 废弃旧的K线数据接口
  - 迁移指南: 请使用 /api/v1/market-data/klines 替代
  - 废弃日期: 2024-01-01
  - 计划移除日期: 2024-06-01
- **/symbols**: 废弃旧的交易对列表接口
  - 迁移指南: 请使用 /api/v1/market-data/symbols 替代
  - 废弃日期: 2024-01-01
  - 计划移除日期: 2024-06-01

### 新增功能

- **/api/v1/market-data/klines**: 新增标准化的K线数据接口
- **/api/v1/market-data/symbols**: 新增标准化的交易对列表接口

