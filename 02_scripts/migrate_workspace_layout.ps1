$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath('E:\4robot')
$oldRepo = Join-Path $taskRoot 'Dai-4-Ji-Super-Robot-Taisen-S'
function Assert-InWorkspace([string]$path) {
    $resolved = [IO.Path]::GetFullPath($path)
    if (-not $resolved.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path outside workspace: $resolved"
    }
    return $resolved
}
function Move-Verified([string]$source, [string]$destination) {
    $src = Assert-InWorkspace $source
    $dst = Assert-InWorkspace $destination
    if (-not (Test-Path -LiteralPath $src)) { throw "Missing source: $src" }
    if (Test-Path -LiteralPath $dst) { throw "Destination already exists: $dst" }
    $parent = Split-Path -Parent $dst
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Move-Item -LiteralPath $src -Destination $dst
    $script:moves.Add([pscustomobject]@{source=$src;destination=$dst})
}
if (Test-Path -LiteralPath (Join-Path $taskRoot '.git')) { throw 'Root is already a repository' }
$moves = [Collections.Generic.List[object]]::new()
$inputs = @(Get-ChildItem -LiteralPath $taskRoot -File | Where-Object { $_.Name -like '*Track*.bin' })
if ($inputs.Count -ne 4) { throw 'Expected four original/reference track files' }
$inputHashes = @{}
foreach ($input in $inputs) { $inputHashes[$input.Name] = (Get-FileHash -LiteralPath $input.FullName -Algorithm SHA256).Hash }
$rootRules = Get-Content -LiteralPath (Join-Path $taskRoot 'AGENTS.md') -Encoding UTF8 -Raw
$nestedRules = Get-Content -LiteralPath (Join-Path $oldRepo 'AGENTS.md') -Encoding UTF8 -Raw
$ruleBackup = Join-Path $oldRepo '99_backup\layout_20260913'
New-Item -ItemType Directory -Path $ruleBackup -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $taskRoot 'AGENTS.md') -Destination (Join-Path $ruleBackup 'root_AGENTS.md')
Move-Verified (Join-Path $oldRepo 'AGENTS.md') (Join-Path $ruleBackup 'nested_AGENTS.md')
foreach ($child in @(Get-ChildItem -LiteralPath $oldRepo -Force)) {
    Move-Verified $child.FullName (Join-Path $taskRoot $child.Name)
}
$extra = $nestedRules.Substring($nestedRules.IndexOf('# SRW-specific rules'))
$mergedRules = $rootRules.Replace('Arc the Lad 1(PS1)', 'Dai-4-Ji Super Robot Taisen S(PS1)') + "`r`n`r`n" + $extra
[IO.File]::WriteAllText((Join-Path $taskRoot 'AGENTS.md'), $mergedRules, [Text.UTF8Encoding]::new($false))
Move-Verified (Join-Path $taskRoot 'extension_analysis') (Join-Path $taskRoot '01_work\extension_analysis')
Move-Verified (Join-Path $taskRoot 'vram_test') (Join-Path $taskRoot '01_work\vram_test')
Move-Verified (Join-Path $taskRoot 'srw4s-kr-patch') (Join-Path $taskRoot '01_work\reference\srw4s-kr-patch')
Move-Verified (Join-Path $taskRoot 'sfc') (Join-Path $taskRoot '00_original\sfc')
foreach ($input in $inputs) {
    $dst = Join-Path $taskRoot ('00_original\ps1\' + $input.Name)
    Move-Verified $input.FullName $dst
    if ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -ne $inputHashes[$input.Name]) { throw "Hash mismatch: $dst" }
}
Move-Verified (Join-Path $taskRoot '03_output') (Join-Path $taskRoot '01_work\experiments')
New-Item -ItemType Directory -Path (Join-Path $taskRoot '03_output\v001_native_loader') -Force | Out-Null
$record = [pscustomobject]@{date='2026-09-13';root=$taskRoot;moves=$moves;input_sha256=$inputHashes;input_hashes_preserved=$true}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskRoot '05_docs\layout_migration.json') -Encoding UTF8
$emptyRepo = Assert-InWorkspace $oldRepo
if (@(Get-ChildItem -LiteralPath $emptyRepo -Force).Count -eq 0) { Remove-Item -LiteralPath $emptyRepo }
Write-Output 'Migration completed; input hashes preserved. Path references still require update.'
