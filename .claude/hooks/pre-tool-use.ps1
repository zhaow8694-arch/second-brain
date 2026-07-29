#!/usr/bin/env pwsh
# PreToolUse Hook — 工具调用前安全检查
# 从 stdin 读取 JSON 上下文，通过 exit code 决定放行(0)或阻断(非0)

param()
$inputJson = [Console]::In.ReadToEnd()

try {
    $context = $inputJson | ConvertFrom-Json
} catch {
    exit 0  # 解析失败时放行，避免误拦截
}

$toolName = $context.tool
$params = $context.params

# ========== 规则 1：禁止修改保护目录 ==========
$protectedDirs = @(
    "08_杂项",
    "07_数据库",
    ".obsidian",
    ".git"
)

# ========== 规则 2：禁止删除 EA 源码 ==========
$protectedExtensions = @(
    ".mq5", ".mq4", ".ex5", ".ex4"
)

if ($toolName -eq "Write" -or $toolName -eq "Edit") {
    $filePath = $params.file_path
    if ($filePath) {
        foreach ($dir in $protectedDirs) {
            if ($filePath -match [regex]::Escape($dir)) {
                Write-Host "BLOCKED: 禁止写入保护目录 $dir — $filePath"
                exit 1
            }
        }
    }
}

if ($toolName -eq "Bash") {
    $cmd = $params.command
    # 阻断高危命令
    $dangerousPatterns = @(
        "rm\s+-rf\s+/",
        "rm\s+-rf\s+--no-preserve-root",
        "format\s+[cC]:",
        "del\s+/[fF]\s+/[sS]\s+[cC]:",
        "rd\s+/[sS]\s+/[qQ]\s+[cC]:"
    )
    foreach ($pattern in $dangerousPatterns) {
        if ($cmd -match $pattern) {
            Write-Host "BLOCKED: 检测到高危命令: $pattern"
            exit 1
        }
    }

    # 阻断删除 .mq5/.mq4 文件
    if ($cmd -match "Remove-Item.*\.mq[54]" -or $cmd -match "rm.*\.mq[54]") {
        Write-Host "BLOCKED: 禁止删除 EA 源码 (.mq5/.mq4)"
        exit 1
    }
}

exit 0
