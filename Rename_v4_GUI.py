"""
灵犀·晓伴 版本发布系统 - GUI界面
基于Tkinter的图形用户界面，实现版本发布的可视化操作
"""

import os
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path
from ctypes import windll


def enable_dpi_awareness():
    """启用高DPI支持，解决Windows下字体模糊问题"""
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError, Exception):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError, Exception):
                pass
    except Exception:
        pass


class ReleaseSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("灵犀·晓伴 版本发布系统")
        
        # 根据屏幕分辨率自适应窗口大小
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算合适的窗口大小（屏幕的85%宽度，90%高度）
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.9)
        self.root.geometry(f"{window_width}x{window_height}")
        
        # 设置最小窗口大小
        self.root.minsize(1400, 900)
        
        # 窗口居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # 计算DPI缩放因子
        self.scale_factor = screen_width / 1920  # 以1920为基准
        if self.scale_factor < 1.0:
            self.scale_factor = 1.0
        elif self.scale_factor > 2.0:
            self.scale_factor = 2.0  # 限制最大缩放
        
        # 增加额外的缩放因子以获得更大的字体
        self.scale_factor *= 1.3
        
        # 设置窗口图标和背景色
        self.root.configure(bg='#f5f6fa')
        
        # 设置窗口缩放
        self.root.tk.call('tk', 'scaling', 1.0 + (self.scale_factor / 1.3 - 1.0) * 0.3)
        
        # 预置路径
        self.path = './'
        self.helppath = './help_documentation'
        self.uppath = './upgrade_package'
        self.pkgpath = './package'
        
        # 运行状态
        self.is_running = False
        self.execution_thread = None
        
        # 创建界面
        self.create_widgets()
        
        # 初始化检查
        self.check_system_status()
    
    def create_widgets(self):
        """创建所有界面组件"""
        # 根据缩放因子计算字体大小 - 增大基础字体
        base_font_size = 12  # 从10增加到12
        title_font_size = int(20 * self.scale_factor)  # 从18增加到20
        subtitle_font_size = int(13 * self.scale_factor)  # 从11增加到13
        section_font_size = int(12 * self.scale_factor)  # 从10增加到12
        label_font_size = int(base_font_size * self.scale_factor)
        small_font_size = int(10 * self.scale_factor)  # 从8增加到10
        
        # 计算内边距
        base_padding = int(15 * self.scale_factor)
        card_padding = int(10 * self.scale_factor)
        
        # 样式设置
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置现代化配色方案
        colors = {
            'primary': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'info': '#16a085',
            'dark': '#2c3e50',
            'light': '#ecf0f1',
            'card_bg': '#ffffff',
            'border': '#bdc3c7'
        }
        
        # 标题样式
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', title_font_size, 'bold'), 
                       foreground='#1a1a2e', background='#ffffff')
        style.configure('Subtitle.TLabel', font=('Microsoft YaHei UI', subtitle_font_size), 
                       foreground='#636e72', background='#ffffff')
        
        # 区块标题样式
        style.configure('Section.TLabel', font=('Microsoft YaHei UI', section_font_size, 'bold'), 
                       foreground=colors['dark'])
        
        # 状态文本样式
        style.configure('Status.TLabel', font=('Microsoft YaHei UI', label_font_size), 
                       foreground='#636e72')
        style.configure('Success.TLabel', foreground=colors['success'], font=('Microsoft YaHei UI', label_font_size, 'bold'))
        style.configure('Warning.TLabel', foreground=colors['warning'], font=('Microsoft YaHei UI', label_font_size, 'bold'))
        style.configure('Error.TLabel', foreground=colors['danger'], font=('Microsoft YaHei UI', label_font_size, 'bold'))
        style.configure('Info.TLabel', foreground=colors['primary'], font=('Microsoft YaHei UI', label_font_size, 'bold'))
        
        # 卡片样式
        style.configure('Card.TLabelframe', background='#ffffff', borderwidth=1, relief='solid')
        style.configure('Card.TLabelframe.Label', font=('Microsoft YaHei UI', section_font_size, 'bold'),
                       foreground=colors['dark'], background='#ffffff')
        
        # 按钮样式
        style.configure('TButton', font=('Microsoft YaHei UI', label_font_size), padding=6)
        style.map('TButton',
                 background=[('active', colors['light'])],
                 foreground=[('active', colors['dark'])])
        
        # 输入框样式
        style.configure('TEntry', font=('Microsoft YaHei UI', label_font_size), fieldbackground='#ffffff',
                      insertbackground=colors['primary'])
        style.map('TEntry', focuscolor=[('focus', colors['primary'])])
        
        # 保存缩放因子供后续使用
        self.font_sizes = {
            'title': title_font_size,
            'subtitle': subtitle_font_size,
            'section': section_font_size,
            'label': label_font_size,
            'small': small_font_size,
            'base': base_font_size
        }
        self.padding = {
            'base': base_padding,
            'card': card_padding
        }
        
        # 主容器 - 使用带背景色的Frame
        main_frame = tk.Frame(self.root, bg='#f5f6fa')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=base_padding, pady=base_padding)
        
        # 内容区域容器（使用grid布局）
        content_area = tk.Frame(main_frame, bg='#f5f6fa')
        content_area.pack(fill=tk.BOTH, expand=True)
        content_area.columnconfigure(0, weight=1)
        content_area.columnconfigure(1, weight=1)
        # header (row 0) should not take remaining weight; set later for specific rows
        content_area.rowconfigure(0, weight=0)

        # ========== 标题区域 ==========
        header_frame = tk.Frame(content_area, bg='#ffffff', relief='raised', bd=1)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, int(15 * self.scale_factor)))
        header_frame.columnconfigure(0, weight=1)

        # 标题容器
        title_container = tk.Frame(header_frame, bg='#ffffff')
        title_container.pack(side=tk.LEFT, padx=int(20 * self.scale_factor), pady=int(12 * self.scale_factor))

        title_label = tk.Label(title_container, text="灵犀·晓伴 版本发布系统",
                              font=('Microsoft YaHei UI', title_font_size, 'bold'), 
                              bg='#ffffff', fg='#1a1a2e')
        title_label.pack(anchor=tk.W)

        subtitle_label = tk.Label(title_container, text="自动化版本打包与发布管理平台",
                                 font=('Microsoft YaHei UI', subtitle_font_size), 
                                 bg='#ffffff', fg='#636e72')
        subtitle_label.pack(anchor=tk.W)

        # 按钮容器
        button_container = tk.Frame(header_frame, bg='#ffffff')
        button_container.pack(side=tk.RIGHT, padx=int(20 * self.scale_factor), pady=int(12 * self.scale_factor))

        # 刷新按钮
        refresh_btn = tk.Button(button_container, text="刷新状态", 
                               font=('Microsoft YaHei UI', label_font_size),
                               bg=colors['light'], fg=colors['dark'],
                               activebackground=colors['border'], activeforeground=colors['dark'],
                               relief='solid', bd=1, padx=int(15 * self.scale_factor), pady=int(6 * self.scale_factor),
                               command=self.check_system_status)
        refresh_btn.pack(side=tk.LEFT, padx=int(8 * self.scale_factor))

        # 执行按钮 - 更显眼
        self.header_execute_btn = tk.Button(button_container, text="执行发布", 
                                           font=('Microsoft YaHei UI', int(16 * self.scale_factor), 'bold'),
                                           bg='#e74c3c', fg='white',
                                           activebackground='#c0392b', activeforeground='white',
                                           relief='solid', bd=2, padx=int(40 * self.scale_factor), pady=int(15 * self.scale_factor),
                                           cursor='hand2',
                                           command=self.execute_release)
        self.header_execute_btn.pack(side=tk.LEFT, padx=int(10 * self.scale_factor))

        # ========== 内容区域布局（网格） ==========
        # 第一行：执行按钮（跨越两列） - 放在 row=1，避免与 header(row=0) 重叠
        execute_frame = tk.Frame(content_area, bg='#f5f6fa')
        execute_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, int(15 * self.scale_factor)))
        execute_frame.columnconfigure(0, weight=1)

        self.execute_btn = tk.Button(execute_frame, text="开始执行发布", 
                                    font=('Microsoft YaHei UI', int(18 * self.scale_factor), 'bold'),
                                    bg='#27ae60', fg='white',
                                    activebackground='#219a52', activeforeground='white',
                                    relief='solid', bd=3, padx=int(40 * self.scale_factor), pady=int(15 * self.scale_factor),
                                    cursor='hand2',
                                    command=self.execute_release)
        self.execute_btn.pack(pady=int(10 * self.scale_factor), fill=tk.X)

        # 左侧主内容放在 row=2，使用可滚动容器以避免内容过高导致遮挡
        left_container = tk.Frame(content_area, bg='#f5f6fa')
        left_container.grid(row=2, column=0, sticky=(tk.N, tk.S, tk.W, tk.E), padx=(0, int(8 * self.scale_factor)))
        left_container.rowconfigure(0, weight=1)
        left_container.columnconfigure(0, weight=1)

        # 使用 Canvas + 垂直滚动条 来实现可滚动的左侧面板
        left_canvas = tk.Canvas(left_container, bg='#f5f6fa', highlightthickness=0)
        left_vscroll = tk.Scrollbar(left_container, orient=tk.VERTICAL, command=left_canvas.yview)
        left_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_canvas.configure(yscrollcommand=left_vscroll.set)

        left_panel = tk.Frame(left_canvas, bg='#f5f6fa')
        left_window = left_canvas.create_window((0, 0), window=left_panel, anchor='nw')

        # 当内层内容改变尺寸时更新滚动区域和窗口宽度
        def _on_left_config(event):
            left_canvas.configure(scrollregion=left_canvas.bbox('all'))
            # 保持内部窗口宽度与canvas一致，避免横向出现滚动条
            if left_panel.winfo_reqwidth() != left_canvas.winfo_width():
                left_canvas.itemconfigure(left_window, width=left_canvas.winfo_width())

        left_panel.bind('<Configure>', _on_left_config)

        # 鼠标滚轮支持（Windows）
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')

        left_canvas.bind_all('<MouseWheel>', _on_mousewheel)

        left_panel.columnconfigure(0, weight=1)

        # 右侧面板（列1，行1-5）
        right_panel = tk.Frame(content_area, bg='#f5f6fa')
        right_panel.grid(row=2, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        right_panel.rowconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)

        # 配置内容区域的行权重：
        # row 0 = header (不占伸展空间)，row 1 = execute 按钮行（不占伸展空间），row 2 = 主内容（左右面板，伸展）
        content_area.rowconfigure(0, weight=0)   # header
        content_area.rowconfigure(1, weight=0)   # execute 按钮行
        content_area.rowconfigure(2, weight=1)   # 左右面板行（主伸展区域）
        content_area.columnconfigure(0, weight=1) # 左列
        content_area.columnconfigure(1, weight=1) # 右列

        # ========== 左侧卡片（垂直顺序） ==========
        # 使用相同的父框架left_panel，但每个卡片单独一行
        # 系统状态卡片 - 行1
        status_panel = self.create_card(left_panel, "系统状态", row=0)
        self.create_status_panel(status_panel)
        
        # 版本信息卡片 - 行2
        version_panel = self.create_card(left_panel, "版本信息配置", row=1)
        self.create_version_panel(version_panel)
        
        # 平台选择卡片 - 行3
        platform_panel = self.create_card(left_panel, "目标平台选择", row=2)
        self.create_platform_panel(platform_panel)
        
        # 文件夹处理卡片 - 行4
        folder_panel = self.create_card(left_panel, "文件夹处理", row=3)
        self.create_folder_panel(folder_panel)
        
        # 执行进度与操作卡片 - 行5
        exec_panel = self.create_card(left_panel, "执行进度与操作", row=4)
        self.create_execution_panel(exec_panel)
        
        # ========== 右侧日志面板 ==========
        log_frame = tk.LabelFrame(right_panel, text=" 操作日志 ", font=('Microsoft YaHei UI', int(11 * self.scale_factor), 'bold'),
                                 bg='#ffffff', fg='#2c3e50', relief='solid', bd=1)
        log_frame.pack(fill=tk.BOTH, expand=True)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.create_log_panel(log_frame)
        
        # ========== 底部状态栏 ==========
        self.create_status_bar(main_frame)
    
    def create_status_panel(self, panel):
        """创建系统状态面板"""
        self.status_labels = {}
        
        status_items = [
            ('package', 'Package 文件夹'),
            ('upgrade', 'upgrade_package 文件夹'),
            ('help', '帮助文档文件夹'),
            ('main_folder', '主版本文件夹'),
        ]
        
        for i, (key, label_text) in enumerate(status_items):
            frame = tk.Frame(panel, bg='#ffffff')
            frame.grid(row=i//2, column=i%2, sticky=(tk.W, tk.E), padx=int(8 * self.scale_factor), pady=int(6 * self.scale_factor))
            panel.columnconfigure(0, weight=1)
            panel.columnconfigure(1, weight=1)
            
            label = tk.Label(frame, text=label_text, font=('Microsoft YaHei UI', self.font_sizes['label']),
                           bg='#ffffff', fg='#636e72')
            label.pack(side=tk.LEFT, padx=int(5 * self.scale_factor))
            
            value_label = tk.Label(frame, text="等待检查...", font=('Microsoft YaHei UI', self.font_sizes['label'], 'bold'),
                                 bg='#ffffff', fg='#bdc3c7')
            value_label.pack(side=tk.RIGHT, padx=int(5 * self.scale_factor))
            
            self.status_labels[key] = value_label
    
    def create_version_panel(self, panel):
        """创建版本信息面板"""
        # 版本号输入
        tk.Label(panel, text="灵犀·晓伴版本号:", font=('Microsoft YaHei UI', self.font_sizes['label']),
                bg='#ffffff', fg='#2c3e50').grid(row=0, column=0, sticky=tk.W, pady=int(8 * self.scale_factor))
        self.version_entry = tk.Entry(panel, width=22, font=('Microsoft YaHei UI', self.font_sizes['label']),
                                     insertbackground='#3498db')
        self.version_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=int(8 * self.scale_factor))
        self.version_entry.insert(0, "1.1.33")
        
        tk.Label(panel, text="格式: x.x.x", font=('Microsoft YaHei UI', self.font_sizes['small']),
                bg='#ffffff', fg='#95a5a6').grid(row=0, column=2, padx=int(8 * self.scale_factor))
        
        # WPS版本号输入
        tk.Label(panel, text="WPS版本号:", font=('Microsoft YaHei UI', self.font_sizes['label']),
                bg='#ffffff', fg='#2c3e50').grid(row=1, column=0, sticky=tk.W, pady=int(8 * self.scale_factor))
        self.wps_version_entry = tk.Entry(panel, width=22, font=('Microsoft YaHei UI', self.font_sizes['label']),
                                         insertbackground='#3498db')
        self.wps_version_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=int(8 * self.scale_factor))
        self.wps_version_entry.insert(0, "")
        
        tk.Label(panel, text="可选", font=('Microsoft YaHei UI', self.font_sizes['small']),
                bg='#ffffff', fg='#95a5a6').grid(row=1, column=2, padx=int(8 * self.scale_factor))
        
        # 日期输入
        tk.Label(panel, text="发布日期:", font=('Microsoft YaHei UI', self.font_sizes['label']),
                bg='#ffffff', fg='#2c3e50').grid(row=2, column=0, sticky=tk.W, pady=int(8 * self.scale_factor))
        self.date_entry = tk.Entry(panel, width=22, font=('Microsoft YaHei UI', self.font_sizes['label']),
                                   insertbackground='#3498db')
        self.date_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=int(8 * self.scale_factor))
        
        # 自动填充今天的日期
        today = datetime.now().strftime("%Y%m%d")
        self.date_entry.insert(0, today)
        
        tk.Label(panel, text="格式: YYYYMMDD", font=('Microsoft YaHei UI', self.font_sizes['small']),
                bg='#ffffff', fg='#95a5a6').grid(row=2, column=2, padx=int(8 * self.scale_factor))
        
        panel.columnconfigure(1, weight=1)
    
    def create_platform_panel(self, panel):
        """创建平台选择面板"""
        self.platform_vars = {}
        
        platforms = [
            ('linux-arm64', 'Linux ARM64', '统信/麒麟'),
            ('linux-x64', 'Linux x64', '统信/麒麟'),
            ('mac-arm64', 'Mac ARM64', 'Apple Silicon'),
            ('mac-x64', 'Mac x64', 'Intel Mac'),
            ('win-x64', 'Windows x64', 'Windows 10/11'),
        ]
        
        for i, (key, icon, desc) in enumerate(platforms):
            frame = tk.Frame(panel, bg='#ffffff')
            frame.pack(fill=tk.X, pady=int(5 * self.scale_factor))
            
            var = tk.BooleanVar(value=True)
            self.platform_vars[key] = var
            
            checkbox = tk.Checkbutton(frame, variable=var, text=f"  {desc}",
                                    font=('Microsoft YaHei UI', self.font_sizes['label']),
                                    bg='#ffffff', fg='#2c3e50',
                                    activebackground='#ffffff', activeforeground='#2c3e50',
                                    selectcolor='#e8f4f8',
                                    padx=int(5 * self.scale_factor), pady=int(2 * self.scale_factor))
            checkbox.pack(side=tk.LEFT, padx=int(5 * self.scale_factor))
        
        # 全选/全不选按钮
        button_frame = tk.Frame(panel, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(int(15 * self.scale_factor), 0))
        
        tk.Button(button_frame, text="全选", font=('Microsoft YaHei UI', self.font_sizes['label']),
                 bg='#ecf0f1', fg='#2c3e50',
                 activebackground='#bdc3c7', activeforeground='#2c3e50',
                 relief='solid', bd=1, padx=int(12 * self.scale_factor), pady=int(5 * self.scale_factor),
                 command=self.select_all_platforms).pack(side=tk.LEFT, padx=int(5 * self.scale_factor))
        
        tk.Button(button_frame, text="全不选", font=('Microsoft YaHei UI', self.font_sizes['label']),
                 bg='#ecf0f1', fg='#2c3e50',
                 activebackground='#bdc3c7', activeforeground='#2c3e50',
                 relief='solid', bd=1, padx=int(12 * self.scale_factor), pady=int(5 * self.scale_factor),
                 command=self.deselect_all_platforms).pack(side=tk.LEFT, padx=int(5 * self.scale_factor))
    
    def create_folder_panel(self, panel):
        """创建文件夹处理面板"""
        # 处理已存在的主文件夹
        tk.Label(panel, text="已存在版本文件夹处理:", font=('Microsoft YaHei UI', self.font_sizes['section'], 'bold'),
                bg='#ffffff', fg='#2c3e50').pack(anchor=tk.W, pady=(0, int(8 * self.scale_factor)))
        
        self.main_folder_var = tk.StringVar(value="skip")
        
        options = [('跳过 (不删除)', 'skip'),
                   ('删除并重新创建', 'delete'),
                   ('重命名现有文件夹', 'rename')]
        
        for text, value in options:
            rb = tk.Radiobutton(panel, text=text, variable=self.main_folder_var, value=value,
                               font=('Microsoft YaHei UI', self.font_sizes['label']),
                               bg='#ffffff', fg='#2c3e50',
                               activebackground='#ffffff', activeforeground='#2c3e50',
                               selectcolor='#e8f4f8',
                               anchor=tk.W, padx=int(5 * self.scale_factor), pady=int(3 * self.scale_factor))
            rb.pack(fill=tk.X, padx=int(5 * self.scale_factor))
        
        # 分隔线
        separator = tk.Frame(panel, height=1, bg='#e0e0e0')
        separator.pack(fill=tk.X, pady=int(12 * self.scale_factor))
        
        # 处理upgrade_package文件夹
        tk.Label(panel, text="upgrade_package文件夹处理:", font=('Microsoft YaHei UI', self.font_sizes['section'], 'bold'),
                bg='#ffffff', fg='#2c3e50').pack(anchor=tk.W, pady=(0, int(8 * self.scale_factor)))
        
        self.upgrade_folder_var = tk.StringVar(value="keep")
        
        options = [('保留现有文件', 'keep'),
                   ('清空所有内容', 'clear')]
        
        for text, value in options:
            rb = tk.Radiobutton(panel, text=text, variable=self.upgrade_folder_var, value=value,
                               font=('Microsoft YaHei UI', self.font_sizes['label']),
                               bg='#ffffff', fg='#2c3e50',
                               activebackground='#ffffff', activeforeground='#2c3e50',
                               selectcolor='#e8f4f8',
                               anchor=tk.W, padx=int(5 * self.scale_factor), pady=int(3 * self.scale_factor))
            rb.pack(fill=tk.X, padx=int(5 * self.scale_factor))
        
        # 手动操作按钮
        button_frame = tk.Frame(panel, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(int(15 * self.scale_factor), 0))
        
        tk.Button(button_frame, text="检查文件夹", font=('Microsoft YaHei UI', self.font_sizes['label']),
                 bg='#3498db', fg='white',
                 activebackground='#2980b9', activeforeground='white',
                 relief='flat', bd=0, padx=int(15 * self.scale_factor), pady=int(6 * self.scale_factor),
                 command=self.check_folders).pack(side=tk.LEFT, padx=int(5 * self.scale_factor))
        
        tk.Button(button_frame, text="清空升级包", font=('Microsoft YaHei UI', self.font_sizes['label']),
                 bg='#e74c3c', fg='white',
                 activebackground='#c0392b', activeforeground='white',
                 relief='flat', bd=0, padx=int(15 * self.scale_factor), pady=int(6 * self.scale_factor),
                 command=self.clear_upgrade_folder).pack(side=tk.LEFT, padx=int(5 * self.scale_factor))
    
    def create_execution_panel(self, panel):
        """创建执行操作面板（仅含进度、概要、辅助按钮）"""
        # 操作概要
        summary_frame = tk.Frame(panel, bg='#f8f9fa', relief='solid', bd=1)
        summary_frame.pack(fill=tk.X, pady=(0, int(12 * self.scale_factor)))

        tk.Label(summary_frame, text="操作概要:", font=('Microsoft YaHei UI', self.font_sizes['section'], 'bold'),
                bg='#f8f9fa', fg='#2c3e50').pack(anchor=tk.W, padx=int(8 * self.scale_factor), pady=(int(8 * self.scale_factor), int(5 * self.scale_factor)))

        self.summary_labels = {}
        summary_items = [
            ('main_folder', '主文件夹:'),
            ('sub_folders', '平台子文件夹:'),
            ('packages', '安装包数量:'),
            ('upgrades', '升级包数量:'),
        ]

        for key, label_text in summary_items:
            frame = tk.Frame(summary_frame, bg='#f8f9fa')
            frame.pack(fill=tk.X, padx=int(8 * self.scale_factor), pady=int(2 * self.scale_factor))

            tk.Label(frame, text=label_text, font=('Microsoft YaHei UI', self.font_sizes['label']),
                    bg='#f8f9fa', fg='#636e72').pack(side=tk.LEFT)
            value_label = tk.Label(frame, text="等待配置...", font=('Microsoft YaHei UI', self.font_sizes['label'], 'bold'),
                                  bg='#f8f9fa', fg='#3498db')
            value_label.pack(side=tk.RIGHT)

            self.summary_labels[key] = value_label

        # 进度条
        tk.Label(panel, text="执行进度:", font=('Microsoft YaHei UI', self.font_sizes['section'], 'bold'),
                bg='#ffffff', fg='#2c3e50').pack(anchor=tk.W, pady=(int(12 * self.scale_factor), int(6 * self.scale_factor)))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(panel, variable=self.progress_var, maximum=100,
                                          style='Custom.Horizontal.TProgressbar')

        # 自定义进度条样式
        style = ttk.Style()
        thickness = int(20 * self.scale_factor)
        style.configure('Custom.Horizontal.TProgressbar',
                       background='#3498db',
                       troughcolor='#e0e0e0',
                       thickness=thickness)

        self.progress_bar.pack(fill=tk.X, pady=int(5 * self.scale_factor))

        self.progress_text = tk.Label(panel, text="准备就绪", font=('Microsoft YaHei UI', self.font_sizes['label']),
                                     bg='#ffffff', fg='#636e72')
        self.progress_text.pack(anchor=tk.W)

        # 其他操作按钮
        button_frame = tk.Frame(panel, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(int(15 * self.scale_factor), 0))

        separator = tk.Frame(button_frame, height=1, bg='#e0e0e0')
        separator.pack(fill=tk.X, pady=(int(8 * self.scale_factor), int(12 * self.scale_factor)))

        self.simulate_btn = tk.Button(button_frame, text="模拟运行",
                                     font=('Microsoft YaHei UI', int(13 * self.scale_factor)),
                                     bg='#f39c12', fg='white',
                                     activebackground='#e67e22', activeforeground='white',
                                     relief='solid', bd=2, padx=int(25 * self.scale_factor), pady=int(12 * self.scale_factor),
                                     cursor='hand2',
                                     command=self.simulate_release)
        self.simulate_btn.pack(side=tk.LEFT, padx=int(10 * self.scale_factor))

        self.stop_btn = tk.Button(button_frame, text="停止执行",
                                 font=('Microsoft YaHei UI', int(13 * self.scale_factor)),
                                 bg='#e74c3c', fg='white',
                                 activebackground='#c0392b', activeforeground='white',
                                 relief='solid', bd=2, padx=int(25 * self.scale_factor), pady=int(12 * self.scale_factor),
                                 cursor='hand2',
                                 state=tk.DISABLED,
                                 command=self.stop_execution)
        self.stop_btn.pack(side=tk.LEFT, padx=int(10 * self.scale_factor))
    
    def create_log_panel(self, panel):
        """创建日志面板"""
        # 日志面板的父容器已经是LabelFrame，所以这里直接构建内部组件
        
        # 日志文本框
        log_font_size = int(11 * self.scale_factor)  # 从10增加到11
        self.log_text = scrolledtext.ScrolledText(
            panel,
            wrap=tk.WORD,
            font=('Consolas', log_font_size),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='#569cd6',
            selectbackground='#264f78'
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=int(8 * self.scale_factor), pady=int(8 * self.scale_factor))
        
        # 配置日志颜色标签 - 使用VS Code风格
        self.log_text.tag_config('info', foreground='#4fc1ff')
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('warning', foreground='#dcdcaa')
        self.log_text.tag_config('error', foreground='#f14c4c')
        self.log_text.tag_config('timestamp', foreground='#808080')
        
        # 日志操作按钮
        button_frame = tk.Frame(panel, bg='#ffffff')
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(int(12 * self.scale_factor), int(8 * self.scale_factor)), padx=int(8 * self.scale_factor))
        button_frame.columnconfigure(0, weight=1)
        
        tk.Button(button_frame, text="清空日志", font=('Microsoft YaHei UI', self.font_sizes['label']),
                 bg='#ecf0f1', fg='#2c3e50',
                 activebackground='#bdc3c7', activeforeground='#2c3e50',
                 relief='solid', bd=1, padx=int(12 * self.scale_factor), pady=int(5 * self.scale_factor),
                 command=self.clear_log).pack(side=tk.LEFT, padx=int(5 * self.scale_factor))
        
        tk.Button(button_frame, text="导出日志", font=('Microsoft YaHei UI', self.font_sizes['label']),
                 bg='#ecf0f1', fg='#2c3e50',
                 activebackground='#bdc3c7', activeforeground='#2c3e50',
                 relief='solid', bd=1, padx=int(12 * self.scale_factor), pady=int(5 * self.scale_factor),
                 command=self.export_log).pack(side=tk.LEFT, padx=int(5 * self.scale_factor))
        
        # 确保panel的grid可以伸展日志文本框
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

    def create_status_bar(self, parent):
        """创建底部状态栏"""
        status_frame = tk.Frame(parent, bg='#2c3e50', height=int(35 * self.scale_factor))
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(int(10 * self.scale_factor), 0))
        status_frame.pack_propagate(False)
        
        self.status_bar = tk.Label(status_frame, text="就绪", font=('Microsoft YaHei UI', self.font_sizes['label']),
                                  bg='#2c3e50', fg='#ecf0f1')
        self.status_bar.pack(side=tk.LEFT, padx=int(15 * self.scale_factor))
        
        # 统计信息
        self.stats_label = tk.Label(status_frame, text="", font=('Microsoft YaHei UI', self.font_sizes['label']),
                                   bg='#2c3e50', fg='#bdc3c7')
        self.stats_label.pack(side=tk.RIGHT, padx=int(15 * self.scale_factor))
    
    def create_card(self, parent, title, row):
        """创建一个卡片式面板"""
        card = tk.LabelFrame(parent, text=f" {title} ", font=('Microsoft YaHei UI', int(11 * self.scale_factor), 'bold'),
                            bg='#ffffff', fg='#2c3e50', relief='solid', bd=1)
        card.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=int(8 * self.scale_factor))
        card.columnconfigure(0, weight=1)
        return card
    
    # ========== 工具方法 ==========
    
    def log(self, message, level='info'):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        
        # 限制日志条目数量
        line_count = int(self.log_text.index('end-1c').split('.')[0])
        if line_count > 500:
            self.log_text.delete('1.0', '50.0')
    
    def safe_copy(self, source, target):
        """安全的文件复制，处理文件占用错误"""
        try:
            # 检查目标文件是否已存在
            if os.path.exists(target):
                try:
                    os.remove(target)
                    self.log(f"已删除已存在的文件: {os.path.basename(target)}", 'warning')
                except PermissionError:
                    self.log(f"错误: 文件被占用，无法删除: {os.path.basename(target)}，请关闭相关程序后重试", 'error')
                    raise
        
            # 复制文件
            shutil.copy(source, target)
            return True
        except PermissionError as e:
            self.log(f"错误: 文件被占用或没有权限: {os.path.basename(target)}，错误: {e}", 'error')
            return False
        except Exception as e:
            self.log(f"复制文件失败: {os.path.basename(target)}，错误: {e}", 'error')
            return False
    
    def get_pkg_dirs(self, path):
        """获取pkg开头的文件夹列表"""
        pkg_dirs = []
        if os.path.exists(path):
            for file in os.listdir(path):
                if os.path.isdir(os.path.join(path, file)) and re.match(r'^pkg.*', file):
                    pkg_dirs.append(file)
        return pkg_dirs
    
    def get_suxiaoban_setup_files(self, path):
        """获取Windows安装包文件列表"""
        suxiaoban_files = []
        if os.path.exists(path):
            for file in os.listdir(path):
                if re.match(r'^suxiaoban-.*-setup.exe.zip', file):
                    suxiaoban_files.append(file)
        return suxiaoban_files
    
    def check_system_status(self):
        """检查系统状态"""
        self.log("正在检查系统状态...", 'info')
        self.status_bar.config(text="检查系统状态中...")
        
        # 检查package文件夹
        pkg_dirs = self.get_pkg_dirs(self.pkgpath)
        if pkg_dirs:
            self.status_labels['package'].config(
                text=f"已找到 {len(pkg_dirs)} 个文件夹",
                fg='#27ae60'
            )
            self.log(f"Package文件夹: 找到 {len(pkg_dirs)} 个pkg文件夹 - {pkg_dirs}", 'success')
        else:
            self.status_labels['package'].config(
                text="未找到pkg文件夹",
                fg='#e74c3c'
            )
            self.log("Package文件夹: 未找到pkg文件夹", 'error')
        
        # 检查upgrade_package文件夹
        if os.path.exists(self.uppath):
            files = os.listdir(self.uppath)
            if files:
                self.status_labels['upgrade'].config(
                    text=f"有 {len(files)} 个升级包",
                    fg='#f39c12'
                )
                self.log(f"Upgrade文件夹: 有 {len(files)} 个文件", 'warning')
            else:
                self.status_labels['upgrade'].config(
                    text="文件夹为空",
                    fg='#27ae60'
                )
                self.log("Upgrade文件夹: 文件夹为空", 'success')
        else:
            self.status_labels['upgrade'].config(
                text="文件夹不存在",
                fg='#f39c12'
            )
            self.log("Upgrade文件夹: 文件夹不存在", 'warning')
        
        # 检查help_documentation文件夹
        if os.path.exists(self.helppath):
            files = [f for f in os.listdir(self.helppath) if f.endswith('.docx') or f.endswith('.json')]
            self.status_labels['help'].config(
                text=f"有 {len(files)} 个文档",
                fg='#27ae60'
            )
            self.log(f"帮助文档: 找到 {len(files)} 个文档", 'success')
        else:
            self.status_labels['help'].config(
                text="文件夹不存在",
                fg='#e74c3c'
            )
            self.log("帮助文档: 文件夹不存在", 'error')
        
        # 检查是否存在已发布的版本文件夹
        existing_folders = []
        for file in os.listdir('./'):
            if re.match(r'^灵犀·晓伴.*--.*', file):
                existing_folders.append(file)
        
        if existing_folders:
            self.status_labels['main_folder'].config(
                text=f"已存在 {len(existing_folders)} 个版本文件夹",
                fg='#f39c12'
            )
            self.log(f"主版本文件夹: 已存在 {len(existing_folders)} 个 - {existing_folders}", 'warning')
        else:
            self.status_labels['main_folder'].config(
                text="未创建",
                fg='#27ae60'
            )
            self.log("主版本文件夹: 未创建", 'info')
        
        self.update_summary()
        self.status_bar.config(text="系统状态检查完成")
    
    def update_summary(self):
        """更新操作概要"""
        version = self.version_entry.get()
        date = self.date_entry.get()
        
        if version and date:
            main_folder = f"灵犀·晓伴_{version} --{date}"
            self.summary_labels['main_folder'].config(text=main_folder)
            
            selected_platforms = [key for key, var in self.platform_vars.items() if var.get()]
            sub_folders = []
            for platform in selected_platforms:
                if platform == 'win-x64':
                    sub_folders.append(f"灵犀·晓伴 {version} win")
                elif platform in ['mac-arm64', 'mac-x64']:
                    sub_folders.append(f"灵犀·晓伴 {version} mac")
                else:
                    sub_folders.append(f"灵犀·晓伴 {version} 统信+麒麟")
            
            self.summary_labels['sub_folders'].config(text=f"{len(selected_platforms)} 个")
            self.summary_labels['packages'].config(text=f"{len(selected_platforms)} 个安装包")
            self.summary_labels['upgrades'].config(text=f"{len(selected_platforms)} 个升级包")
        else:
            self.summary_labels['main_folder'].config(text="等待配置...")
            self.summary_labels['sub_folders'].config(text="等待配置...")
            self.summary_labels['packages'].config(text="等待配置...")
            self.summary_labels['upgrades'].config(text="等待配置...")
    
    def select_all_platforms(self):
        """全选所有平台"""
        for var in self.platform_vars.values():
            var.set(True)
        self.update_summary()
    
    def deselect_all_platforms(self):
        """全不选"""
        for var in self.platform_vars.values():
            var.set(False)
        self.update_summary()
    
    def check_folders(self):
        """检查文件夹状态"""
        self.log("开始检查文件夹状态...", 'info')
        
        # 检查package文件夹
        pkg_dirs = self.get_pkg_dirs(self.pkgpath)
        if not pkg_dirs:
            messagebox.showwarning("检查结果", "未找到pkg开头的文件夹，无法执行发布操作！")
            self.log("检查失败: 未找到pkg文件夹", 'error')
            return
        
        # 检查已存在的版本文件夹
        existing_folders = []
        for file in os.listdir('./'):
            if re.match(r'^灵犀·晓伴.*--.*', file):
                existing_folders.append(file)
        
        if existing_folders:
            message = f"检查完成，发现 {len(existing_folders)} 个已存在的版本文件夹：\n\n"
            for folder in existing_folders:
                message += f"  - {folder}\n"
            message += "\n请在'文件夹处理'面板中选择处理方式。"
            messagebox.showinfo("检查结果", message)
        else:
            messagebox.showinfo("检查结果", "检查完成，未发现已存在的版本文件夹。")
            self.log("文件夹检查完成", 'success')
    
    def clear_upgrade_folder(self):
        """清空upgrade_package文件夹"""
        if not os.path.exists(self.uppath):
            messagebox.showinfo("提示", "upgrade_package文件夹不存在，无需清空。")
            return
        
        files = os.listdir(self.uppath)
        if not files:
            messagebox.showinfo("提示", "upgrade_package文件夹已经是空的。")
            return
        
        if messagebox.askyesno("确认清空", 
                              f"确定要清空upgrade_package文件夹吗？\n\n文件夹中有 {len(files)} 个文件。"):
            try:
                # 使用subprocess删除
                subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', 'upgrade_package'], 
                              shell=True, check=True)
                os.mkdir(self.uppath)
                self.log(f"upgrade_package文件夹已清空，共删除 {len(files)} 个文件", 'success')
                self.check_system_status()
                messagebox.showinfo("成功", "upgrade_package文件夹已成功清空！")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("错误", f"清空文件夹失败: {e}")
                self.log(f"清空upgrade_package文件夹失败: {e}", 'error')
            except Exception as e:
                messagebox.showerror("错误", f"发生未知错误: {e}")
                self.log(f"清空upgrade_package文件夹时发生错误: {e}", 'error')
    
    def execute_release(self):
        """执行发布流程"""
        if self.is_running:
            return
        
        # 验证输入
        version = self.version_entry.get().strip()
        date = self.date_entry.get().strip()
        
        if not version:
            messagebox.showerror("输入错误", "请输入灵犀·晓伴版本号！")
            return
        
        if not date:
            messagebox.showerror("输入错误", "请输入发布日期！")
            return
        
        if not re.match(r'^\d{8}$', date):
            messagebox.showerror("输入错误", "日期格式不正确，请使用YYYYMMDD格式！")
            return
        
        # 检查pkg文件夹
        pkg_dirs = self.get_pkg_dirs(self.pkgpath)
        if not pkg_dirs:
            messagebox.showerror("错误", "未找到pkg文件夹，无法执行发布操作！")
            return
        
        # 检查是否选择了平台
        selected_platforms = [key for key, var in self.platform_vars.items() if var.get()]
        if not selected_platforms:
            messagebox.showerror("错误", "请至少选择一个目标平台！")
            return
        
        # 确认执行
        version_text = f"版本号: {version}\n"
        version_text += f"日期: {date}\n"
        version_text += f"平台数量: {len(selected_platforms)}\n"
        
        if not messagebox.askyesno("确认发布", 
                                   f"确定要执行版本发布流程吗？\n\n{version_text}"):
            return
        
        # 启动执行线程
        self.is_running = True
        self.execute_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.simulate_btn.config(state=tk.DISABLED)
        
        self.execution_thread = threading.Thread(target=self._execute_release_thread, 
                                               args=(version, date, selected_platforms))
        self.execution_thread.daemon = True
        self.execution_thread.start()
    
    def _execute_release_thread(self, version, date, selected_platforms):
        """执行发布流程的线程"""
        try:
            self.log("=" * 50, 'info')
            self.log("开始执行版本发布流程...", 'info')
            self.log(f"版本: {version}, 日期: {date}", 'info')
            self.log(f"选择的平台: {selected_platforms}", 'info')
            
            # 步骤1: 处理已存在的版本文件夹
            self.root.after(0, lambda: self.progress_var.set(5))
            self.root.after(0, lambda: self.progress_text.config(text="检查版本文件夹..."))
            
            existing_folders = []
            for file in os.listdir('./'):
                if re.match(r'^灵犀·晓伴.*--.*', file):
                    existing_folders.append(file)
            
            if existing_folders:
                self.log(f"发现已存在的版本文件夹: {existing_folders}", 'warning')
                
                option = self.main_folder_var.get()
                for folder in existing_folders:
                    if option == 'delete':
                        try:
                            subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', folder], 
                                          shell=True, check=True)
                            self.log(f"已删除版本文件夹: {folder}", 'success')
                        except Exception as e:
                            self.log(f"删除文件夹失败: {folder}, 错误: {e}", 'error')
                            raise
                    elif option == 'rename':
                        counter = 1
                        while True:
                            new_name = f"{folder}_old{counter}"
                            if not os.path.exists(new_name):
                                os.rename(folder, new_name)
                                self.log(f"已重命名: {folder} -> {new_name}", 'success')
                                break
                            counter += 1
                    else:  # skip
                        self.log(f"跳过版本文件夹: {folder}", 'info')
            else:
                self.log("未发现已存在的版本文件夹", 'info')
            
            # 步骤2: 处理upgrade_package文件夹
            self.root.after(0, lambda: self.progress_var.set(10))
            self.root.after(0, lambda: self.progress_text.config(text="处理upgrade_package文件夹..."))
            
            upgrade_option = self.upgrade_folder_var.get()
            if upgrade_option == 'clear' and os.path.exists(self.uppath):
                try:
                    subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', 'upgrade_package'], 
                                  shell=True, check=True)
                    os.mkdir(self.uppath)
                    self.log("已清空upgrade_package文件夹", 'success')
                except Exception as e:
                    self.log(f"清空upgrade_package文件夹失败: {e}", 'error')
                    raise
            
            # 确保upgrade_package文件夹存在
            if not os.path.exists(self.uppath):
                os.mkdir(self.uppath)
                self.log("创建upgrade_package文件夹", 'success')
            
            # 步骤3: 创建版本文件夹结构
            self.root.after(0, lambda: self.progress_var.set(15))
            self.root.after(0, lambda: self.progress_text.config(text="创建文件夹结构..."))
            
            new_dir_name = f"灵犀·晓伴_{version} --{date}"
            os.mkdir(new_dir_name)
            self.log(f"创建主文件夹: {new_dir_name}", 'success')
            
            mac_dir_name = f"灵犀·晓伴 {version} mac"
            win_dir_name = f"灵犀·晓伴 {version} win"
            linux_dir_name = f"灵犀·晓伴 {version} 统信+麒麟"
            
            os.mkdir(os.path.join(new_dir_name, mac_dir_name))
            os.mkdir(os.path.join(new_dir_name, win_dir_name))
            os.mkdir(os.path.join(new_dir_name, linux_dir_name))
            
            self.log("创建平台子文件夹: mac, win, 统信+麒麟", 'success')
            
            # 步骤4-8: 复制各平台安装包
            new_date = date[-4:]  # 取后四位
            total_steps = 5 + len(selected_platforms)
            current_step = 3
            
            def update_progress(percent, message):
                self.root.after(0, lambda: self.progress_var.set(percent))
                self.root.after(0, lambda: self.progress_text.config(text=message))
                self.log(message, 'info')
            
            # 处理各平台
            platforms = {
                'linux-arm64': ('linux', 'linux-arm64', linux_dir_name),
                'linux-x64': ('linux', 'linux-x64', linux_dir_name),
                'mac-arm64': ('mac', 'mac-arm64', mac_dir_name),
                'mac-x64': ('mac', 'mac-intel-x64', mac_dir_name),
                'win-x64': ('win', 'win-x64', win_dir_name),
            }
            
            for i, platform in enumerate(selected_platforms, 1):
                if not self.is_running:
                    break
                
                progress = 20 + (i / len(selected_platforms)) * 50
                platform_type, arch, target_dir = platforms[platform]
                
                if platform == 'win-x64':
                    # Windows特殊处理
                    update_progress(progress, f"处理 Windows x64 安装包...")
                    
                    win_files = self.get_suxiaoban_setup_files(self.pkgpath)
                    if win_files:
                        win_version = re.findall(r'\d+\.\d+\.\d+', win_files[0])[0]
                        self.log(f"Windows安装包版本: {win_version}", 'info')
                        
                        new_win_x64 = f"灵犀·晓伴-{win_version}-标准版-{new_date}-win-x64.zip"
                        source = os.path.join(self.pkgpath, win_files[0])
                        
                        # 检查目标文件是否已存在
                        target = os.path.join(new_dir_name, target_dir, new_win_x64)
                        if os.path.exists(target):
                            self.log(f"警告: 目标文件已存在: {new_win_x64}", 'warning')
                            continue
                        
                        if self.safe_copy(source, target):
                            self.log(f"复制Windows安装包: {new_win_x64}", 'success')
                        
                        # 升级包
                        new2_win_x64 = f"gerenzhushou-{win_version}-standard-win32-x64.zip"
                        if self.safe_copy(source, os.path.join(self.uppath, new2_win_x64)):
                            self.log(f"生成Windows升级包: {new2_win_x64}", 'success')
                    else:
                        self.log(f"警告: 未找到Windows安装包", 'warning')
                else:
                    # Linux/Mac处理
                    pkg_pattern = f'pkg-{arch}'
                    update_progress(progress, f"处理 {arch} 安装包...")
                    
                    for file in os.listdir(self.pkgpath):
                        if os.path.isdir(os.path.join(self.pkgpath, file)) and re.match(f'^{pkg_pattern}.*', file):
                            # 发布包
                            new_filename = f"灵犀·晓伴-{version}-标准版-{new_date}-{arch}.zip"
                            source = os.path.join(self.pkgpath, file, "灵犀·晓伴.zip")
                            target = os.path.join(new_dir_name, target_dir, new_filename)
                            
                            if os.path.exists(source):
                                if self.safe_copy(source, target):
                                    self.log(f"复制安装包: {new_filename}", 'success')
                            else:
                                self.log(f"警告: 源文件不存在: {source}", 'warning')
                                continue
                            
                            # 升级包
                            if arch.startswith('mac'):
                                upgrade_arch = arch.replace('mac-', 'darwin-')
                            else:
                                upgrade_arch = arch
                            
                            upgrade_filename = f"gerenzhushou-{version}-standard-{upgrade_arch}.zip"
                            if self.safe_copy(source, os.path.join(self.uppath, upgrade_filename)):
                                self.log(f"生成升级包: {upgrade_filename}", 'success')
                            break
            
            # 步骤9: 复制帮助文档
            if self.is_running:
                self.root.after(0, lambda: self.progress_var.set(80))
                self.root.after(0, lambda: self.progress_text.config(text="复制帮助文档..."))
                
                # 通用帮助文档
                help_files = [
                    ("苏晓伴桌面版帮助说明.docx", [mac_dir_name, win_dir_name, linux_dir_name]),
                    ("苏晓伴 mac 版安装说明.docx", [mac_dir_name]),
                    ("国产电脑使用苏晓伴说明.docx", [linux_dir_name]),
                ]
                
                for help_file, target_dirs in help_files:
                    source = os.path.join(self.helppath, help_file)
                    if os.path.exists(source):
                        for target_dir in target_dirs:
                            target = os.path.join(new_dir_name, target_dir, help_file)
                            if self.safe_copy(source, target):
                                self.log(f"复制帮助文档: {help_file} -> {target_dir}", 'success')
                    else:
                        self.log(f"警告: 帮助文档不存在: {help_file}", 'warning')
                
                # 复制releases.json
                releases_source = os.path.join(self.helppath, "releases.json")
                if os.path.exists(releases_source):
                    if self.safe_copy(releases_source, os.path.join(self.uppath, "releases.json")):
                        self.log("复制releases.json配置文件", 'success')
            
            # 完成
            if self.is_running:
                self.root.after(0, lambda: self.progress_var.set(100))
                self.root.after(0, lambda: self.progress_text.config(text="发布完成！"))
                self.log("=" * 50, 'success')
                self.log("版本发布流程执行完成！", 'success')
                
                self.root.after(0, lambda: self.check_system_status())
                self.root.after(0, lambda: messagebox.showinfo("完成", "版本发布流程已成功完成！"))
            
        except Exception as e:
            self.log(f"执行过程中发生错误: {e}", 'error')
            self.root.after(0, lambda: messagebox.showerror("错误", f"执行失败: {e}"))
            self.root.after(0, lambda: self.progress_var.set(0))
            self.root.after(0, lambda: self.progress_text.config(text="执行失败"))
        
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.execute_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.simulate_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_bar.config(text="就绪"))
    
    def simulate_release(self):
        """模拟运行"""
        self.log("开始模拟运行...", 'info')
        
        steps = [
            "检查package文件夹...",
            "检查已存在的版本文件夹...",
            f"创建主文件夹: 灵犀·晓伴_{self.version_entry.get()} --{self.date_entry.get()}",
            "创建平台子文件夹...",
            "复制安装包...",
            "生成升级包...",
            "复制帮助文档...",
            "复制配置文件...",
            "模拟完成: 所有操作成功"
        ]
        
        for i, step in enumerate(steps):
            if not self.is_running:
                break
            self.log(f"[模拟] {step}", 'info')
            self.progress_var.set((i + 1) / len(steps) * 100)
            self.root.update()
            self.root.after(300, lambda: None)
            self.root.update()
        
        self.log("模拟运行完成", 'success')
        self.progress_var.set(0)
        self.progress_text.config(text="准备就绪")
    
    def stop_execution(self):
        """停止执行"""
        if self.is_running:
            self.is_running = False
            self.log("正在停止执行...", 'warning')
            messagebox.showinfo("提示", "已发送停止指令，请等待当前操作完成...")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete('1.0', tk.END)
        self.log("日志已清空", 'info')
    
    def export_log(self):
        """导出日志"""
        log_content = self.log_text.get('1.0', tk.END)
        filename = f"发布日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(log_content)
            self.log(f"日志已导出到: {filename}", 'success')
            messagebox.showinfo("成功", f"日志已导出到:\n{filename}")
        except Exception as e:
            self.log(f"导出日志失败: {e}", 'error')
            messagebox.showerror("错误", f"导出日志失败: {e}")


def main():
    """主函数"""
    # 启用DPI感知
    enable_dpi_awareness()
    
    root = tk.Tk()
    app = ReleaseSystemGUI(root)
    
    # 更新概要
    def on_input_change(event):
        app.update_summary()
    
    app.version_entry.bind('<KeyRelease>', on_input_change)
    app.date_entry.bind('<KeyRelease>', on_input_change)
    
    # 添加快捷键
    root.bind('<Control-q>', lambda e: root.quit())
    root.bind('<F5>', lambda e: app.check_system_status())
    root.bind('<Control-r>', lambda e: app.execute_release())
    
    root.mainloop()


if __name__ == "__main__":
    main()
