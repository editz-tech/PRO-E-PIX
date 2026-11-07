#define MyAppName "E-Pix"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "E-Pix"
#define MyAppExeName "E-Pix.exe"

[Setup]
AppId={{A8E6D1B7-2A7F-4B9B-9C43-EF1A20261107}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\E-Pix
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=E-Pix-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\E-Pix.exe

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\E-Pix\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\E-Pix"; Filename: "{app}\E-Pix.exe"
Name: "{autodesktop}\E-Pix"; Filename: "{app}\E-Pix.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\E-Pix.exe"; Description: "Launch E-Pix"; Flags: postinstall nowait skipifsilent
