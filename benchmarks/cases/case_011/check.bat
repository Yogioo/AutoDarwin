@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$e = [IO.File]::ReadAllText('%~dp0expected\config.json');" ^
  "$a = [IO.File]::ReadAllText('config.json');" ^
  "$e2 = [IO.File]::ReadAllText('%~dp0workspace\config.example.json');" ^
  "$a2 = [IO.File]::ReadAllText('config.example.json');" ^
  "$e = $e.Replace([string][char]13, [string]::Empty);" ^
  "$a = $a.Replace([string][char]13, [string]::Empty);" ^
  "$e2 = $e2.Replace([string][char]13, [string]::Empty);" ^
  "$a2 = $a2.Replace([string][char]13, [string]::Empty);" ^
  "if ($e -ne $a -or $e2 -ne $a2) { exit 1 }"
if errorlevel 1 exit /b 1

echo PASS
