# -*- coding: utf-8 -*-

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from threading import Thread, Event
from queue import Queue
import base64
from PIL import Image, ImageTk
import io

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None

from .. import __version__
from ..telnet_manager import TelnetManager
from .log_manager import LogManager
from .chart_manager import ChartManager
from .config_manager import ConfigManager
from .command_editor import CommandEditor

class MainWindow(tk.Tk):
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 设置窗口标题和大小
        self.title("Telnet命令测试工具")
        self.geometry("1200x800")
        
        # 初始化变量
        self._init_variables()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建上下分割区域
        self.upper_frame = ttk.Frame(self.main_frame)
        self.upper_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左右分割区域
        self.upper_left = ttk.Frame(self.upper_frame)
        self.upper_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建日志区域
        self.lower_left = ttk.Frame(self.upper_frame)
        self.lower_left.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 初始化管理器
        self.log_manager = LogManager(self)
        self.command_editor = CommandEditor(self)
        self.config_manager = ConfigManager(self)
        
        # 创建界面元素
        self.create_style()
        self.create_toolbar()
        self.create_menus()
        self.create_widgets()
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _init_variables(self):
        """初始化变量"""
        self.telnet_manager = None
        self.stop_event = Event()
        self.telnet_thread = None
        self.is_auto_scroll = tk.BooleanVar(value=True)
        self.test_results = []
        self.excel_data = []
        self.output_mode_var = tk.StringVar(value="do_not_generate")
        self.stop_on_error_var = tk.BooleanVar(value=False)
        self.timeout_var = tk.IntVar(value=10)
        self.log_file_path = None
        self.excel_file_path = None
        self.progress_var = tk.DoubleVar(value=0.0)  # 添加进度变量

    def create_style(self):
        """创建样式"""
        style = ttk.Style()
        
        # 工具栏按钮样式
        style.configure(
            "Toolbar.TButton",
            padding=(5, 2),  # 减小内边距
            relief="flat",
            font=("Microsoft YaHei UI", 9)  # 设置字体
        )
        
        # 普通按钮样式
        style.configure(
            "TButton",
            padding=(5, 2),  # 减小内边距
            font=("Microsoft YaHei UI", 9)
        )

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=(5,0))
        
        def create_button(text, command, tooltip=None):
            """创建工具栏按钮的辅助函数"""
            btn = ttk.Button(
                toolbar,
                text=text,
                style="Toolbar.TButton",
                command=command
            )
            btn.pack(side=tk.LEFT, padx=2)
            return btn
        
        # 连接按钮
        self.connect_btn = create_button("连接", self.connect_telnet)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # 开始/停止按钮
        create_button("开始", self.start_telnet_thread)
        create_button("停止", self.stop_execution)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # 编辑器按钮
        create_button("编辑器", self.command_editor.open_advanced_editor)
        
        # 清除日志按钮
        create_button("清除", self.log_manager.clear_log)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # 设置按钮
        create_button("设置", lambda: self.notebook.select(0))

    def create_menus(self):
        """创建菜单"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="导入配置", command=self.config_manager.import_config)
        config_menu.add_command(label="导出配置", command=self.config_manager.export_config)
        menubar.add_cascade(label="配置", menu=config_menu)

        editor_menu = tk.Menu(menubar, tearoff=0)
        editor_menu.add_command(label="打开命令编辑器", command=self.command_editor.open_advanced_editor)
        menubar.add_cascade(label="编辑器", menu=editor_menu)

    def create_widgets(self):
        """创建控件"""
        # 创建选项卡
        self.notebook = ttk.Notebook(self.upper_left)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 基本设置标签页
        basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(basic_frame, text="基本设置")

        # Telnet连接设置
        conn_frame = ttk.LabelFrame(basic_frame, text="连接设置", padding=5)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(conn_frame, text="Telnet IP:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.host_var = tk.StringVar(value="192.168.0.21")
        ttk.Entry(conn_frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(conn_frame, text="Telnet端口:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        self.port_var = tk.IntVar(value=81)
        ttk.Entry(conn_frame, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        connect_btn = ttk.Button(
            conn_frame, 
            text="连接",
            command=self.connect_telnet
        )
        connect_btn.grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)

        # 命令设置
        cmd_frame = ttk.LabelFrame(basic_frame, text="命令设置", padding=5)
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(cmd_frame, text="命令文件:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.commands_file_var = tk.StringVar(value="commands.txt")
        ttk.Entry(cmd_frame, textvariable=self.commands_file_var, width=40).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(cmd_frame, text="选择文件", command=self.config_manager.select_commands_file).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        ttk.Label(cmd_frame, text="循环次数:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.loop_count_var = tk.IntVar(value=1)
        ttk.Entry(cmd_frame, textvariable=self.loop_count_var, width=8).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # 高级设置标签页
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="高级设置")

        # 时间设置
        time_frame = ttk.LabelFrame(advanced_frame, text="时间设置", padding=5)
        time_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(time_frame, text="命令执行延迟(毫秒):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.delay_ms_var = tk.IntVar(value=0)
        ttk.Entry(time_frame, textvariable=self.delay_ms_var, width=8).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(time_frame, text="超时时间(秒):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(time_frame, textvariable=self.timeout_var, width=8).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        # 错误处理
        error_frame = ttk.LabelFrame(advanced_frame, text="错误处理", padding=5)
        error_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Radiobutton(error_frame, text="继续执行", variable=self.stop_on_error_var, value=False).pack(side=tk.LEFT, padx=20)
        ttk.Radiobutton(error_frame, text="立即停止", variable=self.stop_on_error_var, value=True).pack(side=tk.LEFT, padx=20)

        # 输出设置标签页
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="输出设置")

        # 输出模式
        mode_frame = ttk.LabelFrame(output_frame, text="输出模式", padding=5)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Radiobutton(mode_frame, text="不生成文件", variable=self.output_mode_var, value="do_not_generate").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(mode_frame, text="仅日志文件", variable=self.output_mode_var, value="log").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(mode_frame, text="仅Excel文件", variable=self.output_mode_var, value="excel").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(mode_frame, text="两种都生成", variable=self.output_mode_var, value="both").pack(anchor=tk.W, padx=20, pady=2)

        # 日志设置
        log_frame = ttk.LabelFrame(output_frame, text="日志设置", padding=5)
        log_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(log_frame, text="日志目录:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.log_dir_var = tk.StringVar(value="telnet_logs")
        ttk.Entry(log_frame, textvariable=self.log_dir_var, width=40).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(log_frame, text="选择目录", command=self.config_manager.select_log_dir).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # 状态和控制区域
        status_frame = ttk.LabelFrame(self.upper_left, text="状态和控制", padding=5)
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        # 状态显示和进度条
        status_progress_frame = ttk.Frame(status_frame)
        status_progress_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Label(status_progress_frame, text="状态:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(status_progress_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # 进度条
        self.progress_bar = ttk.Progressbar(
            status_progress_frame,
            variable=self.progress_var,
            mode='determinate',
            length=200
        )
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 控制按钮
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame, 
            text="开始执行",
            command=self.start_telnet_thread
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="停止执行",
            command=self.stop_execution
        ).pack(side=tk.LEFT, padx=5)

        ttk.Checkbutton(button_frame, text="自动滚动", variable=self.is_auto_scroll).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="清除日志",
            command=self.log_manager.clear_log
        ).pack(side=tk.LEFT, padx=5)

    def connect_telnet(self):
        """连接到Telnet"""
        host = self.host_var.get()
        port = self.port_var.get()
        timeout = self.timeout_var.get()
        self.telnet_manager = TelnetManager(host, port, timeout=timeout)

        try:
            self.telnet_manager.connect()
            self.log_manager.write_log(f"已连接到 {host}:{port}")
            self.update_status("Telnet连接成功")
        except Exception as e:
            self.log_manager.write_log(f"连接失败: {e}")
            self.update_status("连接失败")
            self.telnet_manager = None

    def start_telnet_thread(self):
        """启动Telnet执行线程"""
        if self.telnet_thread and self.telnet_thread.is_alive():
            messagebox.showwarning("提示", "Telnet命令正在执行中，请停止或等待执行完成。")
            return

        if not self.telnet_manager or not self.telnet_manager.is_connected:
            messagebox.showinfo("提示", "请先点击'连接'按钮连接到Telnet。")
            return

        # 重置状态
        self.stop_event.clear()
        self.test_results.clear()
        self.excel_data.clear()

        # 设置日志文件路径
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        mode = self.output_mode_var.get()
        if mode != "do_not_generate":
            os.makedirs(self.log_dir_var.get(), exist_ok=True)
            self.log_file_path = os.path.join(
                self.log_dir_var.get(),
                f"telnet_log_{current_time}.txt"
            )
            self.excel_file_path = self.log_file_path.replace(".txt", ".xlsx")
        else:
            self.log_file_path = None
            self.excel_file_path = None

        # 启动执行线程
        self.telnet_thread = Thread(target=self.run_commands)
        self.telnet_thread.daemon = True
        self.telnet_thread.start()

    def stop_execution(self):
        """停止执行"""
        self.stop_event.set()

    def run_commands(self):
        """执行命令的线程函数"""
        self.update_status("执行中")
        try:
            # 获取命令文件路径
            commands_file = self.commands_file_var.get()
            if not os.path.exists(commands_file):
                self.log_manager.write_log(f"命令文件不存在: {commands_file}")
                return

            # 读取命令
            with open(commands_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 获取循环次数和延迟设置
            loop_count = self.loop_count_var.get()
            delay_ms = self.delay_ms_var.get()
            
            # 计算总命令数（排除注释和空行）
            valid_commands = [line for line in lines if line.strip() and not line.startswith('#')]
            total_commands = len(valid_commands) * loop_count
            executed_commands = 0

            # 执行命令
            for loop in range(loop_count):
                if self.stop_event.is_set():
                    self.log_manager.write_log("用户终止执行。")
                    break

                loop_start = time.time()
                self.log_manager.write_log(f"\n=== 开始第 {loop + 1} 轮执行 ===\n")

                for line in lines:
                    if self.stop_event.is_set():
                        break

                    command_str = line.strip()
                    if not command_str or command_str.startswith('#'):
                        continue

                    success = self.execute_one_command(command_str, delay_ms)
                    executed_commands += 1
                    self.after(0, self.update_progress, executed_commands, total_commands)

                    if not success and self.stop_on_error_var.get():
                        self.log_manager.write_log("检测到错误，停止执行")
                        self.stop_event.set()
                        break

                loop_end = time.time()
                self.log_manager.write_log(f"本轮执行时间: {loop_end - loop_start:.2f} 秒")

            # 生成输出文件
            self.generate_output_files()

            # 重置进度条并更新状态
            self.after(0, lambda: self.progress_var.set(0))
            self.after(0, lambda: self.update_status("执行完成"))

        except Exception as e:
            self.log_manager.write_log(f"执行过程中出错: {str(e)}")
            self.after(0, lambda: self.update_status("执行出错"))
            self.after(0, lambda: self.progress_var.set(0))

        finally:
            self.stop_event.clear()

    def execute_one_command(self, command_str, delay_ms):
        """执行单条命令"""
        try:
            # 执行命令前记录
            self.log_manager.write_log(f"命令: {command_str}")
            
            # 执行命令
            start_time = time.time()
            output, success = self.telnet_manager.execute_command(command_str)
            elapsed = time.time() - start_time
            
            # 格式化输出
            if output:
                # 直接写入原始输出，保持格式
                lines = str(output).splitlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('CIG-EVK-G2:>'):  # 跳过命令提示符
                        if line.startswith('Cmd:'):
                            self.log_manager.write_log(line, "NORMAL")
                        elif line.startswith('Data:'):
                            self.log_manager.write_log(line, "NORMAL")
                        elif line.startswith('Result:'):
                            tag = "RESULT_PASS" if "pass" in line.lower() else "RESULT_FAIL"
                            self.log_manager.write_log(line, tag)
            
            # 记录执行时间
            self.log_manager.write_log(f"命令执行时间: {elapsed:.3f} 秒\n")
            
            # 解析输出用于统计和Excel
            data_val, result_val = self.parse_telnet_output(output)
            
            # 记录到Excel数据
            self.excel_data.append([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                command_str,
                data_val,
                result_val
            ])
            
            # 执行延迟
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            
            return success

        except Exception as e:
            self.log_manager.write_log(f"执行命令 '{command_str}' 时出错: {str(e)}")
            return False

    def parse_telnet_output(self, output):
        """解析Telnet输出"""
        data_val = ""
        result_val = ""

        if output:
            lines = str(output).splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith("Data:"):
                    data_val = line[5:].strip()  # 去掉"Data:"前缀
                elif line.startswith("Result:"):
                    result_val = line[7:].strip()  # 去掉"Result:"前缀

        return data_val, result_val

    def update_progress(self, current, total):
        """更新进度条"""
        progress = (current / total) * 100 if total > 0 else 0
        self.progress_var.set(progress)
        self.update_status(f"正在执行: {current}/{total} ({progress:.1f}%)")
        self.update_idletasks()

    def generate_output_files(self):
        """生成输出文件"""
        mode = self.output_mode_var.get()
        if mode in ("excel", "both") and self.excel_file_path:
            if Workbook:
                try:
                    wb = Workbook()
                    ws = wb.active
                    ws.title = "测试结果"
                    ws.append(["命令", "数据", "结果"])

                    for row in self.excel_data:
                        ws.append(row)

                    wb.save(self.excel_file_path)
                    self.log_manager.write_log(f"Excel文件已保存到 {self.excel_file_path}")
                except Exception as e:
                    self.log_manager.write_log(f"保存Excel文件失败：{e}")
            else:
                self.log_manager.write_log("openpyxl模块未安装，无法保存Excel文件。")

    def update_status(self, message):
        """更新状态显示"""
        self.status_var.set(message)

    def on_closing(self):
        """关闭窗口时的处理"""
        self.stop_event.set()
        if self.telnet_thread and self.telnet_thread.is_alive():
            self.telnet_thread.join(timeout=2)
        if self.telnet_manager:
            self.telnet_manager.close()
        self.destroy() 