@echo off
cd /d %~dp0
echo Processing log file...
python scripts/process_log.py
echo Building daily report...
python scripts/build_report.py
echo.
echo Daily report generation complete.
pause 