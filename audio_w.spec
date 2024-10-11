# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Encontrar la ruta de tkdnd
import tkinterdnd2
tkdnd_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd')

a = Analysis(['audio_w.py'],
             pathex=[],
             binaries=[],
             datas=[('icon.ico', '.'), (tkdnd_path, 'tkinterdnd2/tkdnd')],
             hiddenimports=['tkinter', 'ttkbootstrap', 'tkinterdnd2', 'sounddevice', 'soundfile', 'numpy'],
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
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='icon.ico')