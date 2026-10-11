@echo off
rem ============================================================
rem  NEXUS · arranque en Windows
rem  Levanta el servidor si hace falta y abre la ventana de la app
rem  (Microsoft Edge o Chrome en modo aplicacion, sin barra del navegador).
rem  Solo necesita Python 3.9 o superior instalado.
rem ============================================================
setlocal enabledelayedexpansion
set "APP_DIR=%~dp0"
if "%NEXUS_PORT%"=="" set "NEXUS_PORT=8765"
set "URL=http://127.0.0.1:%NEXUS_PORT%"
if "%NEXUS_DATA%"=="" set "NEXUS_DATA=%LOCALAPPDATA%\NEXUS"
set "LOG=%NEXUS_DATA%\server.log"
set "PIDFILE=%NEXUS_DATA%\server.pid"
if not exist "%NEXUS_DATA%" mkdir "%NEXUS_DATA%" >nul 2>nul

rem ---------- 1) busca Python 3.9+ ----------
set "PY="
set "PYW="
where py >nul 2>nul && ( set "PY=py -3" & set "PYW=py -3w" )
if not defined PY ( where python >nul 2>nul && ( set "PY=python" & set "PYW=pythonw" ) )
if not defined PY ( where python3 >nul 2>nul && ( set "PY=python3" & set "PYW=python3w" ) )
if not defined PY (
  echo.
  echo   No encuentro Python 3 en este equipo.
  echo   Descargalo de https://www.python.org/downloads/  ^(marca "Add python.exe to PATH"^)
  echo.
  start "" "https://www.python.org/downloads/"
  pause
  exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>nul
if errorlevel 1 (
  echo   Tu Python es anterior a 3.9. Actualizalo desde python.org
  pause
  exit /b 1
)

rem ---------- 2) arranca el backend si no responde ----------
%PY% -c "import urllib.request as u,sys;sys.exit(0 if u.urlopen('%URL%/api/health',timeout=2).status==200 else 1)" >nul 2>nul
if errorlevel 1 (
  echo   Arrancando NEXUS...
  start "NEXUS backend" /b %PYW% "%APP_DIR%server.py" >>"%LOG%" 2>&1
  set "LISTO="
  for /l %%i in (1,1,60) do (
    if not defined LISTO (
      %PY% -c "import urllib.request as u,sys;sys.exit(0 if u.urlopen('%URL%/api/health',timeout=2).status==200 else 1)" >nul 2>nul
      if not errorlevel 1 set "LISTO=1"
      if not defined LISTO timeout /t 1 /nobreak >nul
    )
  )
  if not defined LISTO (
    echo   NEXUS no ha arrancado. Revisa el registro: %LOG%
    pause
    exit /b 1
  )
)

rem ---------- 3) abre la ventana de la app ----------
set "BROWSER="
for %%B in (
  "%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"
  "%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"
  "%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"
  "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
  "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
  "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
) do (
  if not defined BROWSER if exist %%B set "BROWSER=%%B"
)
if defined BROWSER (
  start "" "%BROWSER%" --app="%URL%" --user-data-dir="%NEXUS_DATA%\browser-profile" --no-first-run --no-default-browser-check --window-size=1360,880
) else (
  echo   No encuentro Edge ni Chrome: abro la app en tu navegador de siempre.
  start "" "%URL%"
)
exit /b 0
