# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Base directory of the project
base_dir = os.getcwd()

# Collect all modules from src/
hidden_imports = [
    'waitress',
    'django.core.management.commands.migrate',
    'django.core.management.commands.showmigrations',
    'rest_framework.parsers',
    'rest_framework.renderers',
    'rest_framework.authentication',
    'rest_framework.permissions',
    'rest_framework_simplejwt.authentication',
    'rest_framework.authtoken',
    'corsheaders.middleware',
    'django_browser_reload.middleware',
]

# Dynamically collect all modules in src/modules
hidden_imports += collect_submodules('modules')

# Data files (templates, static files if served by Django)
datas = [
    ('src', 'src'),
    ('erp_root', 'erp_root'),
]

# Add third-party data files
datas += collect_data_files('rest_framework')
datas += collect_data_files('django')

a = Analysis(
    ['desktop_entrypoint.py'],
    pathex=[base_dir, os.path.join(base_dir, 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='zchpc_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../hpc.png'] if os.path.exists('../hpc.png') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend_dist',
)
