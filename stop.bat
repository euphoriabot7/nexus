@echo off
rem NEXUS · detiene el backend en Windows
rem (necesita expansion retardada: sin ella !PID! no se sustituye y el taskkill falla)
setlocal enabledelayedexpansion
if "%NEXUS_PORT%"=="" set "NEXUS_PORT=8765"
if "%NEXUS_DATA%"=="" set "NEXUS_DATA=%LOCALAPPDATA%\NEXUS"
if exist "%NEXUS_DATA%\server.pid" (
  set /p PID=<"%NEXUS_DATA%\server.pid"
  taskkill /PID !PID! /F >nul 2>nul
  if errorlevel 1 (
    echo   El proceso !PID! ya no estaba en marcha.
  ) else (
    echo   NEXUS detenido (pid !PID!).
  )
  del "%NEXUS_DATA%\server.pid" >nul 2>nul
) else (
  echo   NEXUS no estaba en marcha (no hay server.pid).
)
timeout /t 3 >nul
