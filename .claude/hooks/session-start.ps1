# SessionStart Hook — 每次会话启动时自动加载 hot.md
# 确保 Claude 在会话开始时就知道当前上下文

# 修复 Windows PowerShell 5.1 中文乱码：强制 UTF-8 输出
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== 🔥 Hot Cache Loaded ==="
Write-Host "自动加载 hot.md — 获取当前活跃上下文"
Write-Host ""

# 通知存在 hot.md，让模型自动读取
Write-Host "关键文件:"
Write-Host "  - E:\知识库\hot.md (活跃上下文)"
Write-Host "  - E:\知识库\CLAUDE.md (第二大脑宪法)"
Write-Host "  - E:\知识库\📖 知识库索引总表.md (全局索引)"
Write-Host "  - E:\知识库\.claude\memory\MEMORY.md (记忆索引)"
Write-Host ""

# 检查收件箱是否有待处理文件
$inboxItems = Get-ChildItem "E:\知识库\99_收件箱" -ErrorAction SilentlyContinue
if ($inboxItems) {
    Write-Host "📥 收件箱有 $($inboxItems.Count) 个文件待处理"
}

exit 0
