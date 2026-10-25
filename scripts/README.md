# 项目工具脚本

## cleanup.ps1

项目清理脚本，用于清理Python项目中的缓存和临时文件。

### 功能
1. 清理所有 `__pycache__/` 目录
2. 删除所有 `.pyc` 文件
3. 清理 IDE 配置文件（.idea, .vscode, .claude）
4. 清理日志文件
5. 清理临时文件
6. 检查并显示空目录

### 使用方法

#### Windows PowerShell
```powershell
# 在项目根目录执行
.\scripts\cleanup.ps1
```

#### 如果遇到执行策略限制
```powershell
# 临时允许脚本执行
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 然后运行脚本
.\scripts\cleanup.ps1
```

### 注意事项
- 脚本会删除所有缓存文件，但不会删除源代码
- IDE 配置文件会被删除，如需保留请修改脚本
- 日志文件会被清理，如需保留请先备份
- 空目录不会自动删除，需要手动确认

### 建议使用场景
- 提交代码前清理缓存
- 切换分支前清理环境
- 定期维护项目
- 解决缓存导致的问题

### 自定义
如需自定义清理规则，请编辑 `cleanup.ps1` 文件中的相应部分。
