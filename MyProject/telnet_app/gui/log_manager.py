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
        self.log_frame = tk.Frame(parent.lower_left, bg='#f0f0f0')
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建日志文本控件
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap=tk.WORD,
            width=60,
            height=20,
            font=('Consolas', 10),
            bg='#ffffff',
            fg='#2c3e50',
            insertbackground='#2c3e50',
            selectbackground='#bdc3c7',
            selectforeground='#2c3e50',
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置标签样式
        self.log_text.tag_config("RESULT_PASS", foreground="#ffffff", background="#27ae60")
        self.log_text.tag_config("RESULT_FAIL", foreground="#ffffff", background="#e74c3c")
        self.log_text.tag_config("NORMAL", foreground="#2c3e50")
        self.log_text.tag_config("CMD", foreground="#2980b9")
        self.log_text.tag_config("DATA", foreground="#8e44ad")
        
        # 自定义滚动条样式
        style = ttk.Style()
        style.configure("Custom.Vertical.TScrollbar",
                      background="#bdc3c7",
                      troughcolor="#f0f0f0",
                      width=10,
                      relief=tk.FLAT)
        
        # 替换默认滚动条
        self.scrollbar = ttk.Scrollbar(
            self.log_text,
            orient=tk.VERTICAL,
            style="Custom.Vertical.TScrollbar",
            command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 启动日志更新定时器
        parent.after(200, self._update_log_text)

    def write_log(self, message, tag="NORMAL"):
        """将消息放入队列，由主线程更新UI"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if message.lower().startswith('cmd:'):
            line = f"[{timestamp}] {message}"
            tag = "CMD"
        elif message.lower().startswith('data:'):
            line = f"                      {message}"
            tag = "DATA"
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
            if self.parent.is_auto_scroll.get():
                self.log_text.see(tk.END)

            # 如果需要则写入文件
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