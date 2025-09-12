@echo off
chcp 65001 >nul
echo 🚴 行者数据导出工具 - Windows 打包脚本
echo =====================================
echo.

echo 🔍 检查 Python 环境...
python --version
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到 PATH
    pause
    exit /b 1
)

echo.
echo 📦 安装打包依赖...
pip install pyinstaller
if errorlevel 1 (
    echo ❌ PyInstaller 安装失败
    pause
    exit /b 1
)

echo.
echo 🧹 清理之前的构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo.
echo 🔨 开始打包...
pyinstaller --onefile --windowed --name "行者数据导出工具" --add-data "README.md;." xoss_export_gui.py
if errorlevel 1 (
    echo ❌ 打包失败
    pause
    exit /b 1
)

echo.
echo 📁 创建发布目录...
if not exist "发布" mkdir "发布"
copy "dist\行者数据导出工具.exe" "发布\"
copy "README.md" "发布\"

echo.
echo 📋 创建使用说明...
echo 🚴 行者数据导出工具 > "发布\使用说明.txt"
echo ================== >> "发布\使用说明.txt"
echo. >> "发布\使用说明.txt"
echo 1. 双击运行 "行者数据导出工具.exe" >> "发布\使用说明.txt"
echo 2. 按照界面提示输入 Cookie 和设置参数 >> "发布\使用说明.txt"
echo 3. 点击开始导出即可下载 GPX 文件 >> "发布\使用说明.txt"
echo. >> "发布\使用说明.txt"
echo 详细使用说明请查看 README.md 文件 >> "发布\使用说明.txt"

echo.
echo ✅ 打包完成!
echo =====================================
echo 📁 输出目录: 发布\
echo 📄 主程序: 行者数据导出工具.exe
echo 📖 说明文档: README.md
echo 📋 使用说明: 使用说明.txt
echo.
echo 💡 可以直接运行 发布\行者数据导出工具.exe
echo.
pause
