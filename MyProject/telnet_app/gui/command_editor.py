# -*- coding: utf-8 -*-

from threading import Thread

class CommandEditor:
    def __init__(self, parent):
        self.parent = parent

    def open_advanced_editor(self):
        """打开高级编辑器"""
        from ..advanced_editor import AdvancedEditor
        
        # 从主窗口获取命令文件路径
        commands_file = self.parent.commands_file_var.get()
        
        # 打开高级编辑器
        AdvancedEditor(
            self.parent,
            send_callback=self._editor_send_callback,
            initial_file=commands_file
        )

    def _editor_send_callback(self, mode, content, text_widget):
        """
        编辑器发送按钮点击的回调函数
        """
        # 处理不同模式
        if mode == "selected_or_cursor":
            # 可能是多行或单行
            lines = content.splitlines()
            lines = [ln for ln in lines if ln.strip()]  # 过滤空行
            if not lines:
                self.parent.log_manager.write_log("没有命令可发送")
                return

            # 启动执行线程
            self.parent.telnet_thread = Thread(
                target=self._run_commands_from_editor,
                args=(lines,)
            )
            self.parent.telnet_thread.daemon = True
            self.parent.telnet_thread.start()

        elif mode == "single_line_flow":
            # 单行模式
            line_to_send = content.strip()
            if not line_to_send:
                return

            # 启动执行线程
            self.parent.telnet_thread = Thread(
                target=self._run_commands_from_editor,
                args=([line_to_send],)
            )
            self.parent.telnet_thread.daemon = True
            self.parent.telnet_thread.start()
        else:
            self.parent.log_manager.write_log(f"未知的发送模式: {mode}")

    def _run_commands_from_editor(self, lines_to_send):
        """在线程中执行命令"""
        # 清除之前的结果和数据
        self.parent.stop_event.clear()
        self.parent.test_results.clear()
        self.parent.excel_data.clear()

        for line in lines_to_send:
            if self.parent.stop_event.is_set():
                self.parent.log_manager.write_log("用户终止执行。")
                break

            cmd_str = line.strip()
            if not cmd_str:
                continue

            # 调用GUI的execute_one_command
            success = self.parent.execute_one_command(cmd_str, self.parent.delay_ms_var.get())
            if not success and self.parent.stop_on_error_var.get():
                self.parent.log_manager.write_log("遇到错误，停止执行。")
                self.parent.stop_event.set()
                break

        # 保存Excel
        self.parent.save_excel_if_needed() 