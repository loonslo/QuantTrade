# 项目清理脚本
# 用于清理Python项目中的缓存和临时文件

Write-Host "开始清理项目..." -ForegroundColor Green

# 1. 清理 Python 缓存
Write-Host "`n[1/5] 清理 Python 缓存文件..." -ForegroundColor Yellow
$pycacheCount = 0
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Remove-Item -Path $_.FullName -Recurse -Force
    $pycacheCount++
}
Write-Host "  删除了 $pycacheCount 个 __pycache__ 目录" -ForegroundColor Cyan

$pycCount = 0
Get-ChildItem -Path . -Recurse -Filter "*.pyc" | ForEach-Object {
    Remove-Item -Path $_.FullName -Force
    $pycCount++
}
Write-Host "  删除了 $pycCount 个 .pyc 文件" -ForegroundColor Cyan

# 2. 清理 IDE 配置（可选）
Write-Host "`n[2/5] 清理 IDE 配置文件..." -ForegroundColor Yellow
$ideFiles = @(".idea", ".vscode/.ropeproject", ".claude")
foreach ($file in $ideFiles) {
    if (Test-Path $file) {
        Remove-Item -Path $file -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  删除了 $file" -ForegroundColor Cyan
    }
}

# 3. 清理日志文件（可选）
Write-Host "`n[3/5] 清理日志文件..." -ForegroundColor Yellow
$logCount = 0
Get-ChildItem -Path "logs" -Filter "*.log" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -Path $_.FullName -Force
    $logCount++
}
Write-Host "  删除了 $logCount 个日志文件" -ForegroundColor Cyan

# 4. 清理临时文件
Write-Host "`n[4/5] 清理临时文件..." -ForegroundColor Yellow
$tempPatterns = @("*.tmp", "*.temp", "*~", ".DS_Store")
$tempCount = 0
foreach ($pattern in $tempPatterns) {
    Get-ChildItem -Path . -Recurse -Filter $pattern -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -Path $_.FullName -Force
        $tempCount++
    }
}
Write-Host "  删除了 $tempCount 个临时文件" -ForegroundColor Cyan

# 5. 显示空目录
Write-Host "`n[5/5] 检查空目录..." -ForegroundColor Yellow
$emptyDirs = Get-ChildItem -Path . -Recurse -Directory | Where-Object { 
    $_.GetFiles().Count -eq 0 -and $_.GetDirectories().Count -eq 0 
}
if ($emptyDirs) {
    Write-Host "  发现以下空目录：" -ForegroundColor Cyan
    $emptyDirs | ForEach-Object { Write-Host "    - $($_.FullName)" -ForegroundColor Gray }
    Write-Host "  提示：空目录不会自动删除，请手动确认是否需要" -ForegroundColor Yellow
} else {
    Write-Host "  没有发现空目录" -ForegroundColor Cyan
}

# 完成
Write-Host "`n清理完成！" -ForegroundColor Green
Write-Host "建议运行 'git status' 检查是否有需要提交的 .gitignore 更新" -ForegroundColor Yellow
