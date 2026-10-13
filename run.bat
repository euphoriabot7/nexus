@echo off
rem ============================================================
rem  NEXUS - arranque en Windows
rem
rem  - Levanta el servidor si no esta corriendo.
rem  - Abre la app en una VENTANA PROPIA (Edge/Chrome/Brave/Vivaldi
rem    en modo aplicacion: sin barra de direcciones ni pestanas).
rem  - Si no hay Python, lo instala solo (winget) o te lleva a la
rem    pagina de descarga.
rem
rem  Uso normal : doble clic en el acceso directo "NEXUS".
rem  Uso manual : run.bat            (deja la ventana para leer avisos)
rem               run.bat --oculto   (sin consola; lo usa NEXUS.vbs)
rem
rem  Truco de cmd que costo un rato: "if not defined X" da FALSO si X
rem  existe pero esta vacia, asi que aqui se compara con !X! (o "").
rem ============================================================
setlocal enabledelayedexpansion
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"
set "SILENCIOSO="
if /i "%~1"=="--oculto" set "SILENCIOSO=1"
if "%NEXUS_PORT%"=="" set "NEXUS_PORT=8765"
set "URL=http://127.0.0.1:%NEXUS_PORT%"
if "%NEXUS_DATA%"=="" set "NEXUS_DATA=%LOCALAPPDATA%\NEXUS"
set "LOG=%NEXUS_DATA%\server.log"
set "LOG_ARRANQUE=%NEXUS_DATA%\server-arranque.log"
if not exist "%NEXUS_DATA%" mkdir "%NEXUS_DATA%" >nul 2>nul

rem ---------- 1) busca Python 3.9 o superior ----------
rem Si defines NEXUS_PYTHON con la ruta a python.exe, se usa esa y no se
rem busca nada (util en equipos donde la deteccion no acierte).
if not "!NEXUS_PYTHON!"=="" if exist "!NEXUS_PYTHON!" call :usa_python "!NEXUS_PYTHON!"
if "!PY!"=="" call :busca_python
if "!PY!"=="" call :instala_python
if "!PY!"=="" call :busca_python
if "!PY!"=="" goto :sin_python
%PY% -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>nul
if errorlevel 1 goto :python_viejo

rem ---------- 2) arranca el backend si no responde ----------
%PY% -c "import urllib.request as u,sys;sys.exit(0 if u.urlopen('%URL%/api/health',timeout=2).status==200 else 1)" >nul 2>nul
if not errorlevel 1 goto :abrir

if not defined SILENCIOSO echo   Arrancando NEXUS...
rem sin /b: el proceso sobrevive al cierre de esta ventana (pythonw no abre consola).
rem el arranque escribe en server-arranque.log; el servidor ya escribe server.log
start "NEXUS" %PYW% "%APP_DIR%server.py" >>"%LOG_ARRANQUE%" 2>&1
set "LISTO="
for /l %%i in (1,1,60) do (
  if "!LISTO!"=="" (
    %PY% -c "import urllib.request as u,sys;sys.exit(0 if u.urlopen('%URL%/api/health',timeout=2).status==200 else 1)" >nul 2>nul
    if not errorlevel 1 set "LISTO=1"
    rem Espera de 1 s con el propio Python: "timeout" falla si no hay consola.
    %PY% -c "import time;time.sleep(1)" >nul 2>nul
  )
)
if "!LISTO!"=="" goto :no_arranca

:abrir
rem ---------- 3) abre la ventana de la app ----------
rem Ojo: nada de meter estas rutas en un bucle "for %%B in (...)":
rem el parentesis de %ProgramFiles(x86)% rompe el analisis del comando.
set "BROWSER="
if not defined BROWSER if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "BROWSER=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "BROWSER=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER if exist "%LocalAppData%\Microsoft\Edge\Application\msedge.exe" set "BROWSER=%LocalAppData%\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "BROWSER=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "BROWSER=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "BROWSER=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe" set "BROWSER=%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"
if not defined BROWSER if exist "%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe" set "BROWSER=%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"
if not defined BROWSER if exist "%ProgramFiles%\Vivaldi\Application\vivaldi.exe" set "BROWSER=%ProgramFiles%\Vivaldi\Application\vivaldi.exe"
if not defined BROWSER if exist "%LocalAppData%\Vivaldi\Application\vivaldi.exe" set "BROWSER=%LocalAppData%\Vivaldi\Application\vivaldi.exe"
if defined BROWSER (
  if not defined SILENCIOSO echo   Abriendo NEXUS en una ventana propia...
  start "" "%BROWSER%" --app="%URL%" --user-data-dir="%NEXUS_DATA%\browser-profile" --no-first-run --no-default-browser-check --window-size=1360,880
) else (
  if not defined SILENCIOSO echo   No encuentro Edge, Chrome, Brave ni Vivaldi: abro la app en tu navegador de siempre.
  start "" "%URL%"
)
exit /b 0

rem ---------- salidas de error ----------
:sin_python
call :fallo "No encuentro Python 3.9 o superior. Descargalo de https://www.python.org/downloads/ marcando la casilla 'Add python.exe to PATH'."
exit /b 1

:python_viejo
call :fallo "Tu Python es anterior a 3.9. Actualizalo desde https://www.python.org/downloads/"
exit /b 1

:no_arranca
call :fallo "NEXUS no ha arrancado. Registro: %LOG%  (detalles del arranque: %LOG_ARRANQUE%)"
exit /b 1

rem ============================================================
rem  Subrutinas
rem ============================================================

:usa_python
rem Fija PY/PYW/PY_EXE a partir de la ruta indicada en %~1.
set "PY_EXE=%~1"
goto :bp_exe

:busca_python
rem Deja en PY el comando a usar ("py -3" o la ruta a python.exe), en PYW su
rem equivalente sin consola y en PY_EXE la ruta. Descarta el senuelo de la
rem Microsoft Store (...\WindowsApps\python.exe), que no es un Python real.
set "PY="
set "PYW="
set "PY_EXE="
rem Ojo: no basta con que "where" encuentre algo (hay equipos donde el
rem propio Windows devuelve una ruta que no es un Python real). Cada
rem candidato se comprueba ejecutandolo.
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not "!PY!"=="" goto :bp_launcher
for /f "delims=" %%W in ('where python 2^>nul ^| findstr /i /v "WindowsApps"') do if "!PY_EXE!"=="" set "PY_EXE=%%W"
for /f "delims=" %%W in ('where python3 2^>nul ^| findstr /i /v "WindowsApps"') do if "!PY_EXE!"=="" set "PY_EXE=%%W"
if not "!PY_EXE!"=="" goto :bp_exe
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set "PY_EXE=%%D\python.exe"
if not "!PY_EXE!"=="" goto :bp_exe
for /d %%D in ("%ProgramFiles%\Python3*") do if exist "%%D\python.exe" set "PY_EXE=%%D\python.exe"
if not "!PY_EXE!"=="" goto :bp_exe
where python >nul 2>nul
if not errorlevel 1 set "PY_EXE=python"
if "!PY_EXE!"=="" exit /b 1
:bp_exe
for %%A in ("%PY_EXE%") do set "PYW=%%~dpApythonw.exe"
if not exist "%PYW%" set "PYW=%PY_EXE%"
rem Comprobacion real: tiene que ejecutarse. Si no, no nos vale.
"%PY_EXE%" -c "" >nul 2>nul
if errorlevel 1 (set "PY=" & set "PYW=" & set "PY_EXE=" & exit /b 1)
rem Se guardan ya entre comillas: asi funcionan aunque la ruta lleve espacios.
set "PY="%PY_EXE%""
set "PYW="%PYW%""
exit /b 0
:bp_launcher
set "PYW=pyw -3"
py -3 -c "" >nul 2>nul
if errorlevel 1 (set "PY=" & set "PYW=" & exit /b 1)
exit /b 0

:instala_python
rem Instala Python automaticamente con winget (sin permisos de administrador).
where winget >nul 2>nul
if errorlevel 1 (
  if not defined SILENCIOSO (
    echo.
    echo   No hay Python y winget no esta disponible en este equipo.
    echo   Te abro la pagina de descarga: instala Python 3.9 o superior y
    echo   MARCA la casilla "Add python.exe to PATH", luego vuelve a abrir NEXUS.
    echo.
    start "" "https://www.python.org/downloads/"
  )
  exit /b 1
)
if not defined SILENCIOSO (
  echo.
  echo   No hay Python en este equipo: lo instalo automaticamente.
  echo   Puede tardar un par de minutos y no necesita permisos de administrador.
  echo   No cierres esta ventana.
  echo.
)
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
if errorlevel 1 winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
exit /b 0

:fallo
rem Mensaje de error visible (y guardado) sin depender de que haya consola.
echo.
echo   %~1
echo.
>"%NEXUS_DATA%\ultimo-error.txt" echo %~1
if not defined SILENCIOSO pause
exit /b 0
