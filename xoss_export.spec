# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 获取当前目录
pro_dir = os.path.abspath(".")

# 资源文件列表
# 格式: (源路径, 目标路径)
added_files = [
    ('README.md', '.'),
    ('icon.jpg', '.'),
    ('icon.ico', '.'),
]

# 自动收集 WebEngine 的数据文件
added_files += collect_data_files('PyQt5.QtWebEngineWidgets')

# 隐式导入列表
hidden_imports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtWebEngineWidgets',
    'requests',
    'tqdm',
    'xoss_export'
]

a = Analysis(
    ['xoss_export_gui.py'],
    pathex=[pro_dir],
    binaries=[],
    datas=added_files,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='行者数据导出工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False 表示不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # 指定 Windows 图标
)

# macOS 特有的 App Bundle 配置
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='XossExport.app',
        icon='icon.ico',  # macOS 理想情况下用 .icns，但此处尝试兼容
        bundle_identifier='com.imxingzhe.export',
    )
