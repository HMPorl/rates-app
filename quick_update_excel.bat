@echo off
echo Quick Excel Update...

REM Check if Excel file exists
if not exist "Net rates Webapp.xlsx" (
    echo ERROR: Excel file not found!
    pause
    exit /b 1
)

REM Quick update with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2% %dt:~8,2%:%dt:~10,2%"

git add "Net rates Webapp.xlsx"
git commit -m "Excel update - %timestamp%"
git push origin main

if errorlevel 0 (
    echo SUCCESS! Excel file updated and pushed to Streamlit.
) else (
    echo ERROR occurred during update.
)

pause