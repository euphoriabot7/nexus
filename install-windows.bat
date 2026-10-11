@echo off
rem ============================================================
rem  NEXUS · crea los accesos directos en Windows
rem  (Escritorio y menu Inicio) para no tener que buscar run.bat
rem ============================================================
setlocal
set "APP_DIR=%~dp0"
set "ICON=%APP_DIR%app\assets\icon.ico"
set "PS=powershell -NoProfile -ExecutionPolicy Bypass -Command"

%PS% "$app='%APP_DIR%run.bat'; $icon='%ICON%'; $w=New-Object -ComObject WScript.Shell; foreach ($dir in @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'))) { if (Test-Path $dir) { $lnk=$w.CreateShortcut((Join-Path $dir 'NEXUS.lnk')); $lnk.TargetPath=$app; $lnk.WorkingDirectory='%APP_DIR%'; if (Test-Path $icon) { $lnk.IconLocation=$icon }; $lnk.Description='NEXUS · consola de chat IA'; $lnk.Save() } }"

echo.
echo   Listo: busca NEXUS en el Escritorio o en el menu Inicio.
echo   (Se abre con doble clic; la primera vez tarda unos segundos.)
echo.
pause
