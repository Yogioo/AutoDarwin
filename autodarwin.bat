@echo off
setlocal EnableExtensions

set "PY_CMD="
where python >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD (
  where py >nul 2>nul && set "PY_CMD=py -3"
)
if not defined PY_CMD (
  echo [error] Python 3 is not installed or not on PATH.
  exit /b 1
)

if "%~1"=="" goto default_run

if /I "%~1"=="smoke" (
  call %PY_CMD% benchmarks\evaluator.py smoke %2 %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

if /I "%~1"=="core" (
  call %PY_CMD% benchmarks\evaluator.py core %2 %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

if /I "%~1"=="holdout" (
  call %PY_CMD% benchmarks\evaluator.py holdout %2 %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

if /I "%~1"=="smoke-ui" (
  call %PY_CMD% tools\eval_with_ui.py smoke %2 %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

if /I "%~1"=="core-ui" (
  call %PY_CMD% tools\eval_with_ui.py core %2 %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

if /I "%~1"=="holdout-ui" (
  call %PY_CMD% tools\eval_with_ui.py holdout %2 %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

if /I "%~1"=="eval-ui" (
  set "SUITE=%~2"
  if "%SUITE%"=="" set "SUITE=core"
  call %PY_CMD% tools\eval_with_ui.py %SUITE% %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

if /I "%~1"=="eval" (
  set "SUITE=%~2"
  if "%SUITE%"=="" set "SUITE=smoke"
  call %PY_CMD% benchmarks\evaluator.py %SUITE% %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

if /I "%~1"=="evolve" (
  call %PY_CMD% evolve.py %2 %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

if /I "%~1"=="replay" (
  call %PY_CMD% replay.py %2 %3 %4 %5 %6 %7 %8 %9
  exit /b %errorlevel%
)

rem Fallback: keep old behavior (pass through evolve args)
call %PY_CMD% evolve.py %*
exit /b %errorlevel%

:default_run
rem Default daily command uses core suite
call %PY_CMD% evolve.py --suite core
exit /b %errorlevel%
