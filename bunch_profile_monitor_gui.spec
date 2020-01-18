# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['bunch_profile_monitor_gui.py'],
             pathex=['g:\\My Drive\\UHCICAGO\\Thesis\\BunchProfileMonitor'],
             binaries=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False,
			 datas=[("signal_transfer_line_data","signal_transfer_line_data")])
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='bunch_profile_monitor_gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
