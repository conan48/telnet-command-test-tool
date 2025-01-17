# config_manager.py

import json
import os

def import_config(file_path):
    """ 从指定 JSON 文件导入配置 """
    if not os.path.isfile(file_path):
        raise FileNotFoundError("配置文件不存在。")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def export_config(file_path, config_data):
    """ 将配置字典导出到 JSON 文件 """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
