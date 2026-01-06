# project_name

## 概要
- 目的：
- 入出力：
- 想定利用者：


## セットアップ（Windows / PowerShell）

py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -U pip

# 依存があれば
# pip install -r requirements.lock.txt

.\.venv\Scripts\Activate.ps1

python .\apps\main.py


$env:PYTHONPATH = (Resolve-Path .\src).Path
>> python .\apps\web.py


★これはDBを更新するときに
################################################################################################

python .\src\tool_asset_system\db\scripts\manage.py





★最短で使える「tree /f 互換（地雷除外版）」強化版
################################################################################################


function Show-Tree {
  param(
    [string]$Root = ".",

    [string[]]$ExcludeDirNames = @(
      ".git", ".venv", "__pycache__", "build", "dist",
      ".webview_storage", ".mypy_cache", ".pytest_cache", ".ruff_cache",
      "node_modules"
    ),

    [string[]]$ExcludeFileNames = @(
      "*.pyc", "*.pyo", "*.log"
    ),

    [int]$MaxDepth = 0,

    [switch]$FollowLinks  # 既定は辿らない（安全）
  )

  $rootItem = Get-Item -LiteralPath $Root
  $rootPath = $rootItem.FullName

  function IsExcludedFile([string]$name) {
    foreach ($pat in $ExcludeFileNames) {
      if ($name -like $pat) { return $true }
    }
    return $false
  }

  function IsLink($item) {
    return [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
  }

  function Walk([string]$Path, [string]$Prefix, [int]$Depth) {
    if ($MaxDepth -gt 0 -and $Depth -ge $MaxDepth) { return }

    $items = @(
      Get-ChildItem -LiteralPath $Path -Force |
        Where-Object {
          if ($_.PSIsContainer) {
            $ExcludeDirNames -notcontains $_.Name
          } else {
            -not (IsExcludedFile $_.Name)
          }
        } |
        Sort-Object @{Expression = { -not $_.PSIsContainer }}, Name
    )

    for ($i = 0; $i -lt $items.Count; $i++) {
      $it = $items[$i]
      $isLast = ($i -eq $items.Count - 1)

      if ($isLast) {
        $branch = "└─ "
        $nextPrefix = $Prefix + "   "
      } else {
        $branch = "├─ "
        $nextPrefix = $Prefix + "│  "
      }

      $Prefix + $branch + $it.Name

      if ($it.PSIsContainer) {
        if (-not $FollowLinks -and (IsLink $it)) {
          continue
        }
        Walk -Path $it.FullName -Prefix $nextPrefix -Depth ($Depth + 1)
      }
    }
  }

  $rootItem.Name
  Walk -Path $rootPath -Prefix "" -Depth 0
}

Show-Tree -Root "."
