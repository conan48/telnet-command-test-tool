# Telnet������Թ���

һ������Python/Tkinter��Telnet������Թ��ߣ��ṩͼ�ν�����ִ�к͹���Telnet������ԡ�

## �����ص�

- ͼ�λ����棬������ֱ��
- ֧������ִ������
- ֧������ִ�н����ʵʱ��ʾ
- ֧�ֵ������Խ����Excel
- ֧�����õĵ��뵼��
- ֧������ִ�еĳ�ʱ����
- ֧�ִ������������
- �ṩ�߼�����༭��
- ʵʱ��ʾ���Խ��ͳ��ͼ��

## ϵͳҪ��

- Python 3.6+
- ��������
  - tkinter (Python��׼��)
  - matplotlib
  - openpyxl (��ѡ������Excel����)

## ��װ

1. ��¡�ֿ⣺
```bash
git clone https://github.com/yourusername/telnet-command-test-tool.git
cd telnet-command-test-tool
```

2. ��װ������
```bash
pip install matplotlib openpyxl
```

## ʹ�÷���

1. ���г���
```bash
python MyProject/main.py
```

2. �ڽ��������ã�
   - Telnet IP�Ͷ˿�
   - �����ļ�·��
   - ִ�д���
   - ��ʱʱ��
   - ���ģʽ��

3. ���"����"��ť����Telnet����

4. ���"��ʼִ��"���в���

## ��Ŀ�ṹ

```
MyProject/
������ main.py                 # �������
������ telnet_app/            # �������
    ������ __init__.py        # ����ʼ��
    ������ telnet_gui.py      # GUI����
    ������ telnet_manager.py  # Telnet����
    ������ config_manager.py  # ���ù���
    ������ advanced_editor.py # �߼��༭��
    ������ gui/               # GUIģ��
        ������ __init__.py    # GUI����ʼ��
        ������ main_window.py # ������
        ������ log_manager.py # ��־����
        ������ chart_manager.py # ͼ�����
        ������ config_manager.py # ���ù���
        ������ command_editor.py # ����༭��
```

## �����ļ���ʽ

�����ļ�ʹ��JSON��ʽ�����������ֶΣ�
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

## �����ļ���ʽ

�����ļ���һ���ı��ļ���ÿ��һ�����֧�����¸�ʽ��
- ��ͨ������
- ��#��ͷ��ע����
- DELAYָ����磺DELAY 1000 ��ʾ��ʱ1�룩

## ���֤

MIT License
