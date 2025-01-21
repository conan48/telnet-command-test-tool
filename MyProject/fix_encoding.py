# -*- coding: utf-8 -*-

def fix_file_encoding(filename):
    try:
        # 首先尝试用UTF-8读取
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"File already in UTF-8: {filename}")
            return
    except UnicodeDecodeError:
        pass
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return

    try:
        # 尝试用GBK读取
        with open(filename, 'r', encoding='gbk') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Failed to read with GBK: {filename}")
        return

    # 重新保存为UTF-8
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Converted to UTF-8: {filename}")

def find_python_files(directory):
    import os
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

if __name__ == "__main__":
    import os
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 获取所有Python文件
    python_files = find_python_files(script_dir)
    
    # 修复每个文件的编码
    for file in python_files:
        fix_file_encoding(file) 