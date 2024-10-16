# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import tkinterdnd2

block_cipher = None

# Encuentra la ruta de tkdnd
tkdnd_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd')

# Asegúrate de que la ruta al icono sea absoluta
icon_path = os.path.abspath('icon.ico')

a = Analysis(['audio_w.py'],
             pathex=[],
             binaries=[],
             datas=[
                 (icon_path, '.'),
                 (tkdnd_path, 'tkinterdnd2/tkdnd')
             ],
             hiddenimports=['tkinterdnd2', 'ttkbootstrap', 'sounddevice', 'soundfile', 'mutagen', 'numpy', 'win32api', 'win32gui', 'win32con'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Audio-W',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch='x86_64',
          codesign_identity=None,
          entitlements_file=None,
          icon=icon_path,
          version='file_version_info.txt')

# Configuración adicional para asegurar la compilación de 64 bits
if sys.platform == 'win32':
    import platform
    if platform.architecture()[0] == '64bit':
        a.binaries = [x for x in a.binaries if not x[0].startswith("msvcp")]

# Optimizaciones adicionales
exe.optimize = 2