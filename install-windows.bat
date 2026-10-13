@echo off
rem ============================================================
rem  NEXUS - instalacion en Windows (un solo doble clic)
rem
rem  1) crea el acceso directo "NEXUS" en el Escritorio y en el
rem     menu Inicio (con el icono de la app)
rem  2) prepara y abre NEXUS: instala Python si falta, levanta el
rem     backend y abre la app en una ventana propia
rem
rem  No necesita permisos de administrador y no toca nada del
rem  sistema fuera de tu carpeta de usuario.
rem ============================================================
setlocal
set "APP_DIR=%~dp0"
title NEXUS - instalacion

echo.
echo   NEXUS - instalacion en Windows
echo   -------------------------------
echo.
rem Los ficheros que vienen dentro de un ZIP descargado llevan una marca de
rem internet que a veces impide ejecutarlos. Se quita (no hace falta ser
rem administrador y no cambia nada mas).
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -Path '%APP_DIR%' -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue" >nul 2>nul
echo.
echo   [1/2] Creando los accesos directos...
cscript //nologo "%APP_DIR%tools\crear-accesos-windows.vbs"
if errorlevel 1 echo         Aviso: no se han podido crear los accesos directos.

echo   [2/2] Preparando y abriendo NEXUS...
echo.
call "%APP_DIR%run.bat"
set "RC=%errorlevel%"

echo.
if "%RC%"=="0" (
  echo   Listo. A partir de ahora abre NEXUS con el acceso directo
  echo   "NEXUS" del Escritorio o del menu Inicio.
  echo   Se abre en una ventana propia, sin barra del navegador.
) else (
  echo   NEXUS no ha podido arrancar: revisa el aviso de arriba.
)
echo.
echo   Esta ventana se puede cerrar.
pause
exit /b %RC%
