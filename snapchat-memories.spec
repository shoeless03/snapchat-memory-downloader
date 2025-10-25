# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['download_snapchat_memories.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('licenses', 'licenses'),  # Include license files
    ],
    hiddenimports=[
        'PIL._tkinter_finder',  # Pillow sometimes needs this
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',           # GUI library not needed
        'matplotlib',        # Plotting library not needed
        'scipy',             # Scientific computing not needed
        'numpy',             # Large library, not directly used
        'pandas',            # Data analysis not needed
        'IPython',           # Interactive shell not needed
        'jupyter',           # Notebook not needed
        'notebook',          # Jupyter notebook not needed
        'pytest',            # Testing framework not needed
        'setuptools',        # Build tools not needed at runtime
        'pip',               # Package installer not needed at runtime
        'wheel',             # Package format not needed at runtime
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='snapchat-memories-downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console window for progress output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
