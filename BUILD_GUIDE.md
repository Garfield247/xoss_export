# 🚴 行者数据导出工具 - 跨平台打包指南

本指南介绍如何在 Windows、macOS、Linux 系统下将行者数据导出工具打包成可执行文件。

## 📋 准备工作

### 环境要求
- **Windows**: Windows 7/8/10/11
- **macOS**: macOS 10.14+ (Mojave 或更高版本)
- **Linux**: Ubuntu 18.04+, CentOS 7+, 或其他主流发行版
- **Python**: Python 3.7+ (推荐 Python 3.8+)
- **网络连接**: 用于下载依赖

### 必要文件
确保以下文件存在于项目目录中：
- `xoss_export_gui.py` - GUI 主程序
- `xoss_export.py` - 核心导出模块
- `requirements.txt` - 依赖列表
- `README.md` - 项目文档

## 🚀 快速打包

### 方法一：使用通用脚本（推荐）

1. **运行通用打包脚本**
   ```bash
   # 自动检测系统并打包
   python build_universal.py
   ```

2. **等待打包完成**
   - 脚本会自动检测操作系统
   - 自动安装依赖
   - 自动清理旧的构建文件
   - 生成对应平台的可执行文件

3. **运行程序**
   - Windows: 进入 `发布_windows/` 目录，双击 `行者数据导出工具.exe`
   - macOS: 进入 `发布_macos/` 目录，双击 `XossExport.app`
   - Linux: 进入 `发布_linux/` 目录，运行 `./xoss-export`

### 方法二：使用平台专用脚本

#### Windows
```batch
# 双击运行
build.bat

# 或使用 Python 脚本
python build_exe.py
python advanced_build.py --type single
```

#### macOS
```bash
# 使用 Shell 脚本
./build_mac.sh

# 或使用 Python 脚本
python build_mac.py
python build_mac.py --dmg  # 创建 DMG 安装包
```

### 方法二：使用 Python 脚本

1. **运行基础打包脚本**
   ```bash
   python build_exe.py
   ```

2. **运行高级打包脚本**
   ```bash
   # 单文件版本（推荐）
   python advanced_build.py --type single
   
   # 目录版本
   python advanced_build.py --type directory
   
   # 仅清理构建目录
   python advanced_build.py --clean
   ```

## 🔧 手动打包

如果自动脚本出现问题，可以手动执行：

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 清理旧文件
```bash
# 删除旧的构建文件
rmdir /s build
rmdir /s dist
del *.spec
```

### 3. 执行打包
```bash
# 单文件版本
pyinstaller --onefile --windowed --name "行者数据导出工具" xoss_export_gui.py

# 目录版本
pyinstaller --onedir --windowed --name "行者数据导出工具" xoss_export_gui.py
```

## 📦 打包选项说明

### 单文件版本 (--onefile)
- **优点**: 只有一个 exe 文件，便于分发
- **缺点**: 启动较慢，文件较大
- **适用**: 个人使用，小范围分发

### 目录版本 (--onedir)
- **优点**: 启动快，文件较小
- **缺点**: 包含多个文件，需要整个目录
- **适用**: 企业内部使用，频繁使用

### 常用参数
- `--windowed`: 不显示控制台窗口（GUI 程序必需）
- `--name`: 指定生成的 exe 文件名
- `--add-data`: 添加额外文件到打包中
- `--hidden-import`: 指定隐藏导入的模块
- `--clean`: 清理临时文件
- `--noconfirm`: 不询问确认

## 🐛 常见问题

### Q: 打包失败，提示缺少模块
A: 使用 `--hidden-import` 参数指定缺少的模块：
```bash
pyinstaller --hidden-import PyQt5.QtCore --hidden-import requests xoss_export_gui.py
```

### Q: exe 文件太大
A: 尝试以下优化：
1. 使用 `--exclude-module` 排除不需要的模块
2. 使用目录版本而不是单文件版本
3. 使用 UPX 压缩（需要安装 UPX）

### Q: 程序无法启动
A: 检查以下问题：
1. 确保所有依赖都已正确打包
2. 检查是否有杀毒软件误报
3. 尝试在命令行运行查看错误信息

### Q: 中文显示乱码
A: 确保：
1. 源代码文件使用 UTF-8 编码
2. 在代码中正确设置编码
3. 使用支持中文的字体

### Q: macOS 下程序无法运行
A: 尝试以下解决方案：
1. 右键点击应用程序，选择"打开"
2. 在"系统偏好设置 > 安全性与隐私"中允许运行
3. 使用终端运行：`xattr -cr XossExport.app`

### Q: macOS 下如何创建 DMG 安装包
A: 使用以下命令：
```bash
python build_mac.py --dmg
```
或手动创建：
```bash
hdiutil create -volname "行者数据导出工具" -srcfolder dist/XossExport.app -ov -format UDZO 行者数据导出工具.dmg
```

## 📁 输出文件结构

### Windows 版本
```
发布_windows/
├── 行者数据导出工具.exe    # 主程序
├── README.md              # 项目文档
├── 使用说明.txt           # 使用说明
└── export_file/           # 导出目录（空）
```

### macOS 版本
```
发布_macos/
├── XossExport.app         # 主程序（应用程序包）
├── 行者数据导出工具.dmg    # DMG 安装包（可选）
├── README.md              # 项目文档
├── 使用说明.txt           # 使用说明
└── export_file/           # 导出目录（空）
```

### Linux 版本
```
发布_linux/
├── xoss-export            # 主程序
├── README.md              # 项目文档
├── 使用说明.txt           # 使用说明
└── export_file/           # 导出目录（空）
```

## 🔄 更新版本

更新程序版本时：
1. 修改源代码
2. 更新版本号
3. 重新运行打包脚本
4. 测试新版本功能
5. 发布新版本

## 📞 技术支持

如果遇到打包问题：
1. 查看错误日志
2. 检查 Python 和依赖版本
3. 尝试不同的打包参数
4. 参考 PyInstaller 官方文档

---

**注意**: 打包后的 exe 文件可能被杀毒软件误报，这是正常现象。如果确定文件来源可信，可以添加到白名单中。
