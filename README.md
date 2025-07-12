# QuantTrade 量化交易系统

基于币安API的BTC/ETH量化分析系统，支持历史回测和实时信号提示。

## 项目结构

```
QuantTrade/
├── main.py              # 主程序入口
├── config.py            # 配置文件管理
├── env_example.txt      # 环境变量示例
├── modules/             # 功能模块
│   ├── data.py         # 数据获取与处理
│   ├── strategy.py     # 策略实现
│   ├── backtest.py     # 回测框架
│   ├── signal.py       # 信号推送
│   └── plot.py         # 可视化
└── README.md           # 项目说明
```

## 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或者单独安装核心依赖
pip install ccxt pandas numpy matplotlib websockets cryptography
```

## 配置说明

### 1. 环境变量配置（推荐）

复制 `env_example.txt` 为 `.env` 文件，并填入你的API密钥：

```bash
# 主网API密钥
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET=your_secret_here

# 环境设置
ENVIRONMENT=development  # development, test, production
```

### 2. 加密配置（更安全）

使用密钥管理工具安全保存API密钥：

```bash
# 交互式保存API密钥（加密存储）
python key_manager.py save

# 验证API密钥
python key_manager.py validate

# 查看密钥状态
python key_manager.py status

# 清除保存的密钥
python key_manager.py clear
```

### 2. 代理配置

如果使用代理，在 `.env` 文件中设置：

```bash
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

## 使用方法

### 1. 基础测试

```python
python test.py
```

### 2. 运行主程序

```python
python main.py
```

### 3. 切换环境

在代码中修改环境配置：

```python
from config import Config

# 开发环境
config = Config(env='development')

# 测试网环境
config = Config(env='test')

# 生产环境
config = Config(env='production')
```

## 功能特性

- ✅ 币安API数据获取（REST + WebSocket）
- ✅ 多环境配置支持（开发/测试/生产）
- ✅ 策略框架（均线交叉、RSI等）
- ✅ 回测系统
- ✅ 实时信号推送
- ✅ 可视化图表
- ✅ 代理支持
- ✅ **安全配置管理**
  - 🔐 环境变量优先级
  - 🔐 加密文件存储
  - 🔐 密钥验证机制
  - 🔐 交互式密钥管理

## 注意事项

1. **API密钥安全**：
   - 🔐 使用环境变量或加密存储，避免硬编码
   - 🔐 定期更换API密钥
   - 🔐 设置API密钥的IP白名单
   - 🔐 仅授予必要的权限（如只读权限）
2. **网络环境**：国内用户可能需要配置代理才能访问币安API
3. **测试网**：建议先在测试网环境测试，避免影响真实资金
4. **API限频**：注意币安API调用频率限制，避免被封禁
5. **文件安全**：确保 `.env`、`.encrypted_config`、`.secret_key` 等敏感文件不被提交到版本控制系统

## 开发计划

- [ ] 更多技术指标
- [ ] 机器学习策略
- [ ] 风险管理模块
- [ ] 多交易所支持
- [ ] Web界面
- [ ] 移动端推送 