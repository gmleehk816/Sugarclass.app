# Start NewsCollect FastAPI Backend
# Port: 8000

Write-Host "🔌 Starting NewsCollect FastAPI Backend..." -ForegroundColor Cyan
Write-Host "   Port: 8000" -ForegroundColor Gray
Write-Host "   URL: http://localhost:8000" -ForegroundColor Gray
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""

python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
