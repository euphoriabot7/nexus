@echo off
rem ============================================================
rem  NEXUS · trae la ultima version desde GitHub (Windows)
rem  Si la carpeta es un clon de git, hace "git pull".
rem  Si se descargo en zip, baja el paquete y lo copia encima.
rem  No toca tus chats, tus claves ni tu configuracion.
rem ============================================================
setlocal enabledelayedexpansion
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"
set "REPO=euphoriabot7/nexus"
set "ZIPURL=https://github.com/%REPO%/archive/refs/heads/main.zip"
set "TMP=%TEMP%\nexus-update-%RANDOM%"

echo NEXUS - actualizando desde github.com/%REPO%

where git >nul 2>nul
if not errorlevel 1 (
  if exist ".git" (
    for /f "delims=" %%H in ('git rev-parse --short HEAD 2^>nul') do set "ANTES=%%H"
    git pull --ff-only
    if errorlevel 1 (
      echo   No se pudo actualizar con git ^(tienes cambios locales^). Revisa: git status
      pause
      exit /b 1
    )
    for /f "delims=" %%H in ('git rev-parse --short HEAD 2^>nul') do set "DESPUES=%%H"
    if "!ANTES!"=="!DESPUES!" (
      echo   Ya tenias la ultima version ^(!ANTES!^).
    ) else (
      echo   Actualizado: !ANTES! -^> !DESPUES!
      echo   Reinicia NEXUS ^(cierra la ventana y vuelve a abrirlo^) para usarlo.
    )
    pause
    exit /b 0
  )
)

echo   Descargando el paquete...
mkdir "%TMP%" >nul 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { Invoke-WebRequest -Uri '%ZIPURL%' -OutFile '%TMP%\nexus.zip' -UseBasicParsing } catch { exit 1 }"
if errorlevel 1 (
  echo   No se pudo descargar. Comprueba tu conexion.
  rmdir /s /q "%TMP%" >nul 2>nul
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Expand-Archive -Path '%TMP%\nexus.zip' -DestinationPath '%TMP%\suelto' -Force"
set "ORIGEN="
for /d %%D in ("%TMP%\suelto\nexus-*") do set "ORIGEN=%%D"
if not defined ORIGEN (
  echo   El paquete descargado no tiene la forma esperada.
  rmdir /s /q "%TMP%" >nul 2>nul
  pause
  exit /b 1
)
echo   Copiando archivos...
robocopy "%ORIGEN%" "%APP_DIR%" /E /XD .git __pycache__ /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
  echo   Hubo problemas al copiar. Revisa los permisos de la carpeta.
) else (
  echo   Actualizado. Version instalada:
  type "%APP_DIR%VERSION" 2>nul
  echo   Reinicia NEXUS ^(cierra la ventana y vuelve a abrirlo^) para usarlo.
)
rmdir /s /q "%TMP%" >nul 2>nul
pause
