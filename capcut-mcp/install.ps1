# One-line install (PowerShell):
#   irm https://raw.githubusercontent.com/enzaout/enzaout/claude/practical-bell-euv4gj/capcut-mcp/install.ps1 | iex
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # progress bar makes downloads very slow on Windows PowerShell
$Branch = "claude/practical-bell-euv4gj"
$Base = "https://raw.githubusercontent.com/enzaout/enzaout/$Branch/capcut-mcp"
$Dir = Join-Path $env:USERPROFILE "capcut-mcp"

Write-Host "Installing CapCut MCP to $Dir"
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
Invoke-WebRequest "$Base/server.py" -OutFile (Join-Path $Dir "server.py") -UseBasicParsing

# Find a real Python (the Microsoft Store "python" alias is a stub that doesn't run).
function Find-Python {
    foreach ($cmd in @("python", "py")) {
        try {
            $exe = & $cmd -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe)) { return $exe.Trim() }
        } catch {}
    }
    $local = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
    if (Test-Path $local) { return $local }
    return $null
}

$Python = Find-Python
if (-not $Python) {
    Write-Host "Python not found. Downloading Python 3.12 from python.org..."
    $installer = Join-Path $env:TEMP "python-3.12.10-amd64.exe"
    Invoke-WebRequest "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe" -OutFile $installer -UseBasicParsing
    Start-Process $installer -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0" -Wait
    $Python = Find-Python
    if (-not $Python) { throw "Python install failed. Install it from python.org (check 'Add to PATH') and run this again." }
}
Write-Host "Using Python: $Python"
& $Python -m pip install --quiet --no-warn-script-location --upgrade pip mcp
if ($LASTEXITCODE -ne 0) { throw "pip install mcp failed." }

# FFmpeg is optional: it lets the server read video length. Placed next to server.py.
$ffprobe = Join-Path $Dir "ffmpeg\ffprobe.exe"
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue) -and -not (Test-Path $ffprobe)) {
    try {
        Write-Host "Downloading FFmpeg (about 100 MB)..."
        $zip = Join-Path $env:TEMP "ffmpeg.zip"
        $tmp = Join-Path $env:TEMP "ffmpeg-extract"
        Invoke-WebRequest "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip -UseBasicParsing
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Expand-Archive $zip -DestinationPath $tmp -Force
        $bin = Get-ChildItem $tmp -Recurse -Filter ffprobe.exe | Select-Object -First 1
        New-Item -ItemType Directory -Force -Path (Join-Path $Dir "ffmpeg") | Out-Null
        Copy-Item (Join-Path $bin.DirectoryName "*.exe") (Join-Path $Dir "ffmpeg") -Force
        Remove-Item $zip, $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "FFmpeg ready."
    } catch {
        Write-Host "FFmpeg download failed (optional, skipping): $_"
    }
}

$drafts = Join-Path $env:LOCALAPPDATA "CapCut\User Data\Projects\com.lveditor.draft"
if (Test-Path $drafts) { Write-Host "Found CapCut projects: $drafts" }
else { Write-Host "CapCut projects folder not found at $drafts. Set CAPCUT_DRAFTS to the folder shown in CapCut settings." }

$server = Join-Path $Dir "server.py"
$connected = $false
if (Get-Command claude -ErrorAction SilentlyContinue) {
    # Windows PowerShell turns a native command's stderr into a terminating error under "Stop".
    $ErrorActionPreference = "Continue"
    cmd /c "claude mcp remove capcut --scope user >nul 2>&1"
    claude mcp add capcut --scope user -- $Python $server
    $ErrorActionPreference = "Stop"
    Write-Host "Connected to Claude Code."
    $connected = $true
}
$cfgDir = Join-Path $env:APPDATA "Claude"
if (Test-Path $cfgDir) {
    $cfg = Join-Path $cfgDir "claude_desktop_config.json"
    $json = if (Test-Path $cfg) { Get-Content $cfg -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    if (-not $json) { $json = [pscustomobject]@{} }
    if (-not $json.mcpServers) { $json | Add-Member -Force -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) }
    $json.mcpServers | Add-Member -Force -NotePropertyName capcut -NotePropertyValue ([pscustomobject]@{ command = $Python; args = @($server) })
    [IO.File]::WriteAllText($cfg, ($json | ConvertTo-Json -Depth 10))
    Write-Host "Connected to Claude Desktop. Fully quit Claude Desktop (tray icon -> Quit) and open it again."
    $connected = $true
}
if (-not $connected) {
    Write-Host "Neither Claude Code nor Claude Desktop was found. Install one, then run this again."
}
Write-Host "Done. Ask Claude: 'show my CapCut projects'"
