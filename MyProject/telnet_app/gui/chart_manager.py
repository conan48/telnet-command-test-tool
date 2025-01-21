# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class ChartManager:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        
        # 创建图表框架
        self.chart_frame = ttk.Frame(parent_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建统计标签
        self.stats_frame = ttk.Frame(self.chart_frame)
        self.stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.total_label = ttk.Label(self.stats_frame, text="总数: 0")
        self.total_label.pack(side=tk.LEFT, padx=5)
        
        self.pass_label = ttk.Label(self.stats_frame, text="通过: 0")
        self.pass_label.pack(side=tk.LEFT, padx=5)
        
        self.fail_label = ttk.Label(self.stats_frame, text="失败: 0")
        self.fail_label.pack(side=tk.LEFT, padx=5)
        
        # 创建图表
        self.figure = Figure(figsize=(4, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 初始化图表
        self.init_chart()

    def init_chart(self):
        """初始化图表"""
        self.ax.clear()
        # 使用柱状图代替饼图来显示初始状态
        self.ax.bar(['通过', '失败'], [0, 0], color=['#27ae60', '#e74c3c'])
        self.ax.set_ylim(0, 1)  # 设置y轴范围
        self.ax.set_title('测试结果统计')
        self.canvas.draw()

    def update_chart(self, results):
        """更新图表"""
        if not results:
            self.init_chart()
            return

        # 计算统计数据
        total = len(results)
        pass_count = results.count("Pass")
        fail_count = results.count("Fail")
        
        # 更新标签
        self.total_label.config(text=f"总数: {total}")
        self.pass_label.config(text=f"通过: {pass_count}")
        self.fail_label.config(text=f"失败: {fail_count}")
        
        # 更新图表
        self.ax.clear()
        if total > 0:
            # 如果有数据，使用饼图
            values = [pass_count, fail_count]
            if sum(values) > 0:  # 确保至少有一个非零值
                labels = ['通过', '失败']
                colors = ['#27ae60', '#e74c3c']
                
                self.ax.pie(values, labels=labels, colors=colors, 
                          autopct='%1.1f%%', startangle=90)
                self.ax.axis('equal')
                self.ax.set_title('测试结果统计')
            else:
                # 如果所有值都是0，使用柱状图
                self.init_chart()
        else:
            self.init_chart()
        
        # 调整布局
        self.figure.tight_layout()
        self.canvas.draw() 