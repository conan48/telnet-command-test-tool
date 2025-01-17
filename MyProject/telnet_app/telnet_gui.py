# telnet_app/telnet_gui.py

import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from datetime import datetime
from threading import Thread, Event
from queue import Queue

# matplotlib
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None

# 正确的相对导入
from .telnet_manager import TelnetManager
from .config_manager import import_config, export_config
from .advanced_editor import AdvancedEditor

class TelnetGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Telnet 指令测试工具 - 模块化改进")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # 创建样式
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", foreground="#333333", font=("Microsoft YaHei", 10))
        style.configure("TButton", font=("Microsoft YaHei", 10))
        style.configure("TEntry", font=("Microsoft YaHei", 10))

        # ========== 核心变量 ==========
        self.telnet_manager = None
        self.stop_event = Event()
        self.telnet_thread = None

        self.is_auto_scroll = tk.BooleanVar(value=True)

        self.test_results = []
        self.excel_data = []

        self.output_mode_var = tk.StringVar(value="do_not_generate")  # 默认改为不生成文件
        self.stop_on_error_var = tk.BooleanVar(value=False)          # 新增变量

        self.log_file_path = None
        self.excel_file_path = None

        # 日志队列与日志处理
        self.log_queue = Queue()

        # ========== 界面布局 ==========
        self.create_menus()
        self.create_widgets()

        # 启动一个定时器来刷新日志到文本框
        self.after(200, self._update_log_text)

    def create_menus(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="导入配置", command=self.import_config)
        config_menu.add_command(label="导出配置", command=self.export_config)
        menubar.add_cascade(label="配置", menu=config_menu)

        editor_menu = tk.Menu(menubar, tearoff=0)
        editor_menu.add_command(label="打开命令编辑器", command=self.open_advanced_editor)
        menubar.add_cascade(label="编辑器", menu=editor_menu)

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 上部
        self.upper_frame = ttk.Frame(main_frame)
        self.upper_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # 下部
        self.lower_frame = ttk.Frame(main_frame)
        self.lower_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ========== 上部控件 ==========
        ttk.Label(self.upper_frame, text="Telnet IP:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.host_var = tk.StringVar(value="192.168.0.21")
        ttk.Entry(self.upper_frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(self.upper_frame, text="Telnet 端口:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.port_var = tk.IntVar(value=81)
        ttk.Entry(self.upper_frame, textvariable=self.port_var, width=15).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        connect_btn = ttk.Button(self.upper_frame, text="连接", command=self.connect_telnet)
        connect_btn.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

        ttk.Label(self.upper_frame, text="循环次数:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.loop_count_var = tk.IntVar(value=1)
        ttk.Entry(self.upper_frame, textvariable=self.loop_count_var, width=15).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(self.upper_frame, text="命令文件:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.commands_file_var = tk.StringVar(value="commands.txt")
        ttk.Entry(self.upper_frame, textvariable=self.commands_file_var, width=40).grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(self.upper_frame, text="选择文件", command=self.select_commands_file).grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)

        ttk.Label(self.upper_frame, text="日志目录:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.E)
        self.log_dir_var = tk.StringVar(value="telnet_logs")
        ttk.Entry(self.upper_frame, textvariable=self.log_dir_var, width=40).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(self.upper_frame, text="选择目录", command=self.select_log_dir).grid(row=4, column=2, padx=5, pady=5, sticky=tk.W)

        ttk.Label(self.upper_frame, text="命令执行延时(ms):").grid(row=5, column=0, padx=5, pady=5, sticky=tk.E)
        self.delay_ms_var = tk.IntVar(value=0)
        ttk.Entry(self.upper_frame, textvariable=self.delay_ms_var, width=15).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)

        # 输出模式
        ttk.Label(self.upper_frame, text="输出模式:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.E)
        mode_frame = ttk.Frame(self.upper_frame)
        mode_frame.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="不生成文件", variable=self.output_mode_var, value="do_not_generate").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="仅Log文件", variable=self.output_mode_var, value="log").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="仅Excel", variable=self.output_mode_var, value="excel").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="两者都输出", variable=self.output_mode_var, value="both").pack(side=tk.LEFT)

        # 新增自动停止选项
        ttk.Label(self.upper_frame, text="遇到错误:").grid(row=7, column=0, padx=5, pady=5, sticky=tk.E)
        stop_frame = ttk.Frame(self.upper_frame)
        stop_frame.grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(stop_frame, text="继续执行", variable=self.stop_on_error_var, value=False).pack(side=tk.LEFT)
        ttk.Radiobutton(stop_frame, text="立即停止", variable=self.stop_on_error_var, value=True).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.upper_frame, text="状态:").grid(row=8, column=0, padx=5, pady=5, sticky=tk.E)
        self.status_label = ttk.Label(self.upper_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W)

        button_frame = ttk.Frame(self.upper_frame)
        button_frame.grid(row=9, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)

        ttk.Button(button_frame, text="开始执行", command=self.start_telnet_thread).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="停止执行", command=self.stop_execution).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(button_frame, text="自动滚动", variable=self.is_auto_scroll).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)

        # ========== 下部：日志 + 图表 ==========
        self.lower_left = ttk.Frame(self.lower_frame)
        self.lower_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.lower_right = ttk.Frame(self.lower_frame)
        self.lower_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(self.lower_left, wrap=tk.WORD, width=60, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config("RESULT_PASS", foreground="green")
        self.log_text.tag_config("RESULT_FAIL", foreground="red")
        self.log_text.tag_config("NORMAL", foreground="black")

        # 图表
        self.fig = Figure(figsize=(4, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("测试结果统计")
        self.ax.set_xlabel("结果类型")
        self.ax.set_ylabel("次数")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.lower_right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ===============================
    # Telnet 连接
    # ===============================
    def connect_telnet(self):
        host = self.host_var.get()
        port = self.port_var.get()
        self.telnet_manager = TelnetManager(host, port)

        try:
            self.telnet_manager.connect()
            self.write_log(f"已连接到 {host}:{port}")
            self.update_status("Telnet连接成功")
        except Exception as e:
            self.write_log(f"连接失败: {e}")
            self.update_status("连接失败")
            self.telnet_manager = None

    # ===============================
    # 文件/目录选择
    # ===============================
    def select_commands_file(self):
        file_path = filedialog.askopenfilename(
            title="选择命令文件",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.commands_file_var.set(file_path)

    def select_log_dir(self):
        directory = filedialog.askdirectory(title="选择日志存放目录")
        if directory:
            self.log_dir_var.set(directory)

    # ===============================
    # 日志逻辑（线程安全）
    # ===============================
    def write_log(self, message):
        """
        将消息放入队列，由主线程来更新 UI。
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.log_queue.put(line)

    def _update_log_text(self):
        """
        定时从队列获取日志消息并写到文本框
        """
        while not self.log_queue.empty():
            line_to_insert = self.log_queue.get()
            use_tag = "NORMAL"
            if "result:" in line_to_insert.lower():
                if "pass" in line_to_insert.lower():
                    use_tag = "RESULT_PASS"
                elif "fail" in line_to_insert.lower():
                    use_tag = "RESULT_FAIL"

            self.log_text.insert(tk.END, line_to_insert + "\n", use_tag)
            if self.is_auto_scroll.get():
                self.log_text.see(tk.END)

            # 写入文件（如果需要）
            mode = self.output_mode_var.get()
            if mode in ("log", "both") and self.log_file_path:
                try:
                    with open(self.log_file_path, "a", encoding="utf-8") as f:
                        f.write(line_to_insert + "\n")
                except Exception as e:
                    self.write_log(f"写入日志文件失败：{e}")

        self.after(200, self._update_log_text)  # 继续轮询

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)

    # ===============================
    # 启动 / 停止命令执行
    # ===============================
    def start_telnet_thread(self):
        if self.telnet_thread and self.telnet_thread.is_alive():
            messagebox.showwarning("提示", "Telnet 命令正在执行，请先停止或等待结束。")
            return

        if not self.telnet_manager or not self.telnet_manager.is_connected:
            messagebox.showinfo("提示", "请先点击“连接”按钮进行Telnet连接。")
            return

        # 重置
        self.stop_event.clear()
        self.test_results.clear()
        self.excel_data.clear()

        # 仅当 mode != do_not_generate 时，才生成文件
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

        self.telnet_thread = Thread(target=self.run_commands)
        self.telnet_thread.daemon = True
        self.telnet_thread.start()

    def stop_execution(self):
        self.stop_event.set()

    def run_commands(self):
        self.update_status("执行中")
        commands_file = self.commands_file_var.get()
        delay_ms = self.delay_ms_var.get()
        loop_count = self.loop_count_var.get()
        stop_on_error = self.stop_on_error_var.get()  # 获取新的选项

        try:
            with open(commands_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            self.write_log(f"打开命令文件时出错: {e}")
            self.update_status("就绪(出错)")
            return

        for i in range(loop_count):
            if self.stop_event.is_set():
                self.write_log("用户终止执行。")
                break

            loop_start = time.time()
            self.write_log(f"===== 第 {i+1} 次循环 =====")

            for cmd_line in lines:
                if self.stop_event.is_set():
                    break
                command_str = cmd_line.strip()
                if not command_str or command_str.startswith('#'):
                    self.write_log(f"跳过命令: {command_str}")
                    continue
                success = self.execute_one_command(command_str, delay_ms)
                if not success and stop_on_error:
                    self.write_log("遇到错误，停止执行。")
                    self.stop_event.set()
                    break

            loop_end = time.time()
            self.write_log(f"本次循环执行时间: {loop_end - loop_start:.2f} 秒")

        self.write_log("完成所有循环。")
        self.update_status("测试完成")
        self.update_chart()
        self.save_excel_if_needed()

    def execute_one_command(self, command_str, delay_ms):
        """
        执行单个命令。
        - 如果是 DELAY 指令，则进行延时。
        - 否则，通过 Telnet 发送命令并处理返回结果。
        """
        self.write_log(f"cmd: {command_str}")

        # 先检查是否为 DELAY 指令
        if self.is_delay_command(command_str):
            delay_time = self.parse_delay_command(command_str)
            if delay_time is not None:
                self.write_log(f"执行延时指令，等待 {delay_time} 毫秒")
                try:
                    time.sleep(delay_time / 1000.0)
                    return True  # 延时成功，继续执行
                except Exception as e:
                    self.write_log(f"延时失败：{e}")
                    return False
            else:
                self.write_log("延时指令解析失败，继续执行其他命令")
                return False

        # 如果不是 DELAY 指令，则通过 Telnet 发送命令
        try:
            output, elapsed = self.telnet_manager.execute_command(
                command_str,
                stop_event=self.stop_event,
                delay_ms=delay_ms
            )
        except Exception as e:
            self.write_log(f"发送命令失败：{e}")
            return False  # 表示执行失败

        # 解析结果
        data_val, result_val = self.parse_telnet_output(output)
        self.write_log(f"data: {data_val}")
        self.write_log(f"result: {result_val}")
        self.write_log(f"命令执行时间: {elapsed:.3f} 秒")

        self.excel_data.append((command_str, data_val, result_val))
        if result_val.lower() == "pass":
            self.test_results.append("Pass")
            return True
        else:
            self.test_results.append("Fail")
            return False

    def parse_telnet_output(self, output):
        """
        解析 Telnet 命令的输出，提取 data_val 和 result_val
        假设输出包含 'data: <value>' 和 'result: <value>' 这样的行
        """
        data_val = ""
        result_val = ""

        for line in output.splitlines():
            line = line.strip()
            if line.lower().startswith("data:"):
                data_val = line[len("data:"):].strip()
            elif line.lower().startswith("result:"):
                result_val = line[len("result:"):].strip()

        return data_val, result_val

    def is_delay_command(self, command_str):
        """
        判断是否是自定义的延时指令
        这里假设延时指令以 "DELAY" 开头，你可以根据需要自定义
        """
        return command_str.upper().startswith("DELAY")

    def parse_delay_command(self, command_str):
        """
        解析延时指令，返回延时时间（毫秒）
        假设格式为: DELAY 1000
        """
        parts = command_str.split()
        if len(parts) != 2:
            return None
        try:
            delay_time = int(parts[1])
            return delay_time
        except ValueError:
            return None

    # ===============================
    # 图表更新
    # ===============================
    def update_chart(self):
        pass_count = self.test_results.count("Pass")
        fail_count = self.test_results.count("Fail")

        self.ax.clear()
        self.ax.set_title("测试结果统计")
        self.ax.set_xlabel("结果类型")
        self.ax.set_ylabel("次数")

        results = ["Pass", "Fail"]
        counts = [pass_count, fail_count]
        bar_positions = range(len(results))

        self.ax.bar(bar_positions, counts, color=["green", "red"], tick_label=results)
        self.ax.set_ylim(0, max(1, max(counts, default=0)))
        self.canvas.draw()

    # ===============================
    # 状态更新
    # ===============================
    def update_status(self, msg):
        self.status_var.set(msg)

    # ===============================
    # 配置导入/导出
    # ===============================
    def import_config(self):
        config_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not config_path:
            return

        try:
            data = import_config(config_path)
            self.host_var.set(data.get("host", "192.168.0.21"))
            self.port_var.set(data.get("port", 81))
            self.loop_count_var.set(data.get("loop_count", 1))
            self.commands_file_var.set(data.get("commands_file", "commands.txt"))
            self.log_dir_var.set(data.get("log_dir", "telnet_logs"))
            self.delay_ms_var.set(data.get("delay_ms", 0))
            self.output_mode_var.set(data.get("output_mode", "do_not_generate"))
            self.stop_on_error_var.set(data.get("stop_on_error", False))
            messagebox.showinfo("提示", "配置导入成功！")
        except Exception as e:
            messagebox.showerror("错误", f"导入配置失败：{e}")

    def export_config(self):
        config_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            defaultextension=".json"
        )
        if not config_path:
            return

        data = {
            "host": self.host_var.get(),
            "port": self.port_var.get(),
            "loop_count": self.loop_count_var.get(),
            "commands_file": self.commands_file_var.get(),
            "log_dir": self.log_dir_var.get(),
            "delay_ms": self.delay_ms_var.get(),
            "output_mode": self.output_mode_var.get(),
            "stop_on_error": self.stop_on_error_var.get(),  # 新增选项
        }
        try:
            export_config(config_path, data)
            messagebox.showinfo("提示", "配置已导出！")
        except Exception as e:
            messagebox.showerror("错误", f"导出配置失败：{e}")

    # ===============================
    # 高级命令编辑器
    # ===============================
    def open_advanced_editor(self):
        """
        打开高级编辑器，并实现：
        1. 一进编辑器就加载主界面里选择的 commands_file
        2. 点击发送时，调用我们在这里定义的回调函数 editor_send_callback
        """
        from threading import Thread

        # 拿到主界面设置的命令文件路径
        commands_file = self.commands_file_var.get()

        def editor_send_callback(mode, content, text_widget):
            """
            当编辑器点击“发送”按钮时的回调:
            - mode: "selected_or_cursor" (发送所选/当前行) 或 "single_line_flow" (逐行发送)
            - content: 要发送的命令文本，可多行，也可单行
            - text_widget: 编辑器本身的 tk.Text，以防后续需要用到
            """

            # 封装一个函数，在线程里执行这些命令
            def run_commands_from_editor(lines_to_send):
                # 清空之前的测试结果、Excel 数据等
                self.stop_event.clear()
                self.test_results.clear()
                self.excel_data.clear()

                self.write_log("===== 开始执行编辑器中的命令 =====")
                for line in lines_to_send:
                    if self.stop_event.is_set():
                        self.write_log("用户中止执行。")
                        break

                    cmd_str = line.strip()
                    if not cmd_str:
                        continue

                    # 这里调用 GUI 内部的 execute_one_command
                    # delay_ms 可以根据主界面的设置来传
                    success = self.execute_one_command(cmd_str, self.delay_ms_var.get())
                    if not success and self.stop_on_error_var.get():
                        self.write_log("遇到错误，停止执行。")
                        self.stop_event.set()
                        break

                self.write_log("===== 编辑器命令执行结束 =====")
                # 更新图表 / 保存Excel
                self.update_chart()
                self.save_excel_if_needed()

            # 根据 mode 不同来决定要发送哪些行
            if mode == "selected_or_cursor":
                # 可能是多行，也可能是单行
                lines = content.splitlines()
                lines = [ln for ln in lines if ln.strip()]  # 过滤空行
                if not lines:
                    self.write_log("没有可发送的命令")
                    return

                # 启动线程执行
                self.telnet_thread = Thread(target=run_commands_from_editor, args=(lines,))
                self.telnet_thread.daemon = True
                self.telnet_thread.start()

            elif mode == "single_line_flow":
                # “逐行发送”时只拿这一行
                line_to_send = content.strip()
                if not line_to_send:
                    return

                # 启动线程执行
                self.telnet_thread = Thread(target=run_commands_from_editor, args=([line_to_send],))
                self.telnet_thread.daemon = True
                self.telnet_thread.start()
            else:
                self.write_log(f"未知的发送模式: {mode}")

        # 打开高级编辑器，并把 commands_file 作为 initial_file 传进去
        AdvancedEditor(
            self,
            send_callback=editor_send_callback,
            initial_file=commands_file
        )

    # ===============================
    # 关闭主窗口
    # ===============================
    def on_closing(self):
        self.stop_event.set()
        if self.telnet_thread and self.telnet_thread.is_alive():
            self.telnet_thread.join(timeout=2)
        if self.telnet_manager:
            self.telnet_manager.close()
        self.destroy()

    # ===============================
    # 自定义延时指令相关函数
    # ===============================
    def is_delay_command(self, command_str):
        """
        判断是否是自定义的延时指令
        这里假设延时指令以 "DELAY" 开头，你可以根据需要自定义
        """
        return command_str.upper().startswith("DELAY")

    def parse_delay_command(self, command_str):
        """
        解析延时指令，返回延时时间（毫秒）
        假设格式为: DELAY 1000
        """
        parts = command_str.split()
        if len(parts) != 2:
            return None
        try:
            delay_time = int(parts[1])
            return delay_time
        except ValueError:
            return None

    # ===============================
    # 图表更新
    # ===============================
    def update_chart(self):
        pass_count = self.test_results.count("Pass")
        fail_count = self.test_results.count("Fail")

        self.ax.clear()
        self.ax.set_title("测试结果统计")
        self.ax.set_xlabel("结果类型")
        self.ax.set_ylabel("次数")

        results = ["Pass", "Fail"]
        counts = [pass_count, fail_count]
        bar_positions = range(len(results))

        self.ax.bar(bar_positions, counts, color=["green", "red"], tick_label=results)
        self.ax.set_ylim(0, max(1, max(counts, default=0)))
        self.canvas.draw()

    # ===============================
    # 状态更新
    # ===============================
    def update_status(self, msg):
        self.status_var.set(msg)

    # ===============================
    # 配置导入/导出
    # ===============================
    def import_config(self):
        config_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not config_path:
            return

        try:
            data = import_config(config_path)
            self.host_var.set(data.get("host", "192.168.0.21"))
            self.port_var.set(data.get("port", 81))
            self.loop_count_var.set(data.get("loop_count", 1))
            self.commands_file_var.set(data.get("commands_file", "commands.txt"))
            self.log_dir_var.set(data.get("log_dir", "telnet_logs"))
            self.delay_ms_var.set(data.get("delay_ms", 0))
            self.output_mode_var.set(data.get("output_mode", "do_not_generate"))
            self.stop_on_error_var.set(data.get("stop_on_error", False))
            messagebox.showinfo("提示", "配置导入成功！")
        except Exception as e:
            messagebox.showerror("错误", f"导入配置失败：{e}")

    def export_config(self):
        config_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            defaultextension=".json"
        )
        if not config_path:
            return

        data = {
            "host": self.host_var.get(),
            "port": self.port_var.get(),
            "loop_count": self.loop_count_var.get(),
            "commands_file": self.commands_file_var.get(),
            "log_dir": self.log_dir_var.get(),
            "delay_ms": self.delay_ms_var.get(),
            "output_mode": self.output_mode_var.get(),
            "stop_on_error": self.stop_on_error_var.get(),  # 新增选项
        }
        try:
            export_config(config_path, data)
            messagebox.showinfo("提示", "配置已导出！")
        except Exception as e:
            messagebox.showerror("错误", f"导出配置失败：{e}")

    # ===============================
    # 保存 Excel（如果需要）
    # ===============================
    def save_excel_if_needed(self):
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
                    self.write_log(f"Excel 文件已保存到 {self.excel_file_path}")
                except Exception as e:
                    self.write_log(f"保存 Excel 文件失败：{e}")
            else:
                self.write_log("openpyxl 模块未安装，无法保存 Excel 文件。")

    # ===============================
    # 高级命令编辑器
    # ===============================
    def open_advanced_editor(self):
        """
        打开高级编辑器，并实现：
        1. 一进编辑器就加载主界面里选择的 commands_file
        2. 点击发送时，调用我们在这里定义的回调函数 editor_send_callback
        """
        from threading import Thread

        # 拿到主界面设置的命令文件路径
        commands_file = self.commands_file_var.get()

        def editor_send_callback(mode, content, text_widget):
            """
            当编辑器点击“发送”按钮时的回调:
            - mode: "selected_or_cursor" (发送所选/当前行) 或 "single_line_flow" (逐行发送)
            - content: 要发送的命令文本，可多行，也可单行
            - text_widget: 编辑器本身的 tk.Text，以防后续需要用到
            """

            # 封装一个函数，在线程里执行这些命令
            def run_commands_from_editor(lines_to_send):
                # 清空之前的测试结果、Excel 数据等
                self.stop_event.clear()
                self.test_results.clear()
                self.excel_data.clear()

                self.write_log("===== 开始执行编辑器中的命令 =====")
                for line in lines_to_send:
                    if self.stop_event.is_set():
                        self.write_log("用户中止执行。")
                        break

                    cmd_str = line.strip()
                    if not cmd_str:
                        continue

                    # 这里调用 GUI 内部的 execute_one_command
                    # delay_ms 可以根据主界面的设置来传
                    success = self.execute_one_command(cmd_str, self.delay_ms_var.get())
                    if not success and self.stop_on_error_var.get():
                        self.write_log("遇到错误，停止执行。")
                        self.stop_event.set()
                        break

                self.write_log("===== 编辑器命令执行结束 =====")
                # 更新图表 / 保存Excel
                self.update_chart()
                self.save_excel_if_needed()

            # 根据 mode 不同来决定要发送哪些行
            if mode == "selected_or_cursor":
                # 可能是多行，也可能是单行
                lines = content.splitlines()
                lines = [ln for ln in lines if ln.strip()]  # 过滤空行
                if not lines:
                    self.write_log("没有可发送的命令")
                    return

                # 启动线程执行
                self.telnet_thread = Thread(target=run_commands_from_editor, args=(lines,))
                self.telnet_thread.daemon = True
                self.telnet_thread.start()

            elif mode == "single_line_flow":
                # “逐行发送”时只拿这一行
                line_to_send = content.strip()
                if not line_to_send:
                    return

                # 启动线程执行
                self.telnet_thread = Thread(target=run_commands_from_editor, args=([line_to_send],))
                self.telnet_thread.daemon = True
                self.telnet_thread.start()
            else:
                self.write_log(f"未知的发送模式: {mode}")

        # 打开高级编辑器，并把 commands_file 作为 initial_file 传进去
        AdvancedEditor(
            self,
            send_callback=editor_send_callback,
            initial_file=commands_file
        )

    # ===============================
    # 自定义延时指令相关函数
    # ===============================
    def is_delay_command(self, command_str):
        """
        判断是否是自定义的延时指令
        这里假设延时指令以 "DELAY" 开头，你可以根据需要自定义
        """
        return command_str.upper().startswith("DELAY")

    def parse_delay_command(self, command_str):
        """
        解析延时指令，返回延时时间（毫秒）
        假设格式为: DELAY 1000
        """
        parts = command_str.split()
        if len(parts) != 2:
            return None
        try:
            delay_time = int(parts[1])
            return delay_time
        except ValueError:
            return None

    # ===============================
    # 图表更新
    # ===============================
    def update_chart(self):
        pass_count = self.test_results.count("Pass")
        fail_count = self.test_results.count("Fail")

        self.ax.clear()
        self.ax.set_title("测试结果统计")
        self.ax.set_xlabel("结果类型")
        self.ax.set_ylabel("次数")

        results = ["Pass", "Fail"]
        counts = [pass_count, fail_count]
        bar_positions = range(len(results))

        self.ax.bar(bar_positions, counts, color=["green", "red"], tick_label=results)
        self.ax.set_ylim(0, max(1, max(counts, default=0)))
        self.canvas.draw()

    # ===============================
    # 状态更新
    # ===============================
    def update_status(self, msg):
        self.status_var.set(msg)

    # ===============================
    # 配置导入/导出
    # ===============================
    def import_config(self):
        config_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not config_path:
            return

        try:
            data = import_config(config_path)
            self.host_var.set(data.get("host", "192.168.0.21"))
            self.port_var.set(data.get("port", 81))
            self.loop_count_var.set(data.get("loop_count", 1))
            self.commands_file_var.set(data.get("commands_file", "commands.txt"))
            self.log_dir_var.set(data.get("log_dir", "telnet_logs"))
            self.delay_ms_var.set(data.get("delay_ms", 0))
            self.output_mode_var.set(data.get("output_mode", "do_not_generate"))
            self.stop_on_error_var.set(data.get("stop_on_error", False))
            messagebox.showinfo("提示", "配置导入成功！")
        except Exception as e:
            messagebox.showerror("错误", f"导入配置失败：{e}")

    def export_config(self):
        config_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            defaultextension=".json"
        )
        if not config_path:
            return

        data = {
            "host": self.host_var.get(),
            "port": self.port_var.get(),
            "loop_count": self.loop_count_var.get(),
            "commands_file": self.commands_file_var.get(),
            "log_dir": self.log_dir_var.get(),
            "delay_ms": self.delay_ms_var.get(),
            "output_mode": self.output_mode_var.get(),
            "stop_on_error": self.stop_on_error_var.get(),  # 新增选项
        }
        try:
            export_config(config_path, data)
            messagebox.showinfo("提示", "配置已导出！")
        except Exception as e:
            messagebox.showerror("错误", f"导出配置失败：{e}")

    # ===============================
    # 保存 Excel（如果需要）
    # ===============================
    def save_excel_if_needed(self):
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
                    self.write_log(f"Excel 文件已保存到 {self.excel_file_path}")
                except Exception as e:
                    self.write_log(f"保存 Excel 文件失败：{e}")
            else:
                self.write_log("openpyxl 模块未安装，无法保存 Excel 文件。")

    # ===============================
    # 关闭主窗口
    # ===============================
    def on_closing(self):
        self.stop_event.set()
        if self.telnet_thread and self.telnet_thread.is_alive():
            self.telnet_thread.join(timeout=2)
        if self.telnet_manager:
            self.telnet_manager.close()
        self.destroy()

    # ===============================
    # 高级命令编辑器
    # ===============================
    def open_advanced_editor(self):
        """
        打开高级编辑器，并实现：
        1. 一进编辑器就加载主界面里选择的 commands_file
        2. 点击发送时，调用我们在这里定义的回调函数 editor_send_callback
        """
        from threading import Thread

        # 拿到主界面设置的命令文件路径
        commands_file = self.commands_file_var.get()

        def editor_send_callback(mode, content, text_widget):
            """
            当编辑器点击“发送”按钮时的回调:
            - mode: "selected_or_cursor" (发送所选/当前行) 或 "single_line_flow" (逐行发送)
            - content: 要发送的命令文本，可多行，也可单行
            - text_widget: 编辑器本身的 tk.Text，以防后续需要用到
            """

            # 封装一个函数，在线程里执行这些命令
            def run_commands_from_editor(lines_to_send):
                # 清空之前的测试结果、Excel 数据等
                self.stop_event.clear()
                self.test_results.clear()
                self.excel_data.clear()

                self.write_log("===== 开始执行编辑器中的命令 =====")
                for line in lines_to_send:
                    if self.stop_event.is_set():
                        self.write_log("用户中止执行。")
                        break

                    cmd_str = line.strip()
                    if not cmd_str:
                        continue

                    # 这里调用 GUI 内部的 execute_one_command
                    # delay_ms 可以根据主界面的设置来传
                    success = self.execute_one_command(cmd_str, self.delay_ms_var.get())
                    if not success and self.stop_on_error_var.get():
                        self.write_log("遇到错误，停止执行。")
                        self.stop_event.set()
                        break

                self.write_log("===== 编辑器命令执行结束 =====")
                # 更新图表 / 保存Excel
                self.update_chart()
                self.save_excel_if_needed()

            # 根据 mode 不同来决定要发送哪些行
            if mode == "selected_or_cursor":
                # 可能是多行，也可能是单行
                lines = content.splitlines()
                lines = [ln for ln in lines if ln.strip()]  # 过滤空行
                if not lines:
                    self.write_log("没有可发送的命令")
                    return

                # 启动线程执行
                self.telnet_thread = Thread(target=run_commands_from_editor, args=(lines,))
                self.telnet_thread.daemon = True
                self.telnet_thread.start()

            elif mode == "single_line_flow":
                # “逐行发送”时只拿这一行
                line_to_send = content.strip()
                if not line_to_send:
                    return

                # 启动线程执行
                self.telnet_thread = Thread(target=run_commands_from_editor, args=([line_to_send],))
                self.telnet_thread.daemon = True
                self.telnet_thread.start()
            else:
                self.write_log(f"未知的发送模式: {mode}")

        # 打开高级编辑器，并把 commands_file 作为 initial_file 传进去
        AdvancedEditor(
            self,
            send_callback=editor_send_callback,
            initial_file=commands_file
        )
