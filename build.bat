@echo off
chcp 65001 >nul
echo 🚴 行者数据导出工具 - Windows 单文件打包脚本
echo ===========================================
echo.

echo 🔍 检查 Python 环境...
python --version
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到 PATH
    pause
    exit /b 1
)

echo.
echo 📦 安装/更新打包依赖...
pip install pyinstaller PyQt5 PyQtWebEngine requests tqdm
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 🧹 清理之前的构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo.
echo 🔨 开始打包 (单文件模式)...
:: --onefile: 产生单文件
:: --windowed: 运行不显示控制台
:: --icon: 指定 exe 图标
:: --add-data: 打包资源文件 (注意 Windows 下用分号 ;)
:: --hidden-import: 显式包含 WebEngine 模块防止漏掉
pyinstaller --onefile --windowed ^
    --name "行者数据导出工具" ^
    --icon "icon.ico" ^
    --add-data "README.md;." ^
    --add-data "icon.jpg;." ^
    --add-data "icon.ico;." ^
    --hidden-import "PyQt5.QtWebEngineWidgets" ^
    --hidden-import "PyQt5.QtCore" ^
    --hidden-import "PyQt5.QtGui" ^
    --hidden-import "PyQt5.QtWidgets" ^
    --clean ^
    --noconfirm ^
    xoss_export_gui.py

if errorlevel 1 (
    echo ❌ 打包失败
    pause
    exit /b 1
)

echo.
echo 📁 创建发布目录...
if not exist "发布" mkdir "发布"
move "dist\行者数据导出工具.exe" "发布\"
copy "README.md" "发布\"

echo.
echo 📋 创建使用说明...
echo 🚴 行者数据导出工具 > "发布\使用说明.txt"
echo ================== >> "发布\使用说明.txt"
echo. >> "发布\使用说明.txt"
echo 1. 双击运行 "行者数据导出工具.exe" >> "发布\使用说明.txt"
echo 2. 点击 "登录账号" 按钮，扫码或输入账号登录 >> "发布\使用说明.txt"
echo 3. 选择保存路径和导出格式 (GPX/FIT) >> "发布\使用说明.txt"
echo 4. 点击 "开始导出" 即可 >> "发布\使用说明.txt"
echo. >> "发布\使用说明.txt"
echo * 注意：由于单文件打包在启动时需要解压，首次运行可能稍慢。 >> "发布\使用说明.txt"

echo.
echo ✅ 打包完成!
echo =====================================
echo 📁 输出目录: 发布\
echo 📄 主程序: 行者数据导出工具.exe
echo 📖 说明文档: README.md
echo.
echo 💡 可以直接运行 发布\行者数据导出工具.exe
echo.
pause
