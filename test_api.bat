@echo off
echo Enviando requisicao para a API...
curl -X POST "http://localhost:8000/search" -H "Content-Type: application/json" -H "X-API-Key: 16a92fd2-a618-4a29-b185-150cfce82da7" -d @test_payload.json
echo.
pause
