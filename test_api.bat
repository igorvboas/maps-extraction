@echo off
echo Enviando requisicao para a API...
curl -X POST "http://localhost:8000/search" -H "Content-Type: application/json" -d @test_payload.json
echo.
pause
