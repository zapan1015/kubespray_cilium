# Cilium Kubernetes Cluster Setup Environment
Write-Host "Cilium Kubernetes Cluster Setup Environment" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

& "venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "가상 환경이 활성화되었습니다." -ForegroundColor Yellow
Write-Host "사전 요구사항을 확인하려면: python scripts\check_prerequisites.py" -ForegroundColor Cyan
Write-Host ""