# Run algorithm tests
Write-Host "Starting algorithm tests..." -ForegroundColor Green

# Activate the virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .venv\Scripts\Activate.ps1
} elseif (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & venv\Scripts\Activate.ps1
} else {
    Write-Host "No virtual environment found. Using system Python." -ForegroundColor Yellow
}

# Run the test script
Write-Host "Running algorithm tests..." -ForegroundColor Green
python test_all_algorithms.py

# Check if the tests completed successfully
if ($LASTEXITCODE -eq 0) {
    Write-Host "Tests completed successfully!" -ForegroundColor Green
    
    # Find the latest results directory
    $latestDir = Get-ChildItem -Directory -Filter "algorithm_test_results_*" | Sort-Object Name -Descending | Select-Object -First 1
    
    if ($latestDir) {
        Write-Host "Results saved to: $($latestDir.FullName)" -ForegroundColor Cyan
        Write-Host "Report file: $($latestDir.FullName)\evaluation_report.md" -ForegroundColor Cyan
        
        # Open the report file if requested
        $openReport = Read-Host "Do you want to open the evaluation report? (y/n)"
        if ($openReport -eq "y") {
            if (Test-Path "$($latestDir.FullName)\evaluation_report.md") {
                Start-Process "$($latestDir.FullName)\evaluation_report.md"
            } else {
                Write-Host "Report file not found!" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "No results directory found!" -ForegroundColor Red
    }
} else {
    Write-Host "Tests failed with exit code $LASTEXITCODE" -ForegroundColor Red
}

# Deactivate the virtual environment if it was activated
if (Test-Path Function:deactivate) {
    deactivate
}
