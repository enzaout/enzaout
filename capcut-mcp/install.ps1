# One-line install (PowerShell):
#   irm https://raw.githubusercontent.com/enzaout/enzaout/claude/practical-bell-euv4gj/capcut-mcp/install.ps1 | iex
$ErrorActionPreference = "Stop"
$Branch = "claude/practical-bell-euv4gj"
$Base = "https://raw.githubusercontent.com/enzaout/enzaout/$Branch/capcut-mcp"
$Dir = Join-Path $env:USERPROFILE "capcut-mcp"

Write-Host "Installing CapCut MCP to $Dir"
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
Invoke-WebRequest "$Base/server.py" -OutFile (Join-Path $Dir "server.py")

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Python not found. Installing with winget..."
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
}
python -m pip install --quiet --upgrade mcp

if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
    Write-Host "Installing FFmpeg (used to read video length)..."
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
}

$drafts = Join-Path $env:LOCALAPPDATA "CapCut\User Data\Projects\com.lveditor.draft"
if (Test-Path $drafts) { Write-Host "Found CapCut projects: $drafts" }
else { Write-Host "CapCut projects folder not found at $drafts. Set CAPCUT_DRAFTS to the folder shown in CapCut settings." }

$server = Join-Path $Dir "server.py"
if (Get-Command claude -ErrorAction SilentlyContinue) {
    claude mcp remove capcut --scope user 2>$null
    claude mcp add capcut --scope user -- python $server
    Write-Host "Connected to Claude Code."
}
$cfg = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
if (Test-Path (Split-Path $cfg)) {
    $json = if (Test-Path $cfg) { Get-Content $cfg -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    if (-not $json.mcpServers) { $json | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) }
    $json.mcpServers | Add-Member -Force -NotePropertyName capcut -NotePropertyValue ([pscustomobject]@{ command = "python"; args = @($server) })
    $json | ConvertTo-Json -Depth 10 | Set-Content $cfg -Encoding UTF8
    Write-Host "Connected to Claude Desktop. Restart Claude Desktop."
}
Write-Host "Done. Ask Claude: 'show my CapCut projects'"
