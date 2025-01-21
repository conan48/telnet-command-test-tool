# -*- coding: utf-8 -*-
# main.py

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from telnet_app.gui.main_window import MainWindow

def main():
    """启动Telnet GUI程序"""
    app = MainWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
