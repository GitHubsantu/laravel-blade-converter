#define MyAppName "Laravel Blade Converter"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "imdevops"
#define MyAppURL "https://github.com/GitHubsantu"
#define MyAppExeName "LaravelBladeConverter.exe"

[Setup]
AppId={{7C2D5B8A-52F4-4B5F-9D47-5F5A7F6D8E91}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Laravel Blade Converter
DefaultGroupName=Laravel Blade Converter
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=Output
OutputBaseFilename=LaravelBladeConverterSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\LaravelBladeConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Laravel Blade Converter"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Laravel Blade Converter"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Laravel Blade Converter"; Flags: nowait postinstall skipifsilent