# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import platform

ROOT = Path(SPECPATH)
ASSETS = ROOT / "assets"
WINDOWS_ICON = ASSETS / "blockviz.ico"
MAC_ICON = ASSETS / "blockviz.icns"
LINUX_ICON = ASSETS / "blockviz.png"

icon_path = None
system = platform.system()
if system == "Windows" and WINDOWS_ICON.exists():
    icon_path = str(WINDOWS_ICON)
elif system == "Darwin" and MAC_ICON.exists():
    icon_path = str(MAC_ICON)
elif LINUX_ICON.exists():
    icon_path = str(LINUX_ICON)


a = Analysis(
    ["scripts/package_entry.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="BlockViz",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
