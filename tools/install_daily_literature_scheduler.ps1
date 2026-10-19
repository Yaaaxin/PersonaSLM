[CmdletBinding(DefaultParameterSetName = "Describe")]
param(
    [Parameter(Mandatory = $true, ParameterSetName = "Install")]
    [switch]$Install,

    [Parameter(Mandatory = $true, ParameterSetName = "Verify")]
    [switch]$VerifyOnly,

    [Parameter(Mandatory = $true, ParameterSetName = "Describe")]
    [switch]$Describe,

    [ValidateNotNullOrEmpty()]
    [string]$TaskName = "PersonaSLM-Daily-Literature-Monitor",

    [ValidatePattern("^(?:[01]\d|2[0-3]):[0-5]\d$")]
    [string]$DailyAt = "04:23"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$contractVersion = "personaslm_windows_literature_scheduler_v1"
$taskPath = "\"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$runner = Join-Path $repoRoot "tools\run_daily_literature_monitor.ps1"
$powerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$actionArguments = '-NoLogo -NoProfile -NonInteractive -File "{0}"' -f $runner

$contract = [ordered]@{
    schema_version = $contractVersion
    task_name = $TaskName
    task_path = $taskPath
    schedule = [ordered]@{
        frequency = "DAILY"
        local_time = $DailyAt
        days_interval = 1
    }
    principal = [ordered]@{
        user_id = $currentUser
        logon_type = "INTERACTIVE_TOKEN"
        run_level = "LIMITED"
        stored_credentials = $false
    }
    action = [ordered]@{
        executable = $powerShell
        arguments = $actionArguments
        working_directory = $repoRoot
        wrapper = $runner
    }
    settings = [ordered]@{
        enabled = $true
        allow_start_on_batteries = $true
        stop_if_going_on_batteries = $false
        start_when_available = $true
        multiple_instances = "IGNORE_NEW"
        execution_time_limit_minutes = 20
    }
}

function ConvertTo-NormalizedPath {
    param([AllowEmptyString()][string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return ""
    }
    $expanded = [Environment]::ExpandEnvironmentVariables($Path)
    return [IO.Path]::GetFullPath($expanded).TrimEnd("\").ToLowerInvariant()
}

function ConvertFrom-TaskDuration {
    param($Value)

    if ($Value -is [TimeSpan]) {
        return $Value
    }
    $text = [string]$Value
    try {
        return [Xml.XmlConvert]::ToTimeSpan($text)
    }
    catch {
        return [TimeSpan]::Parse($text)
    }
}

function ConvertTo-AccountSid {
    param([string]$UserId)

    try {
        return ([Security.Principal.NTAccount]$UserId).Translate(
            [Security.Principal.SecurityIdentifier]
        ).Value
    }
    catch {
        return $null
    }
}

function Get-InstalledTask {
    Import-Module ScheduledTasks -ErrorAction Stop
    return Get-ScheduledTask -TaskName $TaskName -TaskPath $taskPath -ErrorAction SilentlyContinue
}

function Test-InstalledTask {
    param($Task)

    $violations = New-Object System.Collections.Generic.List[string]
    if ($null -eq $Task) {
        $violations.Add("TASK_NOT_FOUND") | Out-Null
        return [pscustomobject]@{ matches = $false; violations = @($violations) }
    }

    $actions = @($Task.Actions)
    if ($actions.Count -ne 1) {
        $violations.Add("ACTION_COUNT") | Out-Null
    }
    else {
        $action = $actions[0]
        if ((ConvertTo-NormalizedPath $action.Execute) -ne (ConvertTo-NormalizedPath $contract.action.executable)) {
            $violations.Add("ACTION_EXECUTABLE") | Out-Null
        }
        if ([string]$action.Arguments -ne $contract.action.arguments) {
            $violations.Add("ACTION_ARGUMENTS") | Out-Null
        }
        if ((ConvertTo-NormalizedPath $action.WorkingDirectory) -ne (ConvertTo-NormalizedPath $contract.action.working_directory)) {
            $violations.Add("ACTION_WORKING_DIRECTORY") | Out-Null
        }
    }

    $triggers = @($Task.Triggers)
    if ($triggers.Count -ne 1) {
        $violations.Add("TRIGGER_COUNT") | Out-Null
    }
    else {
        $trigger = $triggers[0]
        if ([int]$trigger.DaysInterval -ne 1) {
            $violations.Add("TRIGGER_DAYS_INTERVAL") | Out-Null
        }
        try {
            $actualTime = ([DateTimeOffset]::Parse([string]$trigger.StartBoundary)).ToString("HH:mm")
            if ($actualTime -ne $contract.schedule.local_time) {
                $violations.Add("TRIGGER_LOCAL_TIME") | Out-Null
            }
        }
        catch {
            $violations.Add("TRIGGER_START_BOUNDARY") | Out-Null
        }
    }

    $expectedSid = ConvertTo-AccountSid $contract.principal.user_id
    $actualSid = ConvertTo-AccountSid ([string]$Task.Principal.UserId)
    if ($null -eq $expectedSid -or $null -eq $actualSid -or $actualSid -ne $expectedSid) {
        $violations.Add("PRINCIPAL_USER") | Out-Null
    }
    if ([string]$Task.Principal.LogonType -notmatch "^(Interactive|InteractiveToken|3)$") {
        $violations.Add("PRINCIPAL_LOGON_TYPE") | Out-Null
    }
    if ([string]$Task.Principal.RunLevel -notmatch "^(Limited|0)$") {
        $violations.Add("PRINCIPAL_RUN_LEVEL") | Out-Null
    }

    $settings = $Task.Settings
    if (-not [bool]$settings.Enabled) {
        $violations.Add("SETTING_ENABLED") | Out-Null
    }
    if ([bool]$settings.DisallowStartIfOnBatteries) {
        $violations.Add("SETTING_BATTERY_START") | Out-Null
    }
    if ([bool]$settings.StopIfGoingOnBatteries) {
        $violations.Add("SETTING_BATTERY_STOP") | Out-Null
    }
    if (-not [bool]$settings.StartWhenAvailable) {
        $violations.Add("SETTING_START_WHEN_AVAILABLE") | Out-Null
    }
    if ([string]$settings.MultipleInstances -notmatch "^(IgnoreNew|2)$") {
        $violations.Add("SETTING_MULTIPLE_INSTANCES") | Out-Null
    }
    try {
        if ((ConvertFrom-TaskDuration $settings.ExecutionTimeLimit).TotalMinutes -ne 20) {
            $violations.Add("SETTING_EXECUTION_TIME_LIMIT") | Out-Null
        }
    }
    catch {
        $violations.Add("SETTING_EXECUTION_TIME_LIMIT") | Out-Null
    }

    return [pscustomobject]@{
        matches = ($violations.Count -eq 0)
        violations = @($violations)
    }
}

function Write-Result {
    param(
        [string]$Mode,
        [bool]$Matches,
        [string[]]$Violations,
        [bool]$Changed
    )

    [ordered]@{
        schema_version = $contractVersion
        mode = $Mode
        task_name = $TaskName
        contract_matches = $Matches
        changed = $Changed
        task_started = $false
        violations = @($Violations)
        contract = $contract
    } | ConvertTo-Json -Depth 6
}

if ($Describe) {
    Write-Result -Mode "DESCRIBE" -Matches $true -Violations @() -Changed $false
    return
}

if ($VerifyOnly) {
    $verification = Test-InstalledTask (Get-InstalledTask)
    Write-Result -Mode "VERIFY" -Matches $verification.matches -Violations $verification.violations -Changed $false
    if (-not $verification.matches) {
        exit 1
    }
    return
}

if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw "Literature-monitor wrapper is missing: $runner"
}

# Validate repository-local dependencies and the reviewed ledger before changing
# external scheduler state. This performs no network request or model inference.
$validationOutput = & $runner -ValidateOnly 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Literature-monitor validation failed: $($validationOutput -join [Environment]::NewLine)"
}

$existing = Get-InstalledTask
$before = Test-InstalledTask $existing
$changed = $false
if (-not $before.matches) {
    $at = [DateTime]::Today.Add([TimeSpan]::ParseExact($DailyAt, "hh\:mm", $null))
    $action = New-ScheduledTaskAction `
        -Execute $contract.action.executable `
        -Argument $contract.action.arguments `
        -WorkingDirectory $contract.action.working_directory
    $trigger = New-ScheduledTaskTrigger -Daily -At $at
    $principal = New-ScheduledTaskPrincipal `
        -UserId $contract.principal.user_id `
        -LogonType Interactive `
        -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
    $definition = New-ScheduledTask `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "PersonaSLM daily metadata-only literature discovery ($contractVersion)."
    Register-ScheduledTask `
        -TaskName $TaskName `
        -TaskPath $taskPath `
        -InputObject $definition `
        -Force | Out-Null
    $changed = $true
}

$after = Test-InstalledTask (Get-InstalledTask)
Write-Result -Mode "INSTALL" -Matches $after.matches -Violations $after.violations -Changed $changed
if (-not $after.matches) {
    exit 1
}
