Write-Host "ShiftFair V2 startup helper" -ForegroundColor Green
Write-Host "1. Keep LocalStack running on port 4566."
Write-Host "2. Create/seed ShiftFairV2Table."
Write-Host "3. Run: sam build --no-cached"
Write-Host "4. Run: sam local start-api --port 3001"
Write-Host "5. Frontend: cd frontend; python -m http.server 5501"
