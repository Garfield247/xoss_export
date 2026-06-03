#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行者数据导出工具 - GUI版本
使用 PyQt5 开发的图形界面版本
"""

import sys
import os

# 屏蔽 QtWebEngine 的冗余日志输出
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--log-level=3"

import time
import threading
import json
import requests
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QFileDialog,
    QProgressBar,
    QGroupBox,
    QMessageBox,
    QSplitter,
    QFrame,
    QDialog,
    QRadioButton,
    QButtonGroup,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QStandardPaths
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QImage
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtNetwork import QNetworkCookie

# 导入核心导出功能
from xoss_export import run_export, convert_sport_to_number


class SettingsManager:
    """配置管理类"""
    def __init__(self, app_name="xoss_export"):
        # 获取系统标准的 AppData 路径
        self.data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
        self.config_file = self.data_dir / "config.json"
        self.avatar_file = self.data_dir / "avatar.jpg"
        self.settings = self.load_settings()

    def load_settings(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_settings(self, settings):
        self.settings.update(settings)
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def clear(self):
        """完全清除配置和头像文件"""
        self.settings = {}
        if self.config_file.exists():
            self.config_file.unlink()
        if self.avatar_file.exists():
            self.avatar_file.unlink()

    def get(self, key, default=None):
        return self.settings.get(key, default)


class SilentWebEnginePage(QWebEnginePage):
    """自定义页面类，静默 JS 控制台输出"""
    def javaScriptConsoleMessage(self, level, message, lineID, sourceID):
        # 忽略所有来自网页控制台的消息
        pass


class LoginDialog(QDialog):
    """登录对话框"""
    login_success = pyqtSignal(dict)  # 发送登录成功的用户信息和cookie

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录行者")
        self.resize(1000, 700)
        self.layout = QVBoxLayout(self)
        
        self.browser = QWebEngineView()
        # 使用静默页面处理器
        self.browser.setPage(SilentWebEnginePage(self.browser))
        self.layout.addWidget(self.browser)
        
        # 获取 Cookie 存储
        self.profile = QWebEngineProfile.defaultProfile()
        self.cookie_store = self.profile.cookieStore()
        self.cookie_store.cookieAdded.connect(self.on_cookie_added)
        
        self.cookies_dict = {}
        self.is_logging_in = False
        
        # 加载登录页面
        self.browser.load(QUrl("https://www.imxingzhe.com/login"))

    def on_cookie_added(self, cookie):
        name = cookie.name().data().decode()
        value = cookie.value().data().decode()
        self.cookies_dict[name] = value
        
        # 如果检测到 sessionid，尝试获取用户信息
        if "sessionid" in self.cookies_dict and not self.is_logging_in:
            self.check_login_status()

    def check_login_status(self):
        self.is_logging_in = True
        # 组装 Cookie 字符串
        cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies_dict.items()])
        
        # 使用多线程或异步方式检查，这里简单处理
        threading.Thread(target=self._verify_cookie, args=(cookie_str,), daemon=True).start()

    def _verify_cookie(self, cookie_str):
        url = "https://www.imxingzhe.com/api/v1/user/user_info/"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            "Cookie": cookie_str,
            "Referer": "https://www.imxingzhe.com/"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    user_data = data.get("data", {})
                    result = {
                        "cookies": cookie_str,
                        "username": user_data.get("username"),
                        "user_id": user_data.get("id"),
                        "avatar_url": user_data.get("avatar")
                    }
                    self.login_success.emit(result)
                    QTimer.singleShot(0, self.accept)
                    return
        except Exception as e:
            print(f"验证登录失败: {e}")
        
        self.is_logging_in = False


class ExportThread(QThread):
    """导出线程"""
    progress_update = pyqtSignal(str)
    progress_bar_update = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(bool, str)
    
    def __init__(self, cookies, output_dir, limit, sport, year, month, file_format):
        super().__init__()
        self.cookies = cookies
        self.output_dir = output_dir
        self.limit = limit
        self.sport = sport
        self.year = year
        self.month = month
        self.file_format = file_format
        self.is_running = True
    
    def run(self):
        """运行导出任务"""
        try:
            # 直接调用核心导出功能，不使用重定向
            from xoss_export import XossExport, convert_sport_to_number
            
            # 创建导出实例
            xe = XossExport(self.cookies, self.output_dir)
            
            def gui_print_status(message, status="INFO"):
                """重写状态打印方法"""
                self.progress_update.emit(f"[{status}] {message}")
            
            def gui_print_final_stats():
                """重写最终统计打印方法"""
                if xe.start_time:
                    import time
                    elapsed_time = time.time() - xe.start_time
                    minutes = int(elapsed_time // 60)
                    seconds = int(elapsed_time % 60)
                    
                    self.progress_update.emit("=" * 50)
                    self.progress_update.emit("导出完成！")
                    self.progress_update.emit(f"总耗时: {minutes}分{seconds}秒")
                    self.progress_update.emit(f"成功下载: {xe.total_downloaded} 个文件")
                    if xe.total_failed > 0:
                        self.progress_update.emit(f"下载失败: {xe.total_failed} 个文件")
                    self.progress_update.emit(f"导出目录: {xe.export_path.absolute()}")
                    self.progress_update.emit("=" * 50)
            
            # 替换方法
            xe._print_status = gui_print_status
            xe._print_final_stats = gui_print_final_stats
            
            # 重写下载方法以支持进度条
            def gui_download_workout(title, sport_id, file_format=None):
                """重写下载方法"""
                fmt = file_format or self.file_format
                self.progress_update.emit(f"正在下载: {title}...")
                url = f"https://www.imxingzhe.com/api/v1/workout/{sport_id}/{fmt}/"
                
                import os
                safe_title = title.replace(" ", "_").replace("/", "_").replace("\\", "_")
                filename = xe.export_path / f"{safe_title}_{sport_id}.{fmt}"

                try:
                    response = xe.session.get(url, headers=xe.headers)
                    response.raise_for_status()

                    with open(filename, "wb") as file:
                        file.write(response.content)

                    xe.total_downloaded += 1
                    return True
                    
                except Exception as e:
                    xe.total_failed += 1
                    self.progress_update.emit(f"下载失败: {title} (ID: {sport_id}, 格式: {fmt}) - {str(e)}")
                    return False
            
            xe.download_workout_file = gui_download_workout
            
            # 手动执行导出逻辑以支持进度条
            xe.start_time = time.time()
            self.progress_update.emit("开始导出行者数据...")
            self.progress_update.emit(f"导出目录: {xe.export_path.absolute()}")
            
            # 显示筛选条件
            if self.sport:
                sport_display = self.sport if self.sport.isdigit() else f"{self.sport}({convert_sport_to_number(self.sport)})"
                self.progress_update.emit(f"运动类型筛选: {sport_display}")
            if self.year:
                self.progress_update.emit(f"年份筛选: {self.year}")
            if self.month:
                self.progress_update.emit(f"月份筛选: {self.month}")
            
            offset = 0
            total_items = 0
            processed_items = 0
            
            while True:
                data = xe.get_pgworkout(offset, self.limit, self.sport, self.year, self.month)
                if not data:
                    break
                
                sport_list = data.get("data", {}).get("data", [])
                if not sport_list:
                    break
                
                # 如果是第一批数据，显示总数
                if offset == 0:
                    total_count = data.get("data", {}).get("total", 0)
                    if total_count > 0:
                        total_items = total_count
                        self.progress_update.emit(f"发现 {total_items} 条运动记录")
                
                # 显示当前页面信息
                page_num = (offset // self.limit) + 1
                self.progress_update.emit(f"正在处理第 {page_num} 页，共 {len(sport_list)} 个文件")
                
                # 下载当前批次的文件
                for i, s in enumerate(sport_list):
                    if not self.is_running:
                        return
                        
                    processed_items += 1
                    title = s.get("title", "未知标题")
                    sport_id = s.get("id")
                    
                    # 更新进度条
                    self.progress_bar_update.emit(i + 1, len(sport_list), title)
                    
                    xe.download_workout_file(title, sport_id, self.file_format)
                    
                    time.sleep(1)  # 避免请求过于频繁
                
                # 页面下载完成，显示总体进度
                if total_items > 0:
                    self.progress_update.emit(f"第 {page_num} 页完成，总体进度: {processed_items}/{total_items}")
                else:
                    self.progress_update.emit(f"第 {page_num} 页完成，已处理 {processed_items} 个文件")
                
                offset += self.limit
            
            # 显示最终统计
            gui_print_final_stats()
            self.finished.emit(True, "导出完成")
            
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def stop(self):
        """停止导出"""
        self.is_running = False
        self.terminate()


class XossExportGUI(QMainWindow):
    """主窗口类"""
    avatar_ready = pyqtSignal(bytes)  # 新增信号：用于传递下载好的图片数据
    
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.export_thread = None
        self._avatar_loading = False  # 下载锁
        
        # 连接信号
        self.avatar_ready.connect(self._on_avatar_ready)
        
        # 获取默认桌面路径
        desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        
        self.user_info = {
            "cookies": self.settings_manager.get("cookies", ""),
            "username": self.settings_manager.get("username", "未登录"),
            "avatar_url": self.settings_manager.get("avatar_url", ""),
            "user_id": self.settings_manager.get("user_id", ""),
            "output_dir": self.settings_manager.get("output_dir", desktop_path)
        }
        self.init_ui()
        self.setup_styles()
        self.update_user_ui()  # 确保初始状态正确
        
        # 初始加载时尝试刷新用户信息
        if self.user_info["cookies"]:
            QTimer.singleShot(500, self.refresh_user_info)
    
    def get_resource_path(self, relative_path):
        """获取资源文件的绝对路径 (支持 PyInstaller 打包)"""
        try:
            # PyInstaller 创建临时文件夹并把路径存储在 _MEIPASS 中
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("🚴 行者数据导出工具 - GUI版本")
        self.setGeometry(100, 100, 800, 600)
        
        # 设置窗口图标
        icon_jpg = self.get_resource_path("icon.jpg")
        icon_ico = self.get_resource_path("icon.ico")
        
        if os.path.exists(icon_jpg):
            self.setWindowIcon(QIcon(icon_jpg))
        elif os.path.exists(icon_ico):
            self.setWindowIcon(QIcon(icon_ico))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # 右侧日志面板
        log_panel = self.create_log_panel()
        splitter.addWidget(log_panel)
        
        # 设置分割器比例
        splitter.setSizes([400, 400])
        
        # 底部状态栏
        self.create_status_bar()
    
    def refresh_user_info(self):
        """刷新用户信息"""
        if not self.user_info["cookies"]:
            self.update_user_ui()
            return
            
        def _fetch():
            url = "https://www.imxingzhe.com/api/v1/user/user_info/"
            headers = {
                "Accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
                "Cookie": self.user_info["cookies"],
                "Referer": "https://www.imxingzhe.com/"
            }
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 0:
                        user_data = data.get("data", {})
                        self.user_info.update({
                            "username": user_data.get("username"),
                            "user_id": user_data.get("id"),
                            "avatar_url": user_data.get("avatar")
                        })
            except Exception as e:
                print(f"刷新用户信息失败: {e}")
            
            QTimer.singleShot(0, self.update_user_ui)

        threading.Thread(target=_fetch, daemon=True).start()

    def update_user_ui(self):
        """更新用户界面显示"""
        self.username_label.setText(self.user_info["username"])
        self.user_id_label.setText(f"ID: {self.user_info['user_id']}" if self.user_info["user_id"] else "未登录")
        
        # 切换按钮显示
        is_logged_in = bool(self.user_info["cookies"])
        self.login_button.setVisible(not is_logged_in)
        self.logout_button.setVisible(is_logged_in)
        
        # 处理头像显示
        if is_logged_in:
            avatar_path = self.settings_manager.avatar_file
            if avatar_path.exists():
                pixmap = QPixmap(str(avatar_path))
                if not pixmap.isNull():
                    self.avatar_label.setPixmap(pixmap)
                    return
            
            # 如果本地没有或加载失败，且有 URL，则下载
            if self.user_info["avatar_url"] and not self._avatar_loading:
                self._avatar_loading = True
                threading.Thread(target=self._load_avatar, args=(self.user_info["avatar_url"],), daemon=True).start()
        else:
            self.avatar_label.clear()

    def logout(self):
        """退出登录"""
        reply = QMessageBox.question(self, "确认退出", "确定要退出登录并清除保存的信息吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        # 清除内存数据
        self.user_info = {
            "cookies": "",
            "username": "未登录",
            "avatar_url": "",
            "user_id": ""
        }
        # 清除持久化文件 (config.json 和 avatar.jpg)
        self.settings_manager.clear()
        
        # 彻底清除浏览器数据
        profile = QWebEngineProfile.defaultProfile()
        profile.cookieStore().deleteAllCookies()
        profile.clearHttpCache()
        profile.clearAllVisitedLinks()
        profile.cookieStore().loadAllCookies()
        
        # 更新界面
        self.update_user_ui()
        QMessageBox.information(self, "已退出", "已退出登录。下次登录时将需要重新输入账号或扫码。")

    def _load_avatar(self, url):
        """后台线程下载头像"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # 保存到本地文件
                with open(self.settings_manager.avatar_file, "wb") as f:
                    f.write(response.content)
                # 发送信号回主线程更新 UI
                self.avatar_ready.emit(response.content)
            else:
                self._avatar_loading = False
        except Exception as e:
            print(f"加载头像出错: {e}")
            self._avatar_loading = False

    def _on_avatar_ready(self, data):
        """主线程接收到图片数据后的处理"""
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.avatar_label.setPixmap(pixmap)
            self.avatar_label.repaint()  # 强制立即重绘
        self._avatar_loading = False

    def open_login_dialog(self):
        """打开登录对话框"""
        dialog = LoginDialog(self)
        dialog.login_success.connect(self.on_login_success)
        dialog.exec_()

    def on_login_success(self, data):
        """登录成功回调"""
        self.user_info.update(data)
        # 保存到配置
        self.settings_manager.save_settings(self.user_info)
        # 更新界面
        self.update_user_ui()
        QMessageBox.information(self, "登录成功", f"欢迎回来，{data['username']}！")

    def create_control_panel(self):
        """创建控制面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("🚴 行者数据导出工具")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 用户信息组 (替代原 Cookie 输入组)
        user_group = QGroupBox("用户信息")
        user_layout = QHBoxLayout(user_group)
        
        # 头像
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(60, 60)
        self.avatar_label.setStyleSheet("border-radius: 30px; border: 1px solid #ddd;")
        self.avatar_label.setScaledContents(True)
        user_layout.addWidget(self.avatar_label)
        
        # 用户名和 ID
        user_info_layout = QVBoxLayout()
        self.username_label = QLabel(self.user_info["username"])
        self.username_label.setFont(QFont("Arial", 12, QFont.Bold))
        user_info_layout.addWidget(self.username_label)
        
        self.user_id_label = QLabel(f"ID: {self.user_info['user_id']}" if self.user_info["user_id"] else "未登录")
        user_info_layout.addWidget(self.user_id_label)
        user_layout.addLayout(user_info_layout)
        
        user_layout.addStretch()
        
        # 登录/退出按钮
        button_container = QVBoxLayout()
        self.login_button = QPushButton("登录账号")
        self.login_button.clicked.connect(self.open_login_dialog)
        button_container.addWidget(self.login_button)
        
        self.logout_button = QPushButton("退出登录")
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setStyleSheet("color: #f44336;")
        button_container.addWidget(self.logout_button)
        
        user_layout.addLayout(button_container)
        
        layout.addWidget(user_group)
        
        # 导出设置组
        settings_group = QGroupBox("导出设置")
        settings_layout = QGridLayout(settings_group)
        
        # 输出目录
        settings_layout.addWidget(QLabel("输出目录:"), 0, 0)
        self.output_dir_input = QLineEdit(self.user_info["output_dir"])
        settings_layout.addWidget(self.output_dir_input, 0, 1)
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_output_dir)
        settings_layout.addWidget(self.browse_button, 0, 2)
        
        # 导出文件格式
        settings_layout.addWidget(QLabel("导出格式:"), 1, 0)
        format_layout = QHBoxLayout()
        self.gpx_radio = QRadioButton("GPX")
        self.fit_radio = QRadioButton("FIT")
        self.gpx_radio.setChecked(True)
        
        self.format_group = QButtonGroup(self)
        self.format_group.addButton(self.gpx_radio)
        self.format_group.addButton(self.fit_radio)
        
        format_layout.addWidget(self.gpx_radio)
        format_layout.addWidget(self.fit_radio)
        format_layout.addStretch()
        settings_layout.addLayout(format_layout, 1, 1)
        
        layout.addWidget(settings_group)
        
        # 筛选条件组 (设为扩展以填充空间)
        filter_group = QGroupBox("筛选条件")
        filter_layout = QGridLayout(filter_group)
        filter_layout.setSpacing(15)  # 增加控件间距
        
        # 运动类型
        filter_layout.addWidget(QLabel("运动类型:"), 0, 0)
        self.sport_combo = QComboBox()
        self.sport_combo.addItems([
            "全部", "徒步", "跑步", "骑行", "游泳", "滑雪", 
            "训练", "室内骑行", "虚拟骑行", "其他"
        ])
        filter_layout.addWidget(self.sport_combo, 0, 1)
        
        # 年份
        filter_layout.addWidget(QLabel("年份:"), 1, 0)
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("如: 2024")
        filter_layout.addWidget(self.year_input, 1, 1)
        
        # 月份
        filter_layout.addWidget(QLabel("月份:"), 2, 0)
        self.month_combo = QComboBox()
        self.month_combo.addItems(["全部", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])
        filter_layout.addWidget(self.month_combo, 2, 1)
        
        layout.addWidget(filter_group)
        layout.setStretchFactor(filter_group, 1)  # 让筛选组占用更多剩余空间
        
        # 按钮组
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        self.start_button = QPushButton("🚀 开始导出")
        self.start_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.start_button.setFixedHeight(60)  # 稍微加高一点按钮
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_button.clicked.connect(self.start_export)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("🛑 停止导出")
        self.stop_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.stop_button.setFixedHeight(60)  # 稍微加高一点按钮
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_button.clicked.connect(self.stop_export)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        return panel

    def create_log_panel(self):
        """创建日志面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # 标题
        log_title = QLabel("📋 导出日志")
        log_title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(log_title)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 9))
        layout.addWidget(self.log_text)
        layout.setStretchFactor(self.log_text, 1)  # 让日志框填充整个面板空间
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 清空日志按钮
        clear_button = QPushButton("🗑️ 清空日志")
        clear_button.clicked.connect(self.clear_log)
        layout.addWidget(clear_button)
        
        return panel
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
    
    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 2px solid #4CAF50;
            }
        """)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.output_dir_input.text()
        )
        if directory:
            self.output_dir_input.setText(directory)
            # 记住修改后的路径
            self.user_info["output_dir"] = directory
            self.settings_manager.save_settings({"output_dir": directory})
    
    def validate_inputs(self):
        """验证输入"""
        if not self.user_info["cookies"] or "sessionid=" not in self.user_info["cookies"]:
            QMessageBox.warning(self, "认证错误", "请先点击[登录账号]进行登录")
            return False
        return True

    def start_export(self):
        """开始导出"""
        if not self.validate_inputs():
            return

        # 获取参数
        cookies = self.user_info["cookies"]
        base_dir = self.output_dir_input.text().strip()
        # 记住手动修改后的基础路径
        self.user_info["output_dir"] = base_dir
        self.settings_manager.save_settings({"output_dir": base_dir})
        
        limit = 10  # 固定为 10
        file_format = "gpx" if self.gpx_radio.isChecked() else "fit"
        
        # 自动创建带时间戳的子目录: 格式_月日时分秒
        timestamp = time.strftime("%m%d%H%M%S")
        sub_dir_name = f"{file_format}_{timestamp}"
        final_output_dir = str(Path(base_dir) / sub_dir_name)
        
        sport_name = self.sport_combo.currentText()
        sport_param = "" if sport_name == "全部" else convert_sport_to_number(sport_name)
        
        year = self.year_input.text().strip()
        month_name = self.month_combo.currentText()
        month_param = "" if month_name == "全部" else month_name
        
        # 更新UI状态
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.status_bar.showMessage("正在导出...")
        
        # 清空日志
        self.log_text.clear()
        self.log_text.append("🚀 开始导出数据...")
        self.log_text.append(f"📁 基础目录: {base_dir}")
        self.log_text.append(f"📂 导出目录: {final_output_dir}")
        if sport_name != "全部":
            self.log_text.append(f"🏃 运动类型: {sport_name}")
        if year:
            self.log_text.append(f"📅 年份: {year}")
        if month_name != "全部":
            self.log_text.append(f"📅 月份: {month_name}")
        self.log_text.append("-" * 50)
        
        # 创建并启动导出线程
        self.export_thread = ExportThread(
            cookies, final_output_dir, limit, sport_param, year, month_param, file_format
        )
        self.export_thread.progress_update.connect(self.update_log)
        self.export_thread.progress_bar_update.connect(self.update_progress_bar)
        self.export_thread.finished.connect(self.export_finished)
        self.export_thread.start()
    
    def stop_export(self):
        """停止导出"""
        if self.export_thread and self.export_thread.isRunning():
            self.export_thread.stop()
            self.export_thread.wait()
        
        self.export_finished(False, "用户取消导出")
    
    def update_log(self, message):
        """更新日志"""
        self.log_text.append(message)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_progress_bar(self, current, total, filename):
        """更新进度条"""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
            self.progress_bar.setFormat(f"{current}/{total} - {filename[:30]}...")
        else:
            self.progress_bar.setRange(0, 0)  # 不确定进度
    
    def export_finished(self, success, message):
        """导出完成"""
        # 更新UI状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_bar.showMessage("导出完成")
            self.log_text.append("✅ " + message)
            QMessageBox.information(self, "导出完成", message)
        else:
            self.status_bar.showMessage("导出失败")
            self.log_text.append("❌ 错误: " + message)
            QMessageBox.critical(self, "导出错误", message)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("日志已清空")


def main():
    """启动应用程序"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 设置应用信息
    app.setApplicationName("行者数据导出工具")
    app.setApplicationVersion("3.0.0")
    
    gui = XossExportGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
