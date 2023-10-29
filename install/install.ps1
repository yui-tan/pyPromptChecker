$directory = (Get-Item -Path $PSScriptRoot).FullName
$targetPath = (Split-Path -Path $directory)
$executePath = Join-Path $targetPath "venv\Scripts\pythonw.exe"
$packagePath = Join-Path $targetPath "pyPromptChecker"
$shortcutPath = Join-Path $targetPath "pyPromptChecker.lnk"
$commandPath = Join-Path $targetPath "pyPromptChecker\main.py"
$iconPath = Join-Path $targetPath "pyPromptChecker\icon\icon.ico"
$python = (python --version 2>&1)

Set-Location $targetPath

if (!($python -like 'Python 3.*')) {
    Write-Host "Python 3.x is not installed. Please install Python 3.x before running this script."
    Start-Process "https://www.python.org/"
    exit 1
}

if (!(Test-Path -Path ".\venv" -PathType Container)) {
    python -m pip install --upgrade pip
    Write-Host "Installing venv..."
    python -m venv venv
    Write-Host "Activating venv..."
    . .\venv\Scripts\Activate
    Write-Host "Installing pyPromptChecker..."
    python -m pip install --upgrade pip
    pip install -e .
    Write-Host "Instalation has been done."
}

if (!(Test-Path -Path $shortcutPath -PathType Leaf)) {
    Write-Host "Shortcut creating..."
    $WshShell = New-Object -ComObject WScript.Shell
    $shortcut = $WshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $executePath
    $shortcut.Arguments = $commandPath
    $shortcut.IconLocation = $iconPath
    $shortcut.WorkingDirectory = $packagePath
    $shortcut.Save()
    Write-Host "Shortcut created at $shortcutPath"
}

Write-Host "Everything has been done!"
exit 0
