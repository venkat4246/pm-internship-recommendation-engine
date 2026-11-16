
@echo off
setlocal

cd /d "C:\Users\hp\Pictures\pm_internship_recommendation_engine"

if not exist logs mkdir logs

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set "STAMP=%%i"

if not defined STAMP set "STAMP=manual"

echo ================================================ >> "logs\pmis_update_%STAMP%.log"
echo INTERNMATCH AI - DAILY PMIS UPDATE >> "logs\pmis_update_%STAMP%.log"
echo Started: %DATE% %TIME% >> "logs\pmis_update_%STAMP%.log"

"C:\Python314\python.exe" discovery.py --import --yes >> "logs\pmis_update_%STAMP%.log" 2>&1

set "RESULT=%ERRORLEVEL%"
echo Finished: %DATE% %TIME% >> "logs\pmis_update_%STAMP%.log"
echo Exit code: %RESULT% >> "logs\pmis_update_%STAMP%.log"

exit /b %RESULT%
