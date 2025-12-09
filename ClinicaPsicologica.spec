# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Recopilar todos los archivos de matplotlib
datas = []
binaries = []
hiddenimports = []

# Recopilar matplotlib completo
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=[
        ('assets', 'assets'),
        ('styles.qss', '.'),
        ('config.ini', '.')
    ] + datas,
    hiddenimports=hiddenimports + [
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.dialects.mssql',  # Soporte para SQL Server
        'sqlalchemy.dialects.mssql.pyodbc',  # Driver pyodbc para SQL Server
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.figure',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_agg',
        'PySide6.QtCharts',
        'PySide6.QtSvg',
        'PySide6.QtDataVisualization',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='ClinicaPsicologica',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No mostrar ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('assets', 'icon.ico') # <-- RUTA AL ICONO MÁS ROBUSTA
)
