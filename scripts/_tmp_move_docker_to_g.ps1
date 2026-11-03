# Temporary migration helper (not part of the backend): relocates Docker Desktop from C: to G:.
# Phases are ordered and idempotent: prep -> move -> ubuntu -> verify -> cleanup. Rollback restores the
# original folders from the *.old copies created during 'move' (nothing is deleted before that point).
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('prep', 'move', 'ubuntu', 'verify', 'cleanup', 'rollback')]
    [string]$Phase,
    [string]$Root = 'G:\Docker',
    # Restricts 'move' to selected entries of $Map (used when one folder is temporarily locked, e.g. the
    # program directory while wslservice.exe still holds resources\wsl\ext4.vhdx).
    [string[]]$Only = @()
)

$ErrorActionPreference = 'Stop'
$script:Log = Join-Path $Root '_migration\migration.log'

function Write-Log([string]$Message) {
    $line = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Add-Content -Path $script:Log -Value $line -Encoding UTF8
    Write-Host $line
}

function Get-FolderStats([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $files = Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue
    $bytes = ($files | Measure-Object -Property Length -Sum).Sum
    [pscustomobject]@{ Count = @($files).Count; Bytes = [int64]$bytes; GB = [math]::Round($bytes / 1GB, 2) }
}

# Directory pairs to relocate: the real content lands on G:, a junction keeps the old C: path valid so
# services, PATH entries and Docker Desktop's own persisted settings need no edits.
$Map = @(
    [pscustomobject]@{ Name = 'engine-data'; Source = Join-Path $env:LOCALAPPDATA 'Docker'; Dest = Join-Path $Root 'data' }
    [pscustomobject]@{ Name = 'program'; Source = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop'; Dest = Join-Path $Root 'app' }
    [pscustomobject]@{ Name = 'cli-config'; Source = Join-Path $env:USERPROFILE '.docker'; Dest = Join-Path $Root 'cli' }
    [pscustomobject]@{ Name = 'settings'; Source = Join-Path $env:APPDATA 'Docker'; Dest = Join-Path $Root 'settings' }
)

function Get-DockerProcess {
    Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match 'Docker|docker-credential|vpnkit|com\.docker' }
}

switch ($Phase) {

    'prep' {
        New-Item -ItemType Directory -Force -Path (Join-Path $Root '_migration') | Out-Null
        Write-Log "=== prep: start (Root=$Root) ==="
        foreach ($d in 'data', 'app', 'cli', 'settings', 'wsl\Ubuntu') {
            New-Item -ItemType Directory -Force -Path (Join-Path $Root $d) | Out-Null
        }
        # Keep a copy of the persisted settings so later troubleshooting has the original values.
        $src = Join-Path $env:APPDATA 'Docker\settings-store.json'
        if (Test-Path -LiteralPath $src) {
            Copy-Item -LiteralPath $src -Destination (Join-Path $Root '_migration\settings-store.json.bak') -Force
            Write-Log 'Backed up settings-store.json'
        }
        $running = @(Get-DockerProcess)
        if ($running.Count) {
            Write-Log "Stopping Docker processes: $(($running | ForEach-Object Name) -join ', ')"
            $running | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
        }
        else {
            Write-Log 'No Docker processes running'
        }
        $null = wsl --shutdown
        Start-Sleep -Seconds 3
        Write-Log 'wsl --shutdown issued'
        foreach ($m in $Map) {
            $s = Get-FolderStats $m.Source
            if ($s) { Write-Log ('PREP  {0,-11} {1} files / {2} GB  <- {3}' -f $m.Name, $s.Count, $s.GB, $m.Source) }
            else { Write-Log "PREP  MISSING source for $($m.Name): $($m.Source)" }
        }
        $ubuntu = Get-FolderStats (Join-Path $env:LOCALAPPDATA 'wsl')
        if ($ubuntu) { Write-Log ('PREP  ubuntu-wsl  {0} files / {1} GB' -f $ubuntu.Count, $ubuntu.GB) }
        $freeG = (Get-PSDrive -Name G).Free / 1GB
        Write-Log ('PREP  free space on G: {0:N1} GB' -f $freeG)
        if ($freeG -lt 30) { throw 'Less than 30 GB free on G: - aborting before any copy' }
        Write-Log '=== prep: done, safe to run -Phase move ==='
    }

    'move' {
        $running = @(Get-DockerProcess)
        if ($running.Count) {
            throw "Docker is still running: $(($running | ForEach-Object Name) -join ', '). Run -Phase prep first."
        }
        $items = if ($Only.Count) { @($Map | Where-Object { $Only -contains $_.Name }) } else { @($Map) }
        foreach ($m in $items) {
            if (-not (Test-Path -LiteralPath $m.Source)) { Write-Log "SKIP  $($m.Name): source absent"; continue }
            $existing = Get-Item -LiteralPath $m.Source -Force
            if ($existing.LinkType -eq 'Junction') {
                Write-Log "SKIP  $($m.Name): already a junction -> $($existing.Target)"
                continue
            }

            $before = Get-FolderStats $m.Source
            Write-Log ('COPY  {0}: {1} files / {2} GB -> {3}' -f $m.Name, $before.Count, $before.GB, $m.Dest)
            $null = & robocopy $m.Source $m.Dest /E /COPY:DAT /DCOPY:DAT /XJ /R:1 /W:1 /MT:16 /NP /NFL /NDL /LOG+:$script:Log
            $code = $LASTEXITCODE
            if ($code -ge 8) { throw "robocopy failed for $($m.Name) with exit code $code" }
            Write-Log "COPY  $($m.Name): robocopy exit $code (0-7 means success)"

            $after = Get-FolderStats $m.Dest
            if ($after.Bytes -ne $before.Bytes -or $after.Count -ne $before.Count) {
                throw ('COPY  {0}: verification mismatch (source {1} files/{2} B, dest {3} files/{4} B) - aborting, nothing renamed' -f `
                    $m.Name, $before.Count, $before.Bytes, $after.Count, $after.Bytes)
            }
            Write-Log ('COPY  {0}: verified identical ({1} files / {2} GB)' -f $m.Name, $after.Count, $after.GB)

            $old = "$($m.Source).old"
            if (Test-Path -LiteralPath $old) { throw "Refusing to overwrite existing $old" }
            # A transient handle (antivirus or indexer opening the folder) makes the first rename attempt fail
            # with ACCESS_DENIED, so the rename is retried before giving up.
            for ($attempt = 1; ; $attempt++) {
                try {
                    Rename-Item -LiteralPath $m.Source -NewName (Split-Path $old -Leaf) -ErrorAction Stop
                    break
                }
                catch {
                    if ($attempt -ge 10) { throw "Cannot rename $($m.Name) source after $attempt attempts : $($_.Exception.Message)" }
                    Start-Sleep -Seconds 3
                }
            }
            Write-Log "MOVE  $($m.Name): renamed source to $old"
            $null = New-Item -ItemType Junction -Path $m.Source -Target $m.Dest
            Write-Log "LINK  $($m.Name): junction $($m.Source) -> $($m.Dest)"
        }
        Write-Log ('=== move: done, processed: ' + (($items | ForEach-Object Name) -join ', ') + ' ===')
    }

    'ubuntu' {
        # Native WSL relocation (WSL 2.5+): re-registers the distro at the new path, no tar round-trip.
        $distros = & wsl -l -v 2>&1 | Out-String
        if ($distros -match 'Ubuntu\s+Running') {
            $null = wsl --terminate Ubuntu
            Start-Sleep -Seconds 2
            Write-Log 'Terminated Ubuntu distro'
        }
        $target = Join-Path $Root 'wsl\Ubuntu'
        $null = & wsl --manage Ubuntu --move $target 2>&1
        Write-Log "MOVE  ubuntu-wsl: requested move to $target"
        $reg = Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' |
            ForEach-Object { Get-ItemProperty $_.PSPath } |
            Where-Object { $_.DistributionName -eq 'Ubuntu' }
        Write-Log "CHECK Ubuntu BasePath now: $($reg.BasePath)"
        if ($reg.BasePath -notlike "*$target*") { throw "Ubuntu was not moved (BasePath still $($reg.BasePath))" }
        Write-Log '=== ubuntu: done ==='
    }

    'verify' {
        foreach ($m in $Map) {
            $item = Get-Item -LiteralPath $m.Source -Force -ErrorAction SilentlyContinue
            if (-not $item) { Write-Log "FAIL  $($m.Name): path missing"; continue }
            if ($item.LinkType -eq 'Junction') {
                $reachable = Get-FolderStats $m.Source
                Write-Log ('OK    {0,-11} junction -> {1} ({2} files / {3} GB reachable)' -f `
                    $m.Name, $item.Target, $reachable.Count, $reachable.GB)
            }
            else {
                $s = Get-FolderStats $m.Source
                Write-Log ('WARN  {0,-11} is a real folder again ({1} GB) - junction not applied?' -f $m.Name, $s.GB)
            }
        }
        foreach ($v in (Get-ChildItem -Path (Join-Path $Root 'data') -Recurse -Filter *.vhdx -ErrorAction SilentlyContinue)) {
            Write-Log ('DISK  {0}  {1:N2} GB' -f $v.FullName, ($v.Length / 1GB))
        }
        Write-Log ('BIN   docker.exe resolves to: ' + (Get-Command docker.exe -ErrorAction SilentlyContinue).Source)
        $svc = Get-Service -Name 'com.docker.service' -ErrorAction SilentlyContinue
        if ($svc) { Write-Log "SVC   com.docker.service status: $($svc.Status)" }
        else { Write-Log 'SVC   com.docker.service not installed (per-user install)' }
        $csum = (Get-PSDrive -Name C).Free / 1GB
        $gsum = (Get-PSDrive -Name G).Free / 1GB
        Write-Log ('DISK  free: C: {0:N1} GB, G: {1:N1} GB' -f $csum, $gsum)
        Write-Log '=== verify: done; launch Docker Desktop and re-check docker version/ps ==='
    }

    'cleanup' {
        # Only run after Docker Desktop starts, docker compose up works and nothing references C: anymore.
        $items = if ($Only.Count) { @($Map | Where-Object { $Only -contains $_.Name }) } else { @($Map) }
        foreach ($m in $items) {
            $old = "$($m.Source).old"
            if (Test-Path -LiteralPath $old) {
                $s = Get-FolderStats $old
                Remove-Item -LiteralPath $old -Recurse -Force
                Write-Log ('CLEAN removed {0} ({1} GB freed on C:)' -f $old, $s.GB)
            }
        }
        Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'wsl') -Force -ErrorAction SilentlyContinue |
            ForEach-Object { Write-Log "NOTE  leftover under AppData\Local\wsl: $($_.Name)" }
        Write-Log ('=== cleanup: done, processed: ' + (($items | ForEach-Object Name) -join ', ') + ' ===')
    }

    'rollback' {
        # WSL refuses to mount a VHD whose path traverses a junction (Wsl/Service/CreateInstance/MountDisk
        # ERROR_UNTRUSTED_MOUNT_POINT 0x800701c0), so any tree containing a .vhdx must be rolled back.
        $items = if ($Only.Count) { @($Map | Where-Object { $Only -contains $_.Name }) } else { @($Map) }
        foreach ($m in $items) {
            $old = "$($m.Source).old"
            $item = Get-Item -LiteralPath $m.Source -Force -ErrorAction SilentlyContinue
            if ($item -and $item.LinkType -eq 'Junction' -and (Test-Path -LiteralPath $old)) {
                $item.Delete()
                Rename-Item -LiteralPath $old -NewName (Split-Path $m.Source -Leaf)
                Write-Log "ROLLBACK restored $($m.Name) from $old"
            }
        }
        Write-Log ('=== rollback: done, processed: ' + (($items | ForEach-Object Name) -join ', ') + ' ===')
    }
}
