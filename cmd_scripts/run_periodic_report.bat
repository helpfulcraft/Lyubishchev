@echo off
cd /d %~dp0

REM This script generates a periodic report.
REM It can be run with an argument: run_periodic_report.bat [period]
REM where [period] can be: week, month, last7days
REM If no period is provided, it will prompt for input.

set "period=%1"
if defined period (
    goto :run_script
)

:prompt
echo.
set /p period="Enter report period (week, month, last7days): "
if not defined period (
    echo Invalid input. Please try again.
    goto :prompt
)

:run_script
echo Generating %period% report...
python scripts/generate_periodic_report.py --period %period%

echo.
echo Periodic report generation complete.
pause 