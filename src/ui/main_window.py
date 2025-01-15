import customtkinter as ctk
from PIL import Image, ImageTk
import os
from .exercise_frame import ExerciseFrame
from .history_frame import HistoryFrame
from .analysis_frame import AnalysisFrame
import sqlite3

class MainWindow:
    def __init__(self):
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 创建主窗口
        self.window = ctk.CTk()
        self.window.title("智能运动")
        self.window.geometry("1024x768")
        
        # 初始化UI
        self.setup_ui()
        self.current_frame = None
        
    def setup_ui(self):
        # 创建主容器
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 顶部标题栏
        self.create_title_bar()
        
        # 运动卡片区域
        self.create_exercise_grid()
        
        # 底部统计栏
        self.create_stats_bar()
        
    def create_title_bar(self):
        title_frame = ctk.CTkFrame(self.main_container)
        title_frame.pack(fill="x", pady=(0, 20))
        
        # 标题
        ctk.CTkLabel(
            title_frame,
            text="智能运动",
            font=ctk.CTkFont(size=32, weight="bold")
        ).pack(side="left", padx=20)
        
        # 右侧按钮组
        buttons_frame = ctk.CTkFrame(title_frame)
        buttons_frame.pack(side="right", padx=20)
        
        # 历史记录按钮
        ctk.CTkButton(
            buttons_frame,
            text="历史记录",
            command=self.show_history_frame
        ).pack(side="left", padx=10)
        
        # 数据分析按钮
        ctk.CTkButton(
            buttons_frame,
            text="数据分析",
            command=self.show_analysis_frame
        ).pack(side="left", padx=10)
        
    def create_exercise_grid(self):
        exercises = [
            {
                "name": "深蹲",
                "description": "锻炼大腿和臀部肌肉的基础动作",
                "color": "#FF6B6B",
                "icon": "🏃"
            },
            {
                "name": "俯卧撑",
                "description": "锻炼胸部、肩部和手臂的经典动作",
                "color": "#4ECDC4",
                "icon": "💪"
            },
            {
                "name": "平板支撑",
                "description": "锻炼核心肌群的静态动作",
                "color": "#45B7D1",
                "icon": "🔥"
            },
            {
                "name": "跳绳",
                "description": "全身性有氧运动，提高心肺功能",
                "color": "#FFB347",
                "icon": "⭕"
            }
        ]
        
        grid_frame = ctk.CTkFrame(self.main_container)
        grid_frame.pack(fill="both", expand=True)
        
        # 配置网格列
        grid_frame.grid_columnconfigure((0, 1), weight=1)
        
        for i, exercise in enumerate(exercises):
            row, col = divmod(i, 2)
            self.create_exercise_card(grid_frame, exercise, row, col)
            
    def create_exercise_card(self, parent, exercise, row, col):
        # 创建卡片容器
        card = ctk.CTkFrame(
            parent,
            corner_radius=15,
            fg_color=exercise["color"]
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # 图标和名称容器
        header_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # 图标
        ctk.CTkLabel(
            header_frame,
            text=exercise["icon"],
            font=ctk.CTkFont(size=48)
        ).pack(side="left", padx=10)
        
        # 名称
        ctk.CTkLabel(
            header_frame,
            text=exercise["name"],
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left", padx=10)
        
        # 描述文本
        ctk.CTkLabel(
            card,
            text=exercise["description"],
            wraplength=250,
            text_color="#ffffff"
        ).pack(pady=10, padx=20)
        
        # 统计信息
        stats_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        # 从数据库获取统计信息
        try:
            conn = sqlite3.connect('exercise_data.db')
            cursor = conn.cursor()
            
            # 今日次数（使用 count_or_duration 的总和）
            cursor.execute("""
                SELECT SUM(count_or_duration) FROM exercise_records 
                WHERE exercise_type = ? AND date(timestamp) = date('now')
            """, (exercise["name"],))
            today_count = cursor.fetchone()[0] or 0
            
            # 累计次数（使用 count_or_duration 的总和）
            cursor.execute("""
                SELECT SUM(count_or_duration) FROM exercise_records 
                WHERE exercise_type = ?
            """, (exercise["name"],))
            total_count = cursor.fetchone()[0] or 0
            
        finally:
            if 'conn' in locals():
                conn.close()
        
        # 显示统计信息
        ctk.CTkLabel(
            stats_frame,
            text=f"今日: {today_count}次",
            text_color="#ffffff"
        ).pack(side="left", padx=10)
        
        ctk.CTkLabel(
            stats_frame,
            text=f"累计: {total_count}次",
            text_color="#ffffff"
        ).pack(side="right", padx=10)
        
        # 开始按钮
        ctk.CTkButton(
            card,
            text="开始训练",
            command=lambda: self.show_exercise_frame(exercise["name"]),
            fg_color="#ffffff",
            text_color=exercise["color"],
            hover_color="#f0f0f0",
            height=40
        ).pack(pady=(10, 20), padx=20)
        
    def create_stats_bar(self):
        stats_frame = ctk.CTkFrame(self.main_container)
        stats_frame.pack(fill="x", pady=(20, 0))
        
        # 修改统计信息标签
        stats = ["今日次数", "今日时长", "累计时长"]
        self.stats_labels = {}
        
        for i, label in enumerate(stats):
            container = ctk.CTkFrame(stats_frame)
            container.pack(side="left", expand=True, padx=10)
            
            ctk.CTkLabel(
                container,
                text=label,
                font=ctk.CTkFont(size=14)
            ).pack()
            
            self.stats_labels[label] = ctk.CTkLabel(
                container,
                text="0",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            self.stats_labels[label].pack()
        
        # 初始更新统计信息
        self.update_stats()
        
    def show_exercise_frame(self, exercise_name):
        # 隐藏主容器
        self.main_container.pack_forget()
        
        # 创建并显示运动界面
        self.current_frame = ExerciseFrame(self.window, exercise_name, self.show_main_frame)
        self.current_frame.pack(fill="both", expand=True)
        
    def show_main_frame(self):
        """返回主界面"""
        # 销毁当前界面
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
            
        # 显示主界面
        self.main_container.pack(fill="both", expand=True)
        
        # 更新统计信息
        self.update_stats()
        
    def show_history_frame(self):
        """显示历史记录界面"""
        # 隐藏主容器
        self.main_container.pack_forget()
        
        # 创建并显示历史记录界面
        self.current_frame = HistoryFrame(
            self.window, 
            self.show_main_frame
        )
        self.current_frame.pack(fill="both", expand=True)
        
    def show_analysis_frame(self):
        """显示数据分析界面"""
        # 隐藏主容器
        self.main_container.pack_forget()
        
        # 创建并显示数据分析界面
        self.current_frame = AnalysisFrame(
            self.window, 
            self.show_main_frame
        )
        self.current_frame.pack(fill="both", expand=True)
        
    def update_stats(self):
        """更新统计信息"""
        conn = sqlite3.connect('exercise_data.db')
        cursor = conn.cursor()
        
        # 获取今日运动次数
        cursor.execute("""
            SELECT COUNT(*) FROM exercise_records 
            WHERE date(timestamp) = date('now')
        """)
        today_count = cursor.fetchone()[0]
        
        # 获取今日运动总时长（秒）
        cursor.execute("""
            SELECT SUM(exercise_time) FROM exercise_records 
            WHERE date(timestamp) = date('now')
        """)
        today_seconds = cursor.fetchone()[0] or 0
        
        # 获取累计运动总时长（秒）
        cursor.execute("""
            SELECT SUM(exercise_time) FROM exercise_records
        """)
        total_seconds = cursor.fetchone()[0] or 0
        
        # 转换为分钟（向上取整）
        today_minutes = (today_seconds + 59) // 60  # 向上取整
        total_minutes = (total_seconds + 59) // 60  # 向上取整
        
        # 更新显示
        self.stats_labels["今日次数"].configure(text=f"{today_count}次")
        self.stats_labels["今日时长"].configure(text=f"{today_minutes}分钟")
        self.stats_labels["累计时长"].configure(text=f"{total_minutes}分钟")
        
        conn.close() 