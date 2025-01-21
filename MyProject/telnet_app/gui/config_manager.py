# -*- coding: utf-8 -*-

from tkinter import filedialog, messagebox
from ..config_manager import import_config, export_config

class ConfigManager:
    def __init__(self, parent):
        self.parent = parent

    def import_config(self):
        """导入配置"""
        config_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if not config_path:
            return

        try:
            data = import_config(config_path)
            self.parent.host_var.set(data.get("host", "192.168.0.21"))
            self.parent.port_var.set(data.get("port", 81))
            self.parent.loop_count_var.set(data.get("loop_count", 1))
            self.parent.commands_file_var.set(data.get("commands_file", "commands.txt"))
            self.parent.log_dir_var.set(data.get("log_dir", "telnet_logs"))
            self.parent.delay_ms_var.set(data.get("delay_ms", 0))
            self.parent.timeout_var.set(data.get("timeout", 10))
            self.parent.output_mode_var.set(data.get("output_mode", "do_not_generate"))
            self.parent.stop_on_error_var.set(data.get("stop_on_error", False))
            messagebox.showinfo("提示", "配置导入成功！")
        except Exception as e:
            messagebox.showerror("错误", f"导入配置失败：{e}")

    def export_config(self):
        """导出配置"""
        config_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            defaultextension=".json"
        )
        if not config_path:
            return

        data = {
            "host": self.parent.host_var.get(),
            "port": self.parent.port_var.get(),
            "loop_count": self.parent.loop_count_var.get(),
            "commands_file": self.parent.commands_file_var.get(),
            "log_dir": self.parent.log_dir_var.get(),
            "delay_ms": self.parent.delay_ms_var.get(),
            "timeout": self.parent.timeout_var.get(),
            "output_mode": self.parent.output_mode_var.get(),
            "stop_on_error": self.parent.stop_on_error_var.get(),
        }
        try:
            export_config(config_path, data)
            messagebox.showinfo("提示", "配置导出成功！")
        except Exception as e:
            messagebox.showerror("错误", f"导出配置失败：{e}")

    def select_commands_file(self):
        """选择命令文件"""
        file_path = filedialog.askopenfilename(
            title="选择命令文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.parent.commands_file_var.set(file_path)

    def select_log_dir(self):
        """选择日志目录"""
        directory = filedialog.askdirectory(title="选择日志目录")
        if directory:
            self.parent.log_dir_var.set(directory) 