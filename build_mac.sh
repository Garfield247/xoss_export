#!/bin/bash
# macOS 下打包 .app 的简单脚本

echo "🚴 行者数据导出工具 - macOS 打包脚本"
echo "====================================="
echo

# 检查是否在 macOS 系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此脚本仅支持 macOS 系统"
    exit 1
fi

echo "🔍 检查 Python 环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python3 未安装或未添加到 PATH"
    exit 1
fi

echo
echo "📦 安装打包依赖..."
pip3 install pyinstaller PyQt5 requests tqdm
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

echo
echo "🧹 清理之前的构建..."
rm -rf build dist *.spec

echo
echo "🔨 开始打包..."
pyinstaller --onedir --windowed --name "XossExport" --add-data "README.md:." xoss_export_gui.py
if [ $? -ne 0 ]; then
    echo "❌ 打包失败"
    exit 1
fi

echo
echo "📁 创建发布目录..."
mkdir -p "发布_macOS"
cp -r "dist/XossExport.app" "发布_macOS/"
cp "README.md" "发布_macOS/"

echo
echo "📋 创建使用说明..."
cat > "发布_macOS/使用说明.txt" << 'EOF'
🚴 行者数据导出工具 - 使用说明
================================

📋 快速开始:
1. 双击运行 "XossExport.app"
2. 在界面中输入从浏览器复制的 Cookie
3. 设置导出参数（输出目录、筛选条件等）
4. 点击"开始导出"按钮
5. 在日志区域查看导出进度

🔑 获取 Cookie:
1. 打开浏览器，访问 https://www.imxingzhe.com
2. 登录您的账户
3. 按 F12 打开开发者工具
4. 切换到 Network 标签页
5. 刷新页面或进行任何操作
6. 在请求头中找到 Cookie 字段
7. 复制完整的 Cookie 字符串

⚠️ 注意事项:
- Cookie 中必须包含 sessionid 字段
- 确保网络连接稳定
- 导出大量数据时请耐心等待

🍎 macOS 特别说明:
- 首次运行可能需要右键选择"打开"来绕过安全限制
- 可以在"系统偏好设置 > 安全性与隐私"中允许运行
- 如果提示"无法验证开发者"，请按住 Control 键点击应用选择"打开"

📁 文件说明:
- XossExport.app: 主程序
- README.md: 详细文档
- export_file/: 导出的 GPX 文件存放目录
EOF

echo
echo "📁 创建导出目录..."
mkdir -p "发布_macOS/export_file"

echo
echo "✅ 打包完成!"
echo "====================================="
echo "📁 输出目录: 发布_macOS/"
echo "📱 应用程序: XossExport.app"
echo "💡 可以直接运行发布目录中的应用程序"
echo
echo "🍎 首次运行提示:"
echo "  如果系统提示无法验证开发者，请："
echo "  1. 右键点击 XossExport.app"
echo "  2. 选择'打开'"
echo "  3. 在弹出对话框中点击'打开'"
echo
