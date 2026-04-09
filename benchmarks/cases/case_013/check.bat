@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$e = [IO.File]::ReadAllText('%~dp0expected\src\slug.py');" ^
  "$a = [IO.File]::ReadAllText('src\slug.py');" ^
  "$e = $e.Replace([string][char]13, [string]::Empty);" ^
  "$a = $a.Replace([string][char]13, [string]::Empty);" ^
  "if ($e -ne $a) { exit 1 }"
if errorlevel 1 exit /b 1

echo PASS
