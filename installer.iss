#define MyAppName "Audio-W"
#define MyAppVersion "1.1"
#define MyAppPublisher "Wamphyre"
#define MyAppExeName "Audio-W.exe"

[Setup]
AppId={{47551223-1DE9-4D36-ABF9-3D30ADE4F29B}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=Audio-W-Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "associateaudiofiles"; Description: "Asociar archivos de audio con Audio-W"; GroupDescription: "Asociación de archivos:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Classes\Audio-W"; ValueType: string; ValueName: ""; ValueData: "Audio-W"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Audio-W"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "Audio-W"
Root: HKCU; Subkey: "Software\Classes\Audio-W\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\.mp3\OpenWithProgids"; ValueType: string; ValueName: "Audio-W"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles
Root: HKCU; Subkey: "Software\Classes\.wav\OpenWithProgids"; ValueType: string; ValueName: "Audio-W"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles
Root: HKCU; Subkey: "Software\Classes\.ogg\OpenWithProgids"; ValueType: string; ValueName: "Audio-W"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles
Root: HKCU; Subkey: "Software\Classes\.flac\OpenWithProgids"; ValueType: string; ValueName: "Audio-W"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associateaudiofiles

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
Filename: "{sys}\reg.exe"; Parameters: "import ""{tmp}\audio_w_association.reg"""; Flags: runhidden; StatusMsg: "Registering file associations..."; Tasks: associateaudiofiles

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
#ifdef UNICODE
  #define AW "W"
#else
  #define AW "A"
#endif

const
  SMTO_ABORTIFHUNG = $0002;
  WM_SETTINGCHANGE = $001A;

type
  WPARAM = UINT_PTR;
  LPARAM = INT_PTR;
  LRESULT = INT_PTR;

function SendMessageTimeout(hWnd: HWND; Msg: UINT; wParam: WPARAM; lParam: LPARAM; fuFlags: UINT; uTimeout: UINT; var lpdwResult: DWORD): LRESULT;
  external 'SendMessageTimeout{#AW}@user32.dll stdcall';

procedure RefreshEnvironment;
var
  S: string;
  I: DWORD;
begin
  S := 'Environment';
end;

procedure CreateAssociationFile();
var
  FileName: string;
  Lines: TStringList;
begin
  FileName := ExpandConstant('{tmp}\audio_w_association.reg');
  Lines := TStringList.Create;
  try
    Lines.Add('Windows Registry Editor Version 5.00');
    Lines.Add('');
    Lines.Add('[HKEY_CURRENT_USER\Software\Classes\.mp3]');
    Lines.Add('"Audio-W"=""');
    Lines.Add('');
    Lines.Add('[HKEY_CURRENT_USER\Software\Classes\.wav]');
    Lines.Add('"Audio-W"=""');
    Lines.Add('');
    Lines.Add('[HKEY_CURRENT_USER\Software\Classes\.ogg]');
    Lines.Add('"Audio-W"=""');
    Lines.Add('');
    Lines.Add('[HKEY_CURRENT_USER\Software\Classes\.flac]');
    Lines.Add('"Audio-W"=""');
    Lines.SaveToFile(FileName);
  finally
    Lines.Free;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('associateaudiofiles') then
    begin
      CreateAssociationFile();
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  mRes : integer;
begin
  case CurUninstallStep of
    usUninstall:
      begin
        mRes := MsgBox('¿Desea eliminar también los archivos de datos de la aplicación?' + #13#10 + 'Esto incluirá configuraciones y otros datos guardados.', mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
        if mRes = IDYES then
        begin
          DelTree(ExpandConstant('{userappdata}\{#MyAppName}'), True, True, True);
        end;
        
        // Eliminar asociaciones de archivos
        RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\Audio-W');
        RegDeleteValue(HKCU, 'Software\Classes\.mp3\OpenWithProgids', 'Audio-W');
        RegDeleteValue(HKCU, 'Software\Classes\.wav\OpenWithProgids', 'Audio-W');
        RegDeleteValue(HKCU, 'Software\Classes\.ogg\OpenWithProgids', 'Audio-W');
        RegDeleteValue(HKCU, 'Software\Classes\.flac\OpenWithProgids', 'Audio-W');
      end;
    usPostUninstall:
      begin
        if DirExists(ExpandConstant('{app}')) then
        begin
          if MsgBox('Se han detectado archivos residuales. ¿Desea eliminarlos?', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
          begin
            DelTree(ExpandConstant('{app}'), True, True, True);
          end;
        end;
        
        // Refrescar el entorno para actualizar los iconos y asociaciones
        RefreshEnvironment;
      end;
  end;
end;