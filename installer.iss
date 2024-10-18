#define MyAppName "Audio-W"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "Wamphyre"
#define MyAppURL "https://github.com/Wamphyre/Audio-W"
#define MyAppExeName "Audio-W.exe"

[Setup]
AppId={{D0E858DF-985E-4907-B7FB-8D732C3FC3B9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=Audio-W-1.3-Setup
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64os
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "associateaudiofiles"; Description: "Asociar archivos de audio con {#MyAppName}"; GroupDescription: "Asociaciones de archivo:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Registry]
Root: HKCR; Subkey: "Applications\{#MyAppExeName}"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\DefaultIcon"; ValueType: string; ValueData: "{app}\{#MyAppExeName},0"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".mp3"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".wav"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".flac"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles
Root: HKCR; Subkey: ".mp3\OpenWithProgids"; ValueType: string; ValueName: "Applications.{#MyAppExeName}"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles
Root: HKCR; Subkey: ".wav\OpenWithProgids"; ValueType: string; ValueName: "Applications.{#MyAppExeName}"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles
Root: HKCR; Subkey: ".flac\OpenWithProgids"; ValueType: string; ValueName: "Applications.{#MyAppExeName}"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles

; Agregar Audio-W al menú contextual de archivos de audio
Root: HKCR; Subkey: ".mp3\shell\{#MyAppName}"; ValueType: string; ValueData: "Reproducir con {#MyAppName}"; Flags: uninsdeletekey; Tasks: associateaudiofiles
Root: HKCR; Subkey: ".mp3\shell\{#MyAppName}\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: associateaudiofiles
Root: HKCR; Subkey: ".wav\shell\{#MyAppName}"; ValueType: string; ValueData: "Reproducir con {#MyAppName}"; Flags: uninsdeletekey; Tasks: associateaudiofiles
Root: HKCR; Subkey: ".wav\shell\{#MyAppName}\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: associateaudiofiles
Root: HKCR; Subkey: ".flac\shell\{#MyAppName}"; ValueType: string; ValueData: "Reproducir con {#MyAppName}"; Flags: uninsdeletekey; Tasks: associateaudiofiles
Root: HKCR; Subkey: ".flac\shell\{#MyAppName}\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: associateaudiofiles

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  UninstallExe: String;
begin
  if CurStep = ssInstall then
  begin
    if RegKeyExists(HKEY_LOCAL_MACHINE, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1') then
    begin
      if MsgBox('Se ha detectado una versión anterior de {#MyAppName}. ¿Desea desinstalarla antes de continuar?', mbConfirmation, MB_YESNO) = IDYES then
      begin
        if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1', 'UninstallString', UninstallExe) then
        begin
          UninstallExe := RemoveQuotes(UninstallExe);
          Exec(UninstallExe, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
        end
        else
        begin
          MsgBox('No se pudo encontrar el desinstalador de la versión anterior.', mbError, MB_OK);
        end;
      end;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Limpiar registros
    RegDeleteKeyIncludingSubkeys(HKCR, 'Applications\{#MyAppExeName}');
    RegDeleteKeyIncludingSubkeys(HKCR, '.mp3\OpenWithProgids\Applications.{#MyAppExeName}');
    RegDeleteKeyIncludingSubkeys(HKCR, '.wav\OpenWithProgids\Applications.{#MyAppExeName}');
    RegDeleteKeyIncludingSubkeys(HKCR, '.flac\OpenWithProgids\Applications.{#MyAppExeName}');
    RegDeleteKeyIncludingSubkeys(HKCR, '.mp3\shell\{#MyAppName}');
    RegDeleteKeyIncludingSubkeys(HKCR, '.wav\shell\{#MyAppName}');
    RegDeleteKeyIncludingSubkeys(HKCR, '.flac\shell\{#MyAppName}');

    // Eliminar asociaciones de archivo
    RegDeleteValue(HKCR, '.mp3\OpenWithProgids', 'Applications.{#MyAppExeName}');
    RegDeleteValue(HKCR, '.wav\OpenWithProgids', 'Applications.{#MyAppExeName}');
    RegDeleteValue(HKCR, '.flac\OpenWithProgids', 'Applications.{#MyAppExeName}');

    // Eliminar entradas del menú de inicio y escritorio
    DeleteFile(ExpandConstant('{commonprograms}\{#MyAppName}.lnk'));
    DeleteFile(ExpandConstant('{userdesktop}\{#MyAppName}.lnk'));

    // Eliminar datos de usuario si el usuario lo desea
    if MsgBox('¿Desea eliminar todos los archivos de configuración y datos de usuario de {#MyAppName}?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\{#MyAppName}'), True, True, True);
    end;
  end;
end;