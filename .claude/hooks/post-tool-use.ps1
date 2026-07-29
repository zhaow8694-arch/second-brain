#!/usr/bin/env pwsh
# PostToolUse Hook — 工具执行后质量保障
# 自动格式化 Markdown + 维护记忆索引

param()
$inputJson = [Console]::In.ReadToEnd()

try {
    $context = $inputJson | ConvertFrom-Json
} catch {
    exit 0
}

$toolName = $context.tool
$result = $context.result

# 仅在 Write/Edit 成功后执行
if ($toolName -ne "Write" -and $toolName -ne "Edit") {
    exit 0
}

$filePath = $context.params.file_path

# 只处理 Markdown 文件
if ($filePath -notmatch "\.md$") {
    exit 0
}

# 忽略系统文件
if ($filePath -match "\.claude|\.obsidian|MEMORY\.md|hot\.md|node_modules") {
    exit 0
}

# === 检查 frontmatter ===
$content = $result.content
if (-not $content -or $content -notmatch "^---") {
    exit 0  # 没有 frontmatter 的文件不处理
}

# === 确保 tags 和 date 字段存在 ===
$hasDate = $content -match "^date:"
$hasTags = $content -match "^tags:"

$fixes = @()
if (-not $hasDate) { $fixes += "date" }
if (-not $hasTags) { $fixes += "tags" }

if ($fixes.Count -gt 0) {
    Write-Host "POSTTOOL: $filePath 缺少 [$($fixes -join ', ')] frontmatter，建议补充"
}

exit 0
