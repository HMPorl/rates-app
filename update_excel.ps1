# Excel Update PowerShell Script
Write-Host "Excel File Update Script" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# Check if Excel file exists
if (-not (Test-Path "Net rates Webapp.xlsx")) {
    Write-Host "ERROR: Excel file not found!" -ForegroundColor Red
    Write-Host "Make sure you're running this from the correct directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for changes
$status = git status --porcelain "Net rates Webapp.xlsx"
if (-not $status) {
    Write-Host "No changes detected in Excel file." -ForegroundColor Yellow
    Write-Host "Make sure you saved your Excel file before running this script." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 0
}

Write-Host "Excel file changes detected!" -ForegroundColor Green

# Get commit message
$commitMsg = Read-Host "Enter description of your changes (or press Enter for default)"
if (-not $commitMsg) {
    $commitMsg = "Updated Excel data file"
}

Write-Host "`nProcessing your update..." -ForegroundColor Cyan

try {
    # Stage file
    Write-Host "[1/4] Staging Excel file..." -ForegroundColor Yellow
    git add "Net rates Webapp.xlsx"
    
    # Commit
    Write-Host "[2/4] Committing changes..." -ForegroundColor Yellow
    git commit -m "Update Excel data - $commitMsg"
    
    # Push
    Write-Host "[3/4] Pushing to GitHub..." -ForegroundColor Yellow
    git push origin main
    
    # Success
    Write-Host "[4/4] SUCCESS!" -ForegroundColor Green
    Write-Host "`nExcel file updated successfully!" -ForegroundColor Green
    Write-Host "Streamlit Cloud will redeploy your app within 1-3 minutes." -ForegroundColor Cyan
    Write-Host "`nMonitor deployment at: https://share.streamlit.io/" -ForegroundColor Blue
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Read-Host "`nPress Enter to exit"