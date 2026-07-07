Option Explicit

Dim shell
Dim fileSystem
Dim arguments
Dim scriptPath
Dim command
Dim index

Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")
Set arguments = WScript.Arguments

If arguments.Count < 1 Then
    WScript.Quit 2
End If

scriptPath = arguments(0)
If Not fileSystem.FileExists(scriptPath) Then
    WScript.Quit 3
End If

command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File " & QuoteArgument(scriptPath)
For index = 1 To arguments.Count - 1
    command = command & " " & QuoteArgument(arguments(index))
Next

WScript.Quit shell.Run(command, 0, True)

Function QuoteArgument(value)
    QuoteArgument = Chr(34) & Replace(CStr(value), Chr(34), Chr(34) & Chr(34)) & Chr(34)
End Function
