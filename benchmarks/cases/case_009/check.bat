@echo off
setlocal

if not exist answer.txt (
  echo answer.txt not found 1>&2
  exit /b 1
)

set /p ANSWER=<answer.txt
if /I not "%ANSWER%"=="config/settings.py" (
  echo unexpected answer: %ANSWER% 1>&2
  exit /b 1
)

echo PASS
