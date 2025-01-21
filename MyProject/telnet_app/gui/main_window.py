# -*- coding: utf-8 -*-

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from threading import Thread, Event
from queue import Queue

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
        super().__init__()
        self.title(f"Telnet命令测试工具 v{__version__} - 模块化版本")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # 创建样式
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", foreground="#333333", font=("Microsoft YaHei", 10))
        style.configure("TButton", font=("Microsoft YaHei", 10))
        style.configure("TEntry", font=("Microsoft YaHei", 10))

        # 创建版本号标签
        version_label = ttk.Label(
            self, 
            text=f"v{__version__}", 
            font=("Microsoft YaHei", 8),
            foreground="#666666"
        )
        version_label.pack(side=tk.BOTTOM, anchor=tk.SE, padx=5, pady=2)

        # ========== 核心变量 ==========
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

        # ========== 创建主框架 ==========
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建水平分隔窗口
        self.h_paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.h_paned.pack(fill=tk.BOTH, expand=True)

        # 创建左侧和右侧框架
        self.left_frame = ttk.Frame(self.h_paned)
        self.right_frame = ttk.Frame(self.h_paned)

        # 将框架添加到分隔窗口
        self.h_paned.add(self.left_frame, weight=3)  # 左侧占比更大
        self.h_paned.add(self.right_frame, weight=1)  # 右侧占比更小

        # 创建垂直分隔的上下区域（在左侧框架中）
        self.v_paned = ttk.PanedWindow(self.left_frame, orient=tk.VERTICAL)
        self.v_paned.pack(fill=tk.BOTH, expand=True)

        # 创建上下区域框架
        self.upper_left = ttk.Frame(self.v_paned)
        self.lower_left = ttk.Frame(self.v_paned)

        # 将框架添加到垂直分隔窗口
        self.v_paned.add(self.upper_left, weight=1)
        self.v_paned.add(self.lower_left, weight=1)

        # 设置样式
        style = ttk.Style()
        style.configure("TPanedwindow", background="#f0f0f0")
        style.configure("TFrame", background="#ffffff")

        # ========== 初始化管理器 ==========
        self.log_manager = LogManager(self)
        self.config_manager = ConfigManager(self)
        self.command_editor = CommandEditor(self)
        self.chart_manager = ChartManager(self.right_frame)  # 修改这里，直接传入right_frame

        # ========== 创建菜单和控件 ==========
        self.create_menus()
        self.create_widgets()

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
        # Telnet连接设置
        ttk.Label(self.upper_left, text="Telnet IP:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.host_var = tk.StringVar(value="192.168.0.21")
        ttk.Entry(self.upper_left, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(self.upper_left, text="Telnet端口:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.port_var = tk.IntVar(value=81)
        ttk.Entry(self.upper_left, textvariable=self.port_var, width=15).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        connect_btn = ttk.Button(self.upper_left, text="连接", command=self.connect_telnet)
        connect_btn.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

        # 循环次数
        ttk.Label(self.upper_left, text="循环次数:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.loop_count_var = tk.IntVar(value=1)
        ttk.Entry(self.upper_left, textvariable=self.loop_count_var, width=15).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        # 命令文件
        ttk.Label(self.upper_left, text="命令文件:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.commands_file_var = tk.StringVar(value="commands.txt")
        ttk.Entry(self.upper_left, textvariable=self.commands_file_var, width=40).grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(self.upper_left, text="选择文件", command=self.config_manager.select_commands_file).grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)

        # 日志目录
        ttk.Label(self.upper_left, text="日志目录:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.E)
        self.log_dir_var = tk.StringVar(value="telnet_logs")
        ttk.Entry(self.upper_left, textvariable=self.log_dir_var, width=40).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(self.upper_left, text="选择目录", command=self.config_manager.select_log_dir).grid(row=4, column=2, padx=5, pady=5, sticky=tk.W)

        # 延迟和超时设置
        ttk.Label(self.upper_left, text="命令执行延迟(毫秒):").grid(row=5, column=0, padx=5, pady=5, sticky=tk.E)
        self.delay_ms_var = tk.IntVar(value=0)
        ttk.Entry(self.upper_left, textvariable=self.delay_ms_var, width=15).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(self.upper_left, text="超时时间(秒):").grid(row=5, column=2, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(self.upper_left, textvariable=self.timeout_var, width=15).grid(row=5, column=3, padx=5, pady=5, sticky=tk.W)

        # 输出模式
        ttk.Label(self.upper_left, text="输出模式:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.E)
        mode_frame = ttk.Frame(self.upper_left)
        mode_frame.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="不生成文件", variable=self.output_mode_var, value="do_not_generate").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="仅日志文件", variable=self.output_mode_var, value="log").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="仅Excel文件", variable=self.output_mode_var, value="excel").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="两种都生成", variable=self.output_mode_var, value="both").pack(side=tk.LEFT)

        # 错误处理选项
        ttk.Label(self.upper_left, text="错误处理:").grid(row=7, column=0, padx=5, pady=5, sticky=tk.E)
        stop_frame = ttk.Frame(self.upper_left)
        stop_frame.grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(stop_frame, text="继续执行", variable=self.stop_on_error_var, value=False).pack(side=tk.LEFT)
        ttk.Radiobutton(stop_frame, text="立即停止", variable=self.stop_on_error_var, value=True).pack(side=tk.LEFT)

        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.upper_left, text="状态:").grid(row=8, column=0, padx=5, pady=5, sticky=tk.E)
        self.status_label = ttk.Label(self.upper_left, textvariable=self.status_var, foreground="blue")
        self.status_label.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W)

        # 控制按钮
        button_frame = ttk.Frame(self.upper_left)
        button_frame.grid(row=9, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)

        ttk.Button(button_frame, text="开始执行", command=self.start_telnet_thread).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="停止执行", command=self.stop_execution).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(button_frame, text="自动滚动", variable=self.is_auto_scroll).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除日志", command=self.log_manager.clear_log).pack(side=tk.LEFT, padx=5)

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
        """运行命令"""
        self.update_status("执行中")
        commands_file = self.commands_file_var.get()
        delay_ms = self.delay_ms_var.get()
        loop_count = self.loop_count_var.get()
        stop_on_error = self.stop_on_error_var.get()

        try:
            with open(commands_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            self.log_manager.write_log(f"打开命令文件失败: {e}")
            self.update_status("就绪(出错)")
            return

        for i in range(loop_count):
            if self.stop_event.is_set():
                self.log_manager.write_log("用户终止执行。")
                break

            loop_start = time.time()
            for cmd_line in lines:
                if self.stop_event.is_set():
                    break
                command_str = cmd_line.strip()
                if not command_str or command_str.startswith('#'):
                    self.log_manager.write_log(f"跳过命令: {command_str}")
                    continue
                success = self.execute_one_command(command_str, delay_ms)
                if not success and stop_on_error:
                    self.log_manager.write_log("遇到错误，停止执行。")
                    self.stop_event.set()
                    break

            loop_end = time.time()
            self.log_manager.write_log(f"本轮执行时间: {loop_end - loop_start:.2f} 秒")

        self.log_manager.write_log("所有循环已完成。")
        self.update_status("测试完成")
        self.chart_manager.update_chart(self.test_results)
        self.save_excel_if_needed()

    def execute_one_command(self, command_str, delay_ms):
        """执行单条命令"""
        try:
            output, elapsed = self.telnet_manager.execute_command(
                command_str,
                stop_event=self.stop_event,
                delay_ms=delay_ms
            )

            # 格式化输出
            lines = output.strip().splitlines()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for line in lines:
                if line.lower().startswith('cmd:'):
                    self.log_manager.write_log(line.replace('Cmd:', 'Cmd:'), "NORMAL")
                elif line.lower().startswith('data:'):
                    self.log_manager.write_log(line.replace('Data:', 'Data:'), "NORMAL")
                elif line.lower().startswith('result:'):
                    tag = "RESULT_PASS" if "pass" in line.lower() else "RESULT_FAIL"
                    self.log_manager.write_log(line.replace('Result:', 'Result:'), tag)
            
            self.log_manager.write_log(f"命令执行时间: {elapsed:.3f} 秒")

            # 解析输出用于统计和Excel
            data_val, result_val = self.parse_telnet_output(output)
            self.excel_data.append((command_str, data_val, result_val))
            if result_val.lower() == "pass":
                self.test_results.append("Pass")
                return True
            else:
                self.test_results.append("Fail")
                return False

        except Exception as e:
            self.log_manager.write_log(f"命令发送失败: {e}")
            return False

    def parse_telnet_output(self, output):
        """解析Telnet输出"""
        data_val = ""
        result_val = ""

        for line in output.splitlines():
            line = line.strip()
            if line.lower().startswith("data:"):
                data_val = line[len("data:"):].strip()
            elif line.lower().startswith("result:"):
                result_val = line[len("result:"):].strip()

        return data_val, result_val

    def save_excel_if_needed(self):
        """保存Excel文件（如果需要）"""
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

    def update_status(self, msg):
        """更新状态栏"""
        self.status_var.set(msg)

    def on_closing(self):
        """关闭窗口时的处理"""
        self.stop_event.set()
        if self.telnet_thread and self.telnet_thread.is_alive():
            self.telnet_thread.join(timeout=2)
        if self.telnet_manager:
            self.telnet_manager.close()
        self.destroy() 