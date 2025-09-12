#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行者数据导出工具 - GUI版本
使用 PyQt5 开发的图形界面版本
"""

import sys
import os
import time
import threading
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
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# 导入核心导出功能
from xoss_export import run_export, convert_sport_to_number


class ExportThread(QThread):
    """导出线程"""
    progress_update = pyqtSignal(str)
    progress_bar_update = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(bool, str)
    
    def __init__(self, cookies, output_dir, limit, sport, year, month):
        super().__init__()
        self.cookies = cookies
        self.output_dir = output_dir
        self.limit = limit
        self.sport = sport
        self.year = year
        self.month = month
        self.is_running = True
    
    def run(self):
        """运行导出任务"""
        try:
            # 直接调用核心导出功能，不使用重定向
            from xoss_export import XossExport, convert_sport_to_number
            
            # 创建导出实例
            xe = XossExport(self.cookies, self.output_dir)
            
            # 重写进度显示方法
            original_print_status = xe._print_status
            original_print_final_stats = xe._print_final_stats
            
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
            original_download_gpx = xe.download_gpx
            
            def gui_download_gpx(title, sport_id):
                """重写下载方法"""
                url = f"https://www.imxingzhe.com/api/v1/pgworkout/{sport_id}/gpx/"
                
                # 使用 pathlib 构建文件路径
                import os
                safe_title = title.replace(" ", "_").replace("/", "_").replace("\\", "_")
                filename = xe.export_path / f"{safe_title}_{sport_id}.gpx"

                try:
                    response = xe.session.get(url, headers=xe.headers)
                    response.raise_for_status()

                    # 使用 pathlib 写入文件
                    with open(filename, "wb") as file:
                        file.write(response.content)

                    xe.total_downloaded += 1
                    return True
                    
                except Exception as e:
                    xe.total_failed += 1
                    self.progress_update.emit(f"下载失败: {title} (ID: {sport_id}) - {str(e)}")
                    return False
            
            xe.download_gpx = gui_download_gpx
            
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
                # 获取数据
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
                    
                    success = xe.download_gpx(title, sport_id)
                    if not success:
                        self.progress_update.emit(f"下载失败: {title}")
                    
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
    
    def __init__(self):
        super().__init__()
        self.export_thread = None
        self.init_ui()
        self.setup_styles()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("🚴 行者数据导出工具 - GUI版本")
        self.setGeometry(100, 100, 800, 600)
        
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
        
        # Cookie 输入组
        cookie_group = QGroupBox("认证信息")
        cookie_layout = QVBoxLayout(cookie_group)
        
        cookie_label = QLabel("Cookie:")
        cookie_layout.addWidget(cookie_label)
        
        self.cookie_input = QTextEdit()
        self.cookie_input.setMaximumHeight(100)
        self.cookie_input.setPlaceholderText("请粘贴从浏览器复制的完整Cookie字符串...")
        cookie_layout.addWidget(self.cookie_input)
        
        layout.addWidget(cookie_group)
        
        # 导出设置组
        settings_group = QGroupBox("导出设置")
        settings_layout = QGridLayout(settings_group)
        
        # 输出目录
        settings_layout.addWidget(QLabel("输出目录:"), 0, 0)
        self.output_dir_input = QLineEdit("export_file")
        settings_layout.addWidget(self.output_dir_input, 0, 1)
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_output_dir)
        settings_layout.addWidget(self.browse_button, 0, 2)
        
        # 每次请求数量
        settings_layout.addWidget(QLabel("每次请求数量:"), 1, 0)
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["10", "20", "50", "100"])
        self.limit_combo.setCurrentText("10")
        settings_layout.addWidget(self.limit_combo, 1, 1)
        
        layout.addWidget(settings_group)
        
        # 筛选条件组
        filter_group = QGroupBox("筛选条件")
        filter_layout = QGridLayout(filter_group)
        
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
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🚀 开始导出")
        self.start_button.clicked.connect(self.start_export)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹️ 停止导出")
        self.stop_button.clicked.connect(self.stop_export)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        
        # 添加弹性空间
        layout.addStretch()
        
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
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
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
    
    def validate_inputs(self):
        """验证输入"""
        # 获取Cookie并自动去除换行符和多余空格
        cookies = self.cookie_input.toPlainText().strip()
        # 去除所有换行符和多余空格，保持Cookie格式
        cookies = " ".join(cookies.split())
        
        if not cookies:
            QMessageBox.warning(self, "输入错误", "请输入Cookie")
            return False
        
        if "sessionid=" not in cookies:
            QMessageBox.warning(
                self, "Cookie错误", 
                "Cookie中必须包含sessionid字段\n请确保从浏览器复制的Cookie是完整的"
            )
            return False
        
        return True
    
    def start_export(self):
        """开始导出"""
        if not self.validate_inputs():
            return
        
        # 获取参数
        cookies = self.cookie_input.toPlainText().strip()
        # 去除所有换行符和多余空格
        cookies = " ".join(cookies.split())
        output_dir = self.output_dir_input.text().strip()
        limit = int(self.limit_combo.currentText())
        
        sport = self.sport_combo.currentText()
        if sport == "全部":
            sport = ""
        else:
            sport = convert_sport_to_number(sport)
        
        year = self.year_input.text().strip()
        month = self.month_combo.currentText()
        if month == "全部":
            month = ""
        
        # 更新UI状态
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.status_bar.showMessage("正在导出...")
        
        # 清空日志
        self.log_text.clear()
        self.log_text.append("🚀 开始导出数据...")
        self.log_text.append(f"📁 输出目录: {output_dir}")
        self.log_text.append(f"📊 每次请求数量: {limit}")
        if sport:
            self.log_text.append(f"🏃 运动类型: {sport}")
        if year:
            self.log_text.append(f"📅 年份: {year}")
        if month:
            self.log_text.append(f"📅 月份: {month}")
        self.log_text.append("-" * 50)
        
        # 创建并启动导出线程
        self.export_thread = ExportThread(
            cookies, output_dir, limit, sport, year, month
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
            self.log_text.append("❌ " + message)
            QMessageBox.critical(self, "导出失败", message)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("行者数据导出工具")
    app.setApplicationVersion("1.2.0")
    
    # 设置应用图标（如果有的话）
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = XossExportGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
