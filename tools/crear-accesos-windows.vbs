' ============================================================
'  NEXUS - crea los accesos directos del Escritorio y del menu Inicio
'
'  Se llama desde install-windows.bat (con cscript, para que los
'  mensajes salgan por la consola y no en ventanas emergentes).
'
'  Apunta a NEXUS.vbs, que arranca run.bat sin consola.
'  Si Windows no deja crear el .lnk (politicas, antivirus, WSH tocado),
'  copia NEXUS.vbs tal cual: al ser un .vbs se abre igual con doble clic
'  y sin ventana negra.
'
'  Cada carpeta se trata por separado y a prueba de fallos: si una no
'  esta disponible, se sigue con la otra.
' ============================================================
Option Explicit

Dim sh, fso, carpeta, destino, icono, lnk, carpetas, n, i, dir, hechos, avisos, wscriptexe, rutaLnk, rutaVbs, d

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Este archivo vive en <app>\tools: subo un nivel si run.bat no esta aqui.
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
If Not fso.FileExists(fso.BuildPath(carpeta, "run.bat")) Then
  carpeta = fso.GetParentFolderName(carpeta)
End If

destino = fso.BuildPath(carpeta, "NEXUS.vbs")
icono   = fso.BuildPath(carpeta, "app\assets\icon.ico")

If Not fso.FileExists(destino) Then
  WScript.Echo "No encuentro NEXUS.vbs en " & carpeta
  WScript.Quit 1
End If

wscriptexe = sh.ExpandEnvironmentStrings("%SystemRoot%\System32\wscript.exe")

' Carpeta especial a prueba de fallos: si el sistema no la da, devuelve "".
ReDim carpetas(2)
n = 0
d = CarpetaEspecial(sh, "Desktop")
If Len(d) > 0 Then carpetas(n) = d : n = n + 1
d = CarpetaEspecial(sh, "Programs")
If Len(d) > 0 Then carpetas(n) = d : n = n + 1

hechos = 0
avisos = ""

For i = 0 To n - 1
  dir = carpetas(i)
  If fso.FolderExists(dir) Then
    rutaLnk = fso.BuildPath(dir, "NEXUS.lnk")

    On Error Resume Next
    Set lnk = sh.CreateShortcut(rutaLnk)
    lnk.TargetPath       = wscriptexe
    lnk.Arguments        = """" & destino & """"
    lnk.WorkingDirectory = carpeta
    lnk.Description      = "NEXUS - consola de chat IA"
    lnk.WindowStyle      = 1
    If fso.FileExists(icono) Then lnk.IconLocation = icono
    lnk.Save
    Err.Clear
    On Error Goto 0

    If fso.FileExists(rutaLnk) Then
      hechos = hechos + 1
    Else
      ' Plan B: dejar el propio NEXUS.vbs en el Escritorio / menu Inicio.
      rutaVbs = fso.BuildPath(dir, "NEXUS.vbs")
      On Error Resume Next
      fso.CopyFile destino, rutaVbs, True
      Err.Clear
      On Error Goto 0
      If fso.FileExists(rutaVbs) Then
        hechos = hechos + 1
        avisos = avisos & "  En " & dir & " se ha dejado NEXUS.vbs (doble clic igual)." & vbCrLf
      Else
        avisos = avisos & "  No se ha podido escribir en " & dir & vbCrLf
      End If
    End If
  End If
Next

If hechos = 0 Then
  WScript.Echo "No se ha podido crear ningun acceso directo."
  If Len(avisos) > 0 Then WScript.Echo avisos
  WScript.Quit 1
End If

WScript.Echo "Accesos directos creados: " & hechos
If Len(avisos) > 0 Then WScript.Echo avisos
WScript.Quit 0

' ------------------------------------------------------------
Function CarpetaEspecial(objeto, nombre)
  Dim v
  v = ""
  On Error Resume Next
  v = objeto.SpecialFolders(nombre)
  If Err.Number <> 0 Then v = ""
  Err.Clear
  On Error Goto 0
  CarpetaEspecial = v
End Function
