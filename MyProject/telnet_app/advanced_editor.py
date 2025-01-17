# advanced_editor.py

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class AdvancedEditor(tk.Toplevel):
    """
    改进后的高级命令编辑器
    解决：
    1. 行号与文本同步滚动
    2. 逐行发送根据当前光标行，并高亮
    """
    def __init__(self, master, send_callback=None, initial_file=None):
        super().__init__(master)
        self.title("高级命令编辑器 - 改进版")
        self.geometry("800x600")

        self.send_callback = send_callback
        self.current_file_path = initial_file  # 打开/保存都指向这个文件
        # 用于高亮当前行
        self.highlight_tag = "highlighted_line"

        # ---- 主容器 ----
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)

        # ---- 行号文本框 ----
        self.line_numbers = tk.Text(
            self.container,
            width=4,
            padx=4,
            takefocus=0,
            border=0,
            background="#f0f0f0",
            state='disabled'
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # ---- 编辑器文本框 ----
        self.text_editor = tk.Text(self.container, wrap=tk.NONE, undo=True)
        self.text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ---- 滚动条 ----
        self.scrollbar = ttk.Scrollbar(self.container, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 配置让 text_editor 和行号都使用同一个滚动条
        self.text_editor.config(yscrollcommand=self._on_text_editor_scroll)
        # 让滚动条反过来控制 text_editor 和行号
        self.scrollbar.config(command=self._on_scrollbar_scroll)

        # ---- 事件绑定 ----
        self.text_editor.bind("<KeyPress>", self._on_text_changed)
        self.text_editor.bind("<Button-1>", self._on_text_changed)
        self.text_editor.bind("<MouseWheel>", self._on_text_changed)
        self.text_editor.bind("<Shift-MouseWheel>", self._on_text_changed)  # 支持Shift+滚轮
        self.text_editor.bind("<Control-MouseWheel>", self._on_text_changed)  # 支持Ctrl+滚轮

        # ---- 高亮标签定义 ----
        self.text_editor.tag_config(
            self.highlight_tag, 
            background="#FFFF00",  # 黄色高亮
            foreground="black"      # 文字颜色
        )

        # ---- 底部按钮 ----
        button_bar = ttk.Frame(self)
        button_bar.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(button_bar, text="打开(刷新)", command=self.load_from_current_file).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_bar, text="保存", command=self.save_to_current_file).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_bar, text="另存为", command=self.editor_save_as_file).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_bar, text="查找/替换", command=self.find_replace_dialog).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(button_bar, text="发送所选", 
                   command=lambda: self._send_commands("selected_or_cursor")).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_bar, text="逐行发送",
                   command=self._send_next_line).pack(side=tk.LEFT, padx=5, pady=5)

        # ---- 如果进来时带了 initial_file，就自动加载它 ----
        if self.current_file_path and os.path.isfile(self.current_file_path):
            self.load_file(self.current_file_path)

        # ---- 关闭窗口事件 ----
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # =============================
    #    行号与滚动同步
    # =============================
    def _on_text_editor_scroll(self, *args):
        """
        当 text_editor 滚动时，更新滚动条位置，并同步行号文本框的 yview
        """
        # 先更新滚动条位置
        self.scrollbar.set(*args)
        # 再让 text_editor 跟随滚动
        self.text_editor.yview_moveto(args[0])
        # 同步行号
        self.line_numbers.yview_moveto(args[0])

    def _on_scrollbar_scroll(self, *args):
        """
        当滚动条被拖动时，调用该方法，使 text_editor 和 line_numbers 一起滚动
        """
        self.text_editor.yview(*args)
        self.line_numbers.yview(*args)

    # =============================
    #    页面内容变动 & 行号更新
    # =============================
    def _on_text_changed(self, event=None):
        """
        页面内容或大小变动，更新行号
        """
        self._update_line_numbers()

    def _update_line_numbers(self):
        """
        重新生成行号文本
        """
        if not self.line_numbers.winfo_exists():
            return
        if not self.text_editor.winfo_exists():
            return

        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)

        row_count = int(self.text_editor.index('end').split('.')[0])
        for i in range(1, row_count):
            self.line_numbers.insert(tk.END, f"{i}\n")

        self.line_numbers.config(state='disabled')

    # =============================
    #     文件读写相关函数
    # =============================
    def load_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text_editor.delete('1.0', tk.END)
            self.text_editor.insert('1.0', content)
            self._update_line_numbers()
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败：{e}")

    def load_from_current_file(self):
        """从 current_file_path 读取"""
        if not self.current_file_path:
            messagebox.showwarning("提示", "尚未关联任何文件路径，请先在主界面选择命令文件或‘另存为’。")
            return
        if not os.path.isfile(self.current_file_path):
            messagebox.showwarning("提示", f"文件 {self.current_file_path} 不存在。")
            return
        self.load_file(self.current_file_path)

    def save_to_current_file(self):
        """保存到 current_file_path"""
        if not self.current_file_path:
            messagebox.showwarning("提示", "尚未关联任何文件路径，请先使用‘另存为’。")
            return
        content = self.text_editor.get('1.0', tk.END)
        try:
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("提示", f"已保存到 {self.current_file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")

    def editor_save_as_file(self):
        """使用对话框另存为，然后更新 current_file_path"""
        new_path = filedialog.asksaveasfilename(title="另存为", defaultextension=".txt")
        if not new_path:
            return
        content = self.text_editor.get('1.0', tk.END)
        try:
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.current_file_path = new_path
            messagebox.showinfo("提示", f"已另存为 {new_path}")
        except Exception as e:
            messagebox.showerror("错误", f"另存为失败：{e}")

    # =============================
    #     查找 / 替换
    # =============================
    def find_replace_dialog(self):
        fr_win = tk.Toplevel(self)
        fr_win.title("查找/替换")
        fr_win.geometry("300x100")

        ttk.Label(fr_win, text="查找：").grid(row=0, column=0, padx=5, pady=5)
        find_var = tk.StringVar()
        find_entry = ttk.Entry(fr_win, textvariable=find_var, width=20)
        find_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(fr_win, text="替换：").grid(row=1, column=0, padx=5, pady=5)
        replace_var = tk.StringVar()
        replace_entry = ttk.Entry(fr_win, textvariable=replace_var, width=20)
        replace_entry.grid(row=1, column=1, padx=5, pady=5)

        def do_find():
            target = find_var.get()
            self.text_editor.tag_remove('found', '1.0', tk.END)
            if target:
                idx = '1.0'
                while True:
                    idx = self.text_editor.search(target, idx, nocase=1, stopindex=tk.END)
                    if not idx:
                        break
                    endidx = f"{idx}+{len(target)}c"
                    self.text_editor.tag_add('found', idx, endidx)
                    idx = endidx
                self.text_editor.tag_config('found', background='yellow')

        def do_replace():
            target = find_var.get()
            replacement = replace_var.get()
            if not target:
                return
            idx = '1.0'
            while True:
                idx = self.text_editor.search(target, idx, nocase=1, stopindex=tk.END)
                if not idx:
                    break
                endidx = f"{idx}+{len(target)}c"
                self.text_editor.delete(idx, endidx)
                self.text_editor.insert(idx, replacement)
                idx = f"{idx}+{len(replacement)}c"
            do_find()

        ttk.Button(fr_win, text="查找", command=do_find).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(fr_win, text="替换", command=do_replace).grid(row=2, column=1, padx=5, pady=5)

    # ===============================
    #     发送命令相关功能
    # ===============================
    def _send_commands(self, mode):
        """
        发送命令的回调
        mode = "selected_or_cursor"
        """
        if not self.send_callback:
            messagebox.showinfo("提示", "未实现发送回调函数。")
            return

        # 如果有选中内容，则发送所选；否则发送光标所在行
        try:
            selection = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selection.strip():
                lines = selection.splitlines()
            else:
                lines = []
        except:
            lines = []

        if not lines:
            # 没有选中，则获取光标所在行
            cursor_index = self.text_editor.index(tk.INSERT)
            row_str = cursor_index.split('.')[0]
            line_start = f"{row_str}.0"
            line_end = f"{row_str}.end"
            line_content = self.text_editor.get(line_start, line_end)
            lines = [line_content]

        # 把这些行传给外部的回调
        content = "\n".join(lines)
        self.send_callback(mode, content, self.text_editor)

    def _send_next_line(self):
        """
        “逐行发送”按钮:
        1. 获取当前光标所在行
        2. 高亮该行
        3. 调用回调发送
        4. 移动光标到下一行
        """
        if not self.send_callback:
            messagebox.showinfo("提示", "未实现发送回调函数。")
            return

        # 获取当前光标所在行
        cursor_index = self.text_editor.index("insert")
        row_str = cursor_index.split('.')[0]
        row = int(row_str)

        # 获取总行数
        total_lines = int(self.text_editor.index('end').split('.')[0]) - 1
        if total_lines < 1:
            messagebox.showwarning("提示", "没有可发送的命令行")
            return

        # 如果当前行超过范围，则重置到第1行
        if row < 1 or row > total_lines:
            row = 1

        # 高亮该行
        self.text_editor.tag_remove(self.highlight_tag, "1.0", "end")
        line_start = f"{row}.0"
        line_end = f"{row}.end"
        self.text_editor.tag_add(self.highlight_tag, line_start, line_end)

        # 获取当前行内容
        line_content = self.text_editor.get(line_start, line_end).strip()
        if not line_content:
            self.write_log("当前行为空，跳过")
        else:
            # 发送
            self.send_callback("single_line_flow", line_content, self.text_editor)

        # 将光标移动到下一行
        row += 1
        if row > total_lines:
            row = 1
        next_line = f"{row}.0"
        self.text_editor.mark_set("insert", next_line)
        # 确保滚动到可见范围
        self.text_editor.see(next_line)
