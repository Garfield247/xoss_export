#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级 Windows 打包脚本
支持多种打包选项和优化
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

class ExeBuilder:
    def __init__(self):
        self.project_name = "行者数据导出工具"
        self.main_script = "xoss_export_gui.py"
        self.core_module = "xoss_export.py"
        
    def check_environment(self):
        """检查环境"""
        print("🔍 检查环境...")
        
        # 检查 Python
        if sys.platform != "win32":
            print("❌ 此脚本仅支持 Windows 系统")
            return False
            
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
    
    def build_single_file(self):
        """构建单文件版本"""
        print("🔨 构建单文件版本...")
        
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
            print("✅ 单文件版本构建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 单文件版本构建失败: {e}")
            return False
    
    def build_directory(self):
        """构建目录版本"""
        print("🔨 构建目录版本...")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onedir",
            "--windowed",
            "--name", f"{self.project_name}_目录版",
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
            print("✅ 目录版本构建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 目录版本构建失败: {e}")
            return False
    
    def create_release_package(self, build_type="single"):
        """创建发布包"""
        print("📦 创建发布包...")
        
        release_dir = Path("发布")
        release_dir.mkdir(exist_ok=True)
        
        if build_type == "single":
            exe_name = f"{self.project_name}.exe"
            exe_path = Path("dist") / exe_name
            if exe_path.exists():
                shutil.copy2(exe_path, release_dir / exe_name)
                print(f"  复制 {exe_name}")
        else:
            # 目录版本
            dir_name = f"{self.project_name}_目录版"
            src_dir = Path("dist") / dir_name
            dst_dir = release_dir / dir_name
            if src_dir.exists():
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                print(f"  复制 {dir_name}/")
        
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
    
    def create_usage_guide(self, release_dir):
        """创建使用说明"""
        guide_content = f"""🚴 {self.project_name} - 使用说明
================================

📋 快速开始:
1. 双击运行 "{self.project_name}.exe"
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
- {self.project_name}.exe: 主程序
- README.md: 详细文档
- export_file/: 导出的 GPX 文件存放目录

🆘 技术支持:
如遇问题，请查看 README.md 文件中的常见问题部分
"""
        
        guide_path = release_dir / "使用说明.txt"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print("  创建使用说明.txt")
    
    def build(self, build_type="single"):
        """执行构建"""
        print(f"🚀 开始构建 {build_type} 版本...")
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
        if build_type == "single":
            success = self.build_single_file()
        else:
            success = self.build_directory()
        
        if not success:
            return False
        
        # 5. 创建发布包
        self.create_release_package(build_type)
        
        print("=" * 50)
        print("🎉 构建完成!")
        print(f"📁 输出目录: 发布/")
        print("💡 可以直接运行发布目录中的程序")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="行者数据导出工具 - Windows 打包脚本")
    parser.add_argument("--type", choices=["single", "directory"], default="single",
                       help="构建类型: single(单文件) 或 directory(目录)")
    parser.add_argument("--clean", action="store_true", help="仅清理构建目录")
    
    args = parser.parse_args()
    
    builder = ExeBuilder()
    
    if args.clean:
        builder.clean_build()
        print("✅ 清理完成")
        return
    
    success = builder.build(args.type)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
