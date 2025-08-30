; WeRSS 单用户版本安装脚本 (Inno Setup)
; 需要安装 Inno Setup (https://jrsoftware.org/isinfo.php) 来编译此脚本

[Setup]
; 应用程序基本信息
AppName=WeRSS 单用户版
AppVersion=1.0.0
AppPublisher=WeRSS Team
AppPublisherURL=https://github.com/your-repo
AppSupportURL=https://github.com/your-repo/issues
AppUpdatesURL=https://github.com/your-repo/releases
DefaultDirName={autopf}\WeRSS
DefaultGroupName=WeRSS
AllowNoIcons=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=安装前说明.txt
InfoAfterFile=安装后说明.txt
OutputDir=installer-output
OutputBaseFilename=WeRSS-Setup-v1.0.0
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; 支持的系统版本
MinVersion=6.1sp1
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; 主程序文件
Source: "dist-standalone\WeRSS-Standalone.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist-standalone\安装说明.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist-standalone\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "dist-standalone\用户系统方案评估.md"; DestDir: "{app}"; Flags: ignoreversion

; 配置文件模板
Source: "config-standalone.yaml"; DestDir: "{app}"; DestName: "config.example.yaml"; Flags: ignoreversion

[Icons]
; 开始菜单图标
Name: "{group}\WeRSS"; Filename: "{app}\WeRSS-Standalone.exe"
Name: "{group}\{cm:ProgramOnTheWeb,WeRSS}"; Filename: "https://github.com/your-repo"
Name: "{group}\{cm:UninstallProgram,WeRSS}"; Filename: "{uninstallexe}"

; 桌面图标
Name: "{autodesktop}\WeRSS"; Filename: "{app}\WeRSS-Standalone.exe"; Tasks: desktopicon

; 快速启动图标  
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\WeRSS"; Filename: "{app}\WeRSS-Standalone.exe"; Tasks: quicklaunchicon

[Run]
; 安装完成后的操作
Filename: "{app}\WeRSS-Standalone.exe"; Description: "{cm:LaunchProgram,WeRSS}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时删除的文件和文件夹
Type: filesandordirs; Name: "{userprofile}\WeRSS"

[Code]
// 自定义代码
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    if (IsUpgrade()) then
    begin
      UnInstallOldVersion();
    end;
  end;
end;