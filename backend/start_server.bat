@echo off
title SUTRAN Backend Server
cd /d "%~dp0"
:run
py -3 server.py
echo.
echo [INFO] El servidor se detuvo. Reiniciando en 2 segundos...
timeout /t 2 /nobreak >nul
goto run
