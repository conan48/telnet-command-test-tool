# telnet_manager.py

import telnetlib
import time
from threading import Event

class TelnetManager:
    """
    封装 Telnet 连接和命令执行的核心逻辑
    """
    def __init__(self, host, port, timeout=10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.tn = None
        self.is_connected = False

    def connect(self):
        """
        建立 Telnet 连接。如果已连接过，会先关闭再重连。
        """
        self.close()
        try:
            self.tn = telnetlib.Telnet(self.host, self.port, self.timeout)
            self.is_connected = True
            # 读取初始提示符，确保连接正常
            self.tn.read_until(b">", timeout=self.timeout)
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Telnet 连接失败: {e}")

    def close(self):
        """ 关闭 Telnet 连接 """
        if self.tn:
            try:
                self.tn.close()
            except:
                pass
        self.is_connected = False

    def execute_command(self, command, stop_event: Event = None, delay_ms=0):
        """
        执行一条命令，并读取返回结果
        - stop_event：在等待响应时，可用于中断
        - delay_ms：执行完当前命令后，额外等待的时间
        """
        if not self.is_connected or not self.tn:
            raise RuntimeError("尚未建立 Telnet 连接，无法执行命令。")

        start_time = time.time()

        # 发送命令
        self.tn.write(command.encode('ascii') + b'\n')

        # 读取直到提示符（假设提示符为 'CIG-EVK-G2:>'）
        prompt = b'CIG-EVK-G2:>'
        try:
            output = self.tn.read_until(prompt, timeout=self.timeout).decode('ascii', errors='ignore')
        except Exception as e:
            raise Exception(f"读取 Telnet 输出时出错: {e}")

        elapsed = time.time() - start_time

        # 可选的延时
        if delay_ms > 0 and not (stop_event and stop_event.is_set()):
            time.sleep(delay_ms / 1000.0)

        return output, elapsed
