@echo off
rem ============================================================
rem  NEXUS · instalacion en Windows (un solo doble clic)
rem  1) comprueba que hay Python 3.9+
rem  2) crea el acceso directo "NEXUS" en el Escritorio y en el
rem     menu Inicio (con el icono de la app)
rem  3) abre NEXUS: backend + ventana propia (Edge/Chrome en modo
rem     aplicacion, sin barra de navegador)
rem ============================================================
setlocal enabledelayedexpansion
set "APP_DIR=%~dp0"
set "ICON=%APP_DIR%app\assets\icon.ico"
set "PS=powershell -NoProfile -ExecutionPolicy Bypass -Command"

rem ---------- 1) Python 3.9 o superior ----------
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY ( where python3 >nul 2>nul && set "PY=python3" )
if not defined PY (
  echo.
  echo   No encuentro Python en este equipo.
  echo   Se va a abrir la pagina de descarga: instala Python 3.9 o superior
  echo   y MARCA la casilla "Add python.exe to PATH", luego vuelve a
  echo   ejecutar este mismo archivo.
  echo.
  start "" "https://www.python.org/downloads/"
  pause
  exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>nul
if errorlevel 1 (
  echo   Tu Python es anterior a 3.9. Actualizalo desde python.org y repite.
  pause
  exit /b 1
)

rem ---------- 2) accesos directos ----------
rem  Sin argumentos: run.bat arranca el backend y abre la ventana.
%PS% "$app='%APP_DIR%run.bat'; $icon='%ICON%'; $w=New-Object -ComObject WScript.Shell; foreach ($dir in @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'))) { if (Test-Path $dir) { $lnk=$w.CreateShortcut((Join-Path $dir 'NEXUS.lnk')); $lnk.TargetPath=$app; $lnk.WorkingDirectory='%APP_DIR%'; if (Test-Path $icon) { $lnk.IconLocation=$icon }; $lnk.Description='NEXUS - consola de chat IA'; $lnk.Save() } }"
if errorlevel 1 (
  echo   No se han podido crear los accesos directos (puedes seguir usando run.bat).
)

echo.
echo   Listo. A partir de ahora: doble clic en "NEXUS" (Escritorio o menu Inicio).
echo   Abriendo NEXUS...
echo.

rem ---------- 3) abre la aplicacion ----------
call "%APP_DIR%run.bat"
exit /b %errorlevel%
