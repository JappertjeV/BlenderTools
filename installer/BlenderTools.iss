[Setup]
AppName=BlenderTools
AppVersion=0.2.0
AppPublisher=BlenderTools
DefaultDirName={autopf}\BlenderTools
DefaultGroupName=BlenderTools
OutputDir=..\dist\installer
OutputBaseFilename=BlenderTools-Setup-0.2.0
PrivilegesRequired=lowest
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
Compression=lzma2
SolidCompression=yes

[Languages]
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\BlenderTools.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\BlenderTools"; Filename: "{app}\BlenderTools.exe"
Name: "{commondesktop}\BlenderTools"; Filename: "{app}\BlenderTools.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Snelkoppeling op bureaublad"; GroupDescription: "Extra opties:"

[Run]
Filename: "{app}\BlenderTools.exe"; Description: "BlenderTools starten"; Flags: nowait postinstall skipifsilent
