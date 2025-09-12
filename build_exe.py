#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 下打包 exe 的构建脚本
使用 PyInstaller 打包 GUI 版本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    print("🔍 检查依赖...")
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller 已安装: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller 安装完成")
    
    # 检查其他依赖
    dependencies = ["PyQt5", "requests", "tqdm"]
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} 已安装")
        except ImportError:
            print(f"❌ {dep} 未安装，正在安装...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"✅ {dep} 安装完成")

def create_spec_file():
    """创建 PyInstaller 规格文件"""
    print("📝 创建 PyInstaller 规格文件...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['xoss_export_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'requests',
        'tqdm',
        'xoss_export'
    ],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    with open('xoss_export_gui.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 规格文件创建完成")

def build_exe():
    """构建 exe 文件"""
    print("🔨 开始构建 exe 文件...")
    
    # 清理之前的构建
    if os.path.exists('build'):
        shutil.rmtree('build')
        print("🧹 清理 build 目录")
    
    if os.path.exists('dist'):
        shutil.rmtree('dist')
        print("🧹 清理 dist 目录")
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "xoss_export_gui.spec"
    ]
    
    print(f"🚀 执行构建命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 构建成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def create_installer_script():
    """创建安装脚本"""
    print("📦 创建安装脚本...")
    
    installer_content = '''@echo off
chcp 65001 >nul
echo 🚴 行者数据导出工具 - 安装脚本
echo ================================
echo.

echo 📁 创建安装目录...
if not exist "C:\\Program Files\\行者数据导出工具" (
    mkdir "C:\\Program Files\\行者数据导出工具"
)

echo 📋 复制文件...
copy "dist\\行者数据导出工具.exe" "C:\\Program Files\\行者数据导出工具\\"
copy "README.md" "C:\\Program Files\\行者数据导出工具\\"

echo 🔗 创建桌面快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\行者数据导出工具.lnk'); $Shortcut.TargetPath = 'C:\\Program Files\\行者数据导出工具\\行者数据导出工具.exe'; $Shortcut.Save()"

echo ✅ 安装完成!
echo.
echo 📍 程序已安装到: C:\\Program Files\\行者数据导出工具\\
echo 🔗 桌面快捷方式已创建
echo.
pause
'''
    
    with open('install.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    
    print("✅ 安装脚本创建完成")

def create_portable_script():
    """创建便携版脚本"""
    print("💼 创建便携版脚本...")
    
    portable_content = '''@echo off
chcp 65001 >nul
echo 🚴 行者数据导出工具 - 便携版
echo ================================
echo.

echo 📁 创建便携版目录...
if not exist "行者数据导出工具_便携版" (
    mkdir "行者数据导出工具_便携版"
)

echo 📋 复制文件...
copy "dist\\行者数据导出工具.exe" "行者数据导出工具_便携版\\"
copy "README.md" "行者数据导出工具_便携版\\"

echo 📁 创建导出目录...
if not exist "行者数据导出工具_便携版\\export_file" (
    mkdir "行者数据导出工具_便携版\\export_file"
)

echo ✅ 便携版创建完成!
echo.
echo 📍 便携版位置: 行者数据导出工具_便携版\\
echo 💡 可以直接运行 行者数据导出工具.exe
echo.
pause
'''
    
    with open('create_portable.bat', 'w', encoding='utf-8') as f:
        f.write(portable_content)
    
    print("✅ 便携版脚本创建完成")

def main():
    """主函数"""
    print("🚴 行者数据导出工具 - Windows 打包脚本")
    print("=" * 50)
    
    # 检查是否在 Windows 系统
    if sys.platform != "win32":
        print("❌ 此脚本仅支持 Windows 系统")
        return
    
    # 检查必要文件
    required_files = ["xoss_export_gui.py", "xoss_export.py", "requirements.txt"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            return
    
    try:
        # 1. 检查依赖
        check_dependencies()
        print()
        
        # 2. 创建规格文件
        create_spec_file()
        print()
        
        # 3. 构建 exe
        if build_exe():
            print()
            
            # 4. 创建安装脚本
            create_installer_script()
            print()
            
            # 5. 创建便携版脚本
            create_portable_script()
            print()
            
            print("🎉 打包完成!")
            print("=" * 50)
            print("📁 输出文件:")
            print("  - dist/行者数据导出工具.exe (主程序)")
            print("  - install.bat (安装脚本)")
            print("  - create_portable.bat (便携版脚本)")
            print()
            print("💡 使用方法:")
            print("  1. 运行 install.bat 安装到系统")
            print("  2. 运行 create_portable.bat 创建便携版")
            print("  3. 直接运行 dist/行者数据导出工具.exe")
            
        else:
            print("❌ 打包失败，请检查错误信息")
            
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()
