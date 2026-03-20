# -*- mode: python ; coding: utf-8 -*-
import sys

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"

if IS_MAC:
    binaries = [('bin/mac/caesiumclt', 'bin/mac')]
elif IS_WIN:
    binaries = [('bin/win/caesiumclt.exe', 'bin/win')]
else:
    binaries = []

a = Analysis(
    ['gui.py'],
    pathex=['.'],
    binaries=binaries,
    datas=[
        ('Materialen.blend', '.'),
        ('render_script.py', '.'),
        ('compress.py', '.'),
        ('batch_render.py', '.'),
        ('extract_objects.py', '.'),
        ('settings.py', '.'),
        ('blender_detect.py', '.'),
        ('version.py', '.'),
        ('updater.py', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'tqdm',
        'winreg',
        'platform',
        'shutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['venv'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

if IS_MAC:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='BlenderTools',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='assets/icon.icns' if __import__('os').path.exists('assets/icon.icns') else None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='BlenderTools',
    )
    app = BUNDLE(
        coll,
        name='BlenderTools.app',
        icon='assets/icon.icns' if __import__('os').path.exists('assets/icon.icns') else None,
        bundle_identifier='nl.blendertools.app',
        info_plist={
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13',
        },
    )
else:
    # Windows: single-file EXE
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='BlenderTools',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='assets/icon.ico' if __import__('os').path.exists('assets/icon.ico') else None,
    )
