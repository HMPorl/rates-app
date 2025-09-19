@echo off
echo =====================================
echo Excel File Update Script
echo =====================================
echo.

REM Check if we're in the right directory
if not exist "Net rates Webapp.xlsx" (
    echo ERROR: Excel file not found!
    echo Make sure you're running this from the correct directory.
    echo Expected file: Net rates Webapp.xlsx
    pause
    exit /b 1
)

REM Check if Excel file was recently modified
echo Checking Excel file status...
git status --porcelain "Net rates Webapp.xlsx" > temp_status.txt
set /p file_status=<temp_status.txt
del temp_status.txt

if "%file_status%"=="" (
    echo.
    echo No changes detected in Excel file.
    echo Make sure you saved your Excel file before running this script.
    echo.
    pause
    exit /b 0
)

echo Excel file changes detected!
echo.

REM Get commit message from user
set /p commit_msg="Enter description of your changes (e.g., 'Updated September pricing'): "

if "%commit_msg%"=="" (
    set commit_msg=Updated Excel data file
)

echo.
echo =====================================
echo Processing your update...
echo =====================================

REM Stage the Excel file
echo [1/4] Staging Excel file...
git add "Net rates Webapp.xlsx"
if errorlevel 1 (
    echo ERROR: Failed to stage Excel file
    pause
    exit /b 1
)

REM Commit the changes
echo [2/4] Committing changes...
git commit -m "Update Excel data - %commit_msg%"
if errorlevel 1 (
    echo ERROR: Failed to commit changes
    pause
    exit /b 1
)

REM Push to GitHub
echo [3/4] Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo ERROR: Failed to push to GitHub
    echo You may need to pull remote changes first.
    echo Try running: git pull origin main
    pause
    exit /b 1
)

REM Success message
echo [4/4] SUCCESS! 
echo.
echo =====================================
echo Excel file updated successfully!
echo =====================================
echo.
echo Your changes have been pushed to GitHub.
echo Streamlit Cloud will automatically redeploy your app.
echo.
echo You can monitor the deployment at:
echo https://share.streamlit.io/
echo.
echo The app should update within 1-3 minutes.
echo.
pause