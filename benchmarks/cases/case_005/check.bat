@echo off
setlocal

if exist output rmdir /s /q output
if exist data\output rmdir /s /q data\output

python tools\export_report.py data\sample.json output\report.txt
if errorlevel 1 exit /b 1

if not exist output\report.txt (
  echo output\report.txt not found 1>&2
  exit /b 1
)

findstr /C:"title=weekly" output\report.txt >nul || exit /b 1
findstr /C:"count=3" output\report.txt >nul || exit /b 1

if exist data\output\report.txt (
  echo wrong output path produced 1>&2
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$e = [IO.File]::ReadAllText('%~dp0expected\tools\export_report.py');" ^
  "$a = [IO.File]::ReadAllText('tools\export_report.py');" ^
  "$e = $e.Replace([string][char]13, [string]::Empty);" ^
  "$a = $a.Replace([string][char]13, [string]::Empty);" ^
  "if ($e -ne $a) { exit 1 }"
if errorlevel 1 exit /b 1

echo PASS
