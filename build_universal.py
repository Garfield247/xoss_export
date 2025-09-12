#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用打包脚本 - 支持 Windows、macOS、Linux
自动检测系统并选择合适的打包方式
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

class UniversalBuilder:
    def __init__(self):
        self.project_name = "行者数据导出工具"
        self.main_script = "xoss_export_gui.py"
        self.core_module = "xoss_export.py"
        self.system = platform.system().lower()
        
    def detect_platform(self):
        """检测平台"""
        print(f"🔍 检测到系统: {platform.system()} {platform.release()}")
        
        if self.system == "windows":
            return "windows"
        elif self.system == "darwin":
            return "macos"
        elif self.system == "linux":
            return "linux"
        else:
            print(f"❌ 不支持的系统: {platform.system()}")
            return None
    
    def check_environment(self):
        """检查环境"""
        print("🔍 检查环境...")
        
        # 检查必要文件
        required_files = [self.main_script, self.core_module, "requirements.txt"]
        for file in required_files:
            if not os.path.exists(file):
                print(f"❌ 缺少必要文件: {file}")
                return False
                
        print("✅ 环境检查通过")
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
    
    def build_windows(self):
        """构建 Windows 版本"""
        print("🔨 构建 Windows 版本...")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name", self.project_name,
            "--add-data", "README.md;.",
            "--hidden-import", "PyQt5.QtCore",
            "--hidden-import", "PyQt5.QtGui",
            "--hidden-import", "PyQt5.QtWidgets",
            "--hidden-import", "requests",
            "--hidden-import", "tqdm",
            "--hidden-import", "xoss_export",
            "--clean",
            "--noconfirm",
            self.main_script
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✅ Windows 版本构建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Windows 版本构建失败: {e}")
            return False
    
    def build_macos(self):
        """构建 macOS 版本"""
        print("🔨 构建 macOS 版本...")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onedir",
            "--windowed",
            "--name", "XossExport",
            "--add-data", "README.md:.",
            "--hidden-import", "PyQt5.QtCore",
            "--hidden-import", "PyQt5.QtGui",
            "--hidden-import", "PyQt5.QtWidgets",
            "--hidden-import", "requests",
            "--hidden-import", "tqdm",
            "--hidden-import", "xoss_export",
            "--clean",
            "--noconfirm",
            self.main_script
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✅ macOS 版本构建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ macOS 版本构建失败: {e}")
            return False
    
    def build_linux(self):
        """构建 Linux 版本"""
        print("🔨 构建 Linux 版本...")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name", "xoss-export",
            "--add-data", "README.md:.",
            "--hidden-import", "PyQt5.QtCore",
            "--hidden-import", "PyQt5.QtGui",
            "--hidden-import", "PyQt5.QtWidgets",
            "--hidden-import", "requests",
            "--hidden-import", "tqdm",
            "--hidden-import", "xoss_export",
            "--clean",
            "--noconfirm",
            self.main_script
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✅ Linux 版本构建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Linux 版本构建失败: {e}")
            return False
    
    def create_release_package(self, platform_name):
        """创建发布包"""
        print(f"📦 创建 {platform_name} 发布包...")
        
        release_dir = Path(f"发布_{platform_name}")
        release_dir.mkdir(exist_ok=True)
        
        if platform_name == "windows":
            exe_name = f"{self.project_name}.exe"
            exe_path = Path("dist") / exe_name
            if exe_path.exists():
                shutil.copy2(exe_path, release_dir / exe_name)
                print(f"  复制 {exe_name}")
                
        elif platform_name == "macos":
            app_name = "XossExport.app"
            app_path = Path("dist") / app_name
            if app_path.exists():
                shutil.copytree(app_path, release_dir / app_name)
                print(f"  复制 {app_name}")
                
        elif platform_name == "linux":
            exe_name = "xoss-export"
            exe_path = Path("dist") / exe_name
            if exe_path.exists():
                shutil.copy2(exe_path, release_dir / exe_name)
                print(f"  复制 {exe_name}")
        
        # 复制文档
        if os.path.exists("README.md"):
            shutil.copy2("README.md", release_dir / "README.md")
            print("  复制 README.md")
        
        # 创建使用说明
        self.create_usage_guide(release_dir, platform_name)
        
        # 创建导出目录
        export_dir = release_dir / "export_file"
        export_dir.mkdir(exist_ok=True)
        print("  创建 export_file/ 目录")
        
        print("✅ 发布包创建完成")
    
    def create_usage_guide(self, target_dir, platform_name):
        """创建使用说明"""
        if platform_name == "windows":
            app_name = f"{self.project_name}.exe"
            platform_notes = """🪟 Windows 特别说明:
- 如果杀毒软件误报，请添加到白名单
- 确保系统已安装 Visual C++ Redistributable"""
        elif platform_name == "macos":
            app_name = "XossExport.app"
            platform_notes = """🍎 macOS 特别说明:
- 首次运行可能需要右键选择"打开"来绕过安全限制
- 可以在"系统偏好设置 > 安全性与隐私"中允许运行
- 如果提示"无法验证开发者"，请按住 Control 键点击应用选择"打开" """
        else:  # linux
            app_name = "./xoss-export"
            platform_notes = """🐧 Linux 特别说明:
- 确保系统已安装 PyQt5 相关依赖
- 可能需要安装额外的字体包
- 运行前请确保文件有执行权限: chmod +x xoss-export"""
        
        guide_content = f"""🚴 {self.project_name} - 使用说明
================================

📋 快速开始:
1. 运行 "{app_name}"
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

{platform_notes}

📁 文件说明:
- {app_name}: 主程序
- README.md: 详细文档
- export_file/: 导出的 GPX 文件存放目录

🆘 技术支持:
如遇问题，请查看 README.md 文件中的常见问题部分
"""
        
        guide_path = target_dir / "使用说明.txt"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print("  创建使用说明.txt")
    
    def build(self):
        """执行构建"""
        platform_name = self.detect_platform()
        if not platform_name:
            return False
        
        print(f"🚀 开始构建 {platform_name.upper()} 版本...")
        print("=" * 50)
        
        # 1. 检查环境
        if not self.check_environment():
            return False
        
        # 2. 安装依赖
        if not self.install_dependencies():
            return False
        
        # 3. 清理构建目录
        self.clean_build()
        
        # 4. 构建
        if platform_name == "windows":
            success = self.build_windows()
        elif platform_name == "macos":
            success = self.build_macos()
        elif platform_name == "linux":
            success = self.build_linux()
        
        if not success:
            return False
        
        # 5. 创建发布包
        self.create_release_package(platform_name)
        
        print("=" * 50)
        print("🎉 构建完成!")
        print(f"📁 输出目录: 发布_{platform_name}/")
        print("💡 可以直接运行发布目录中的程序")
        
        return True

def main():
    builder = UniversalBuilder()
    success = builder.build()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
