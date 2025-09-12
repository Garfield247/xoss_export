#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS 下打包 .app 的构建脚本
使用 PyInstaller 打包 GUI 版本为 macOS 应用程序
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

class MacAppBuilder:
    def __init__(self):
        self.project_name = "行者数据导出工具"
        self.app_name = "XossExport"
        self.main_script = "xoss_export_gui.py"
        self.core_module = "xoss_export.py"
        
    def check_environment(self):
        """检查环境"""
        print("🔍 检查 macOS 环境...")
        
        # 检查是否在 macOS 系统
        if sys.platform != "darwin":
            print("❌ 此脚本仅支持 macOS 系统")
            return False
            
        # 检查必要文件
        required_files = [self.main_script, self.core_module, "requirements.txt"]
        for file in required_files:
            if not os.path.exists(file):
                print(f"❌ 缺少必要文件: {file}")
                return False
                
        print("✅ macOS 环境检查通过")
        return True
    
    def install_dependencies(self):
        """安装依赖"""
        print("📦 安装依赖...")
        
        dependencies = [
            "pyinstaller>=5.0",
            "PyQt5>=5.15.0", 
            "requests>=2.25.0",
            "tqdm>=4.60.0"
        ]
        
        for dep in dependencies:
            print(f"  安装 {dep}...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                print(f"  ✅ {dep} 安装成功")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ {dep} 安装失败: {e}")
                return False
                
        return True
    
    def clean_build(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        
        dirs_to_clean = ["build", "dist", "__pycache__"]
        files_to_clean = ["*.spec"]
        
        for dir_name in dirs_to_clean:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print(f"  删除 {dir_name}/")
                
        # 清理 .spec 文件
        for spec_file in Path(".").glob("*.spec"):
            spec_file.unlink()
            print(f"  删除 {spec_file}")
    
    def create_app_icon(self):
        """创建应用图标"""
        print("🎨 创建应用图标...")
        
        # 创建一个简单的图标文件（如果不存在）
        icon_path = "app_icon.icns"
        if not os.path.exists(icon_path):
            print("  ⚠️ 未找到 app_icon.icns，将使用默认图标")
            return None
        else:
            print(f"  ✅ 使用图标文件: {icon_path}")
            return icon_path
    
    def build_app(self):
        """构建 .app 应用程序"""
        print("🔨 构建 macOS 应用程序...")
        
        # 获取图标路径
        icon_path = self.create_app_icon()
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onedir",
            "--windowed",
            "--name", self.app_name,
            "--add-data", "README.md:.",
            "--hidden-import", "PyQt5.QtCore",
            "--hidden-import", "PyQt5.QtGui",
            "--hidden-import", "PyQt5.QtWidgets",
            "--hidden-import", "requests",
            "--hidden-import", "tqdm",
            "--hidden-import", "xoss_export",
            "--clean",
            "--noconfirm",
        ]
        
        # 添加图标（如果存在）
        if icon_path:
            cmd.extend(["--icon", icon_path])
        
        cmd.append(self.main_script)
        
        try:
            subprocess.run(cmd, check=True)
            print("✅ macOS 应用程序构建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ macOS 应用程序构建失败: {e}")
            return False
    
    def create_dmg(self):
        """创建 DMG 安装包"""
        print("📦 创建 DMG 安装包...")
        
        app_path = Path("dist") / f"{self.app_name}.app"
        if not app_path.exists():
            print("❌ 应用程序不存在，无法创建 DMG")
            return False
        
        dmg_name = f"{self.project_name}.dmg"
        dmg_path = Path("dist") / dmg_name
        
        # 创建临时目录
        temp_dir = Path("temp_dmg")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # 复制应用程序到临时目录
            shutil.copytree(app_path, temp_dir / f"{self.app_name}.app")
            
            # 创建应用程序文件夹的符号链接
            applications_link = temp_dir / "Applications"
            applications_link.symlink_to("/Applications")
            
            # 复制文档
            if os.path.exists("README.md"):
                shutil.copy2("README.md", temp_dir / "README.md")
            
            # 创建使用说明
            self.create_usage_guide(temp_dir)
            
            # 创建 DMG
            cmd = [
                "hdiutil", "create",
                "-volname", self.project_name,
                "-srcfolder", str(temp_dir),
                "-ov",
                "-format", "UDZO",
                str(dmg_path)
            ]
            
            subprocess.run(cmd, check=True)
            print(f"✅ DMG 创建成功: {dmg_path}")
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ DMG 创建失败: {e}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False
    
    def create_usage_guide(self, target_dir):
        """创建使用说明"""
        guide_content = f"""🚴 {self.project_name} - 使用说明
================================

📋 快速开始:
1. 双击运行 "{self.app_name}.app"
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

📁 文件说明:
- {self.app_name}.app: 主程序
- README.md: 详细文档
- export_file/: 导出的 GPX 文件存放目录

🆘 技术支持:
如遇问题，请查看 README.md 文件中的常见问题部分

🍎 macOS 特别说明:
- 首次运行可能需要右键选择"打开"来绕过安全限制
- 可以在"系统偏好设置 > 安全性与隐私"中允许运行
"""
        
        guide_path = target_dir / "使用说明.txt"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print("  创建使用说明.txt")
    
    def create_release_package(self):
        """创建发布包"""
        print("📦 创建发布包...")
        
        release_dir = Path("发布_macOS")
        release_dir.mkdir(exist_ok=True)
        
        # 复制应用程序
        app_path = Path("dist") / f"{self.app_name}.app"
        if app_path.exists():
            shutil.copytree(app_path, release_dir / f"{self.app_name}.app")
            print(f"  复制 {self.app_name}.app")
        
        # 复制 DMG（如果存在）
        dmg_path = Path("dist") / f"{self.project_name}.dmg"
        if dmg_path.exists():
            shutil.copy2(dmg_path, release_dir / f"{self.project_name}.dmg")
            print(f"  复制 {self.project_name}.dmg")
        
        # 复制文档
        if os.path.exists("README.md"):
            shutil.copy2("README.md", release_dir / "README.md")
            print("  复制 README.md")
        
        # 创建使用说明
        self.create_usage_guide(release_dir)
        
        # 创建导出目录
        export_dir = release_dir / "export_file"
        export_dir.mkdir(exist_ok=True)
        print("  创建 export_file/ 目录")
        
        print("✅ 发布包创建完成")
    
    def build(self, create_dmg=False):
        """执行构建"""
        print(f"🚀 开始构建 macOS 应用程序...")
        print("=" * 50)
        
        # 1. 检查环境
        if not self.check_environment():
            return False
        
        # 2. 安装依赖
        if not self.install_dependencies():
            return False
        
        # 3. 清理构建目录
        self.clean_build()
        
        # 4. 构建应用程序
        if not self.build_app():
            return False
        
        # 5. 创建 DMG（可选）
        if create_dmg:
            self.create_dmg()
        
        # 6. 创建发布包
        self.create_release_package()
        
        print("=" * 50)
        print("🎉 构建完成!")
        print(f"📁 输出目录: 发布_macOS/")
        print(f"📱 应用程序: {self.app_name}.app")
        if create_dmg:
            print(f"💿 安装包: {self.project_name}.dmg")
        print("💡 可以直接运行发布目录中的应用程序")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="行者数据导出工具 - macOS 打包脚本")
    parser.add_argument("--dmg", action="store_true", help="创建 DMG 安装包")
    parser.add_argument("--clean", action="store_true", help="仅清理构建目录")
    
    args = parser.parse_args()
    
    builder = MacAppBuilder()
    
    if args.clean:
        builder.clean_build()
        print("✅ 清理完成")
        return
    
    success = builder.build(create_dmg=args.dmg)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
