#!/usr/bin/env pwsh
# Stop Hook — 会话结束时验证工作是否完成

param()
$inputJson = [Console]::In.ReadToEnd()

try {
    $context = $inputJson | ConvertFrom-Json
} catch {
    exit 0
}

$hasWorkRecord = $false
$hasIndexUpdate = $false

# 检查本次会话是否更新了工作记录和索引
foreach ($msg in $context.messages) {
    foreach ($toolCall in $msg.tool_calls) {
        $path = $toolCall.params.file_path
        if ($path -match "工作记录\.md") {
            $hasWorkRecord = $true
        }
        if ($path -match "知识库索引总表\.md") {
            $hasIndexUpdate = $true
        }
    }
}

$warnings = @()

if (-not $hasWorkRecord) {
    $warnings += "⚠️ 工作记录.md 未更新 — 建议追加本次会话摘要"
}
if (-not $hasIndexUpdate) {
    $warnings += "⚠️ 知识库索引总表未更新 — 如有新增文件请更新"
}

# 检查是否更新了 MEMORY.md
$hasMemoryUpdate = $false
foreach ($msg in $context.messages) {
    foreach ($toolCall in $msg.tool_calls) {
        $path = $toolCall.params.file_path
        if ($path -match "MEMORY\.md") {
            $hasMemoryUpdate = $true
        }
    }
}

if (-not $hasMemoryUpdate) {
    $warnings += "⚠️ MEMORY.md 未更新 — 如有关键决策/修复/结论请更新"
}

if ($warnings.Count -gt 0) {
    Write-Host ($warnings -join "`n")
    # exit 1 会阻止会话结束，这里仅警告不阻断
    exit 0
}

exit 0
