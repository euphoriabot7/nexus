' ============================================================
'  NEXUS - lanzador sin ventana de consola
'
'  Lo usan los accesos directos "NEXUS" (Escritorio y menu Inicio):
'  arranca run.bat con la consola oculta y, si algo falla, muestra un
'  aviso con el motivo en vez de morir en silencio.
' ============================================================
Option Explicit

Dim sh, fso, carpeta, rc, errFile, carpetaDatos, msg, f, s

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

carpeta = fso.GetParentFolderName(WScript.ScriptFullName)

' run.bat oculto (0 = sin ventana, True = esperar a que termine)
rc = sh.Run("""" & carpeta & "\run.bat"" --oculto", 0, True)

If rc <> 0 Then
  carpetaDatos = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\NEXUS"
  errFile = carpetaDatos & "\ultimo-error.txt"
  msg = "NEXUS no ha podido arrancar."
  If fso.FileExists(errFile) Then
    Set f = fso.OpenTextFile(errFile, 1, False)
    If Not f.AtEndOfStream Then s = f.ReadAll
    f.Close
    s = Trim(s)
    If Len(s) > 0 Then msg = msg & vbCrLf & vbCrLf & s
  End If
  msg = msg & vbCrLf & vbCrLf & "Registros:" & vbCrLf & _
        carpetaDatos & "\server.log" & vbCrLf & _
        carpetaDatos & "\server-arranque.log"
  MsgBox msg, 16, "NEXUS"
  WScript.Quit 1
End If

WScript.Quit 0
