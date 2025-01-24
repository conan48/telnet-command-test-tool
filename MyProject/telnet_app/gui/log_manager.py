# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime
from queue import Queue

class LogManager:
    def __init__(self, parent):
        self.parent = parent
        self.log_queue = Queue()
        
        # 创建日志文本控件容器框架
        self.log_frame = ttk.Frame(parent.lower_left)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建日志文本控件
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap=tk.WORD,
            width=60,
            height=20,
            font=('Consolas', 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置标签样式
        self.log_text.tag_config("RESULT_PASS", foreground="green")
        self.log_text.tag_config("RESULT_FAIL", foreground="red")
        self.log_text.tag_config("NORMAL", foreground="black")
        
        # 启动日志更新定时器
        parent.after(200, self._update_log_text)

    def write_log(self, message, tag="NORMAL"):
        """将消息放入队列，由主线程更新UI"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if message.lower().startswith('cmd:'):
            line = f"[{timestamp}] {message}"
        elif message.lower().startswith('data:'):
            line = f"                      {message}"
        elif message.lower().startswith('result:'):
            line = f"                      {message}"
        else:
            line = f"[{timestamp}] {message}"
        self.log_queue.put((line, tag))

    def _update_log_text(self):
        """定期从队列获取日志消息并写入文本控件"""
        while not self.log_queue.empty():
            line_to_insert, tag = self.log_queue.get()
            
            self.log_text.insert(tk.END, line_to_insert + "\n", tag)
            if hasattr(self.parent, 'is_auto_scroll') and self.parent.is_auto_scroll.get():
                self.log_text.see(tk.END)

            # 如果需要则写入文件
            if hasattr(self.parent, 'output_mode_var') and hasattr(self.parent, 'log_file_path'):
                mode = self.parent.output_mode_var.get()
                if mode in ("log", "both") and self.parent.log_file_path:
                    try:
                        with open(self.parent.log_file_path, "a", encoding="utf-8") as f:
                            f.write(line_to_insert + "\n")
                    except Exception as e:
                        self.write_log(f"写入日志文件失败：{e}")

        self.parent.after(200, self._update_log_text)

    def clear_log(self):
        """清除日志文本控件"""
        self.log_text.delete("1.0", tk.END) 