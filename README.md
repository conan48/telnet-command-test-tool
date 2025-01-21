# Telnet命令测试工具

一个基于Python/Tkinter的Telnet命令测试工具，提供图形界面来执行和管理Telnet命令测试。

## 功能特点

- 图形化界面，操作简单直观
- 支持批量执行命令
- 支持命令执行结果的实时显示
- 支持导出测试结果到Excel
- 支持配置的导入导出
- 支持命令执行的超时设置
- 支持错误处理策略配置
- 提供高级命令编辑器
- 实时显示测试结果统计图表

## 系统要求

- Python 3.6+
- 依赖包：
  - tkinter (Python标准库)
  - matplotlib
  - openpyxl (可选，用于Excel导出)

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/telnet-command-test-tool.git
cd telnet-command-test-tool
```

2. 安装依赖：
```bash
pip install matplotlib openpyxl
```

## 使用方法

1. 运行程序：
```bash
python MyProject/main.py
```

2. 在界面中设置：
   - Telnet IP和端口
   - 命令文件路径
   - 执行次数
   - 超时时间
   - 输出模式等

3. 点击"连接"按钮建立Telnet连接

4. 点击"开始执行"运行测试

## 项目结构

```
MyProject/
├── main.py                 # 程序入口
└── telnet_app/            # 主程序包
    ├── __init__.py        # 包初始化
    ├── telnet_gui.py      # GUI启动
    ├── telnet_manager.py  # Telnet管理
    ├── config_manager.py  # 配置管理
    ├── advanced_editor.py # 高级编辑器
    └── gui/               # GUI模块
        ├── __init__.py    # GUI包初始化
        ├── main_window.py # 主窗口
        ├── log_manager.py # 日志管理
        ├── chart_manager.py # 图表管理
        ├── config_manager.py # 配置管理
        └── command_editor.py # 命令编辑器
```

## 配置文件格式

配置文件使用JSON格式，包含以下字段：
```json
{
    "host": "192.168.0.21",
    "port": 81,
    "loop_count": 1,
    "commands_file": "commands.txt",
    "log_dir": "telnet_logs",
    "delay_ms": 0,
    "timeout": 10,
    "output_mode": "do_not_generate",
    "stop_on_error": false
}
```

## 命令文件格式

命令文件是一个文本文件，每行一条命令。支持以下格式：
- 普通命令行
- 以#开头的注释行
- DELAY指令（例如：DELAY 1000 表示延时1秒）

## 许可证

MIT License
