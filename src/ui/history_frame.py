import customtkinter as ctk
from datetime import datetime
import sqlite3

class HistoryFrame(ctk.CTkFrame):
    def __init__(self, parent, return_callback):
        super().__init__(parent)
        self.return_callback = return_callback
        self.setup_ui()
        self.load_history()
        
    def setup_ui(self):
        # 顶部导航栏
        nav_frame = ctk.CTkFrame(self)
        nav_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            nav_frame,
            text="返回",
            command=self.return_callback,
            width=80
        ).pack(side="left")
        
        ctk.CTkLabel(
            nav_frame,
            text="运动历史",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left", padx=20)
        
        # 添加导出按钮
        export_button = ctk.CTkButton(
            nav_frame,
            text="导出数据",
            command=self.export_data,
            width=100
        )
        export_button.pack(side="right", padx=10)
        
        # 筛选区域
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        # 时间范围选择
        ctk.CTkLabel(
            filter_frame,
            text="时间范围:"
        ).pack(side="left", padx=5)
        
        self.time_var = ctk.StringVar(value="全部")
        time_options = ["全部", "今天", "本周", "本月"]
        
        time_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=time_options,
            variable=self.time_var,
            command=self.filter_changed
        )
        time_menu.pack(side="left", padx=5)
        
        # 运动类型选择
        ctk.CTkLabel(
            filter_frame,
            text="运动类型:"
        ).pack(side="left", padx=5)
        
        self.type_var = ctk.StringVar(value="全部")
        type_options = ["全部", "深蹲", "俯卧撑", "平板支撑", "跳绳"]
        
        type_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=type_options,
            variable=self.type_var,
            command=self.filter_changed
        )
        type_menu.pack(side="left", padx=5)
        
        # 历史记录列表
        self.history_frame = ctk.CTkScrollableFrame(self)
        self.history_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
    def load_history(self):
        # 清空现有内容
        for widget in self.history_frame.winfo_children():
            widget.destroy()
            
        # 从数据库加载数据
        conn = sqlite3.connect('exercise_data.db')
        cursor = conn.cursor()
        
        # 构建查询条件
        where_clause = []
        params = []
        
        if self.time_var.get() != "全部":
            if self.time_var.get() == "今天":
                where_clause.append("date(timestamp) = date('now')")
            elif self.time_var.get() == "本周":
                where_clause.append("date(timestamp) >= date('now', 'weekday 0', '-7 days')")
            elif self.time_var.get() == "本月":
                where_clause.append("date(timestamp) >= date('now', 'start of month')")
                
        if self.type_var.get() != "全部":
            where_clause.append("exercise_type = ?")
            params.append(self.type_var.get())
            
        query = "SELECT * FROM exercise_records"
        if where_clause:
            query += " WHERE " + " AND ".join(where_clause)
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # 显示记录
        for record in records:
            self.create_history_item(record)
            
        conn.close()
        
    def create_history_item(self, record):
        # 创建记录项容器
        item = ctk.CTkFrame(self.history_frame)
        item.pack(fill="x", pady=5)
        
        # 时间
        time_str = datetime.fromisoformat(record[1]).strftime("%Y-%m-%d %H:%M")
        ctk.CTkLabel(
            item,
            text=time_str,
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=10)
        
        # 运动类型
        ctk.CTkLabel(
            item,
            text=record[2],
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)
        
        # 运动数据
        if record[2] == "平板支撑":
            data_text = f"坚持时间: {record[3]}秒"
        else:
            data_text = f"完成次数: {record[3]}次"
            
        ctk.CTkLabel(
            item,
            text=data_text
        ).pack(side="left", padx=10)
        
    def filter_changed(self, _):
        self.load_history() 
        
    def export_data(self):
        """导出运动数据为CSV文件"""
        from tkinter import filedialog
        import csv
        from datetime import datetime
        
        # 选择保存位置
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv")],
            initialfile=f"运动记录_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if not filename:
            return
        
        try:
            # 获取数据
            conn = sqlite3.connect('exercise_data.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, exercise_type, count_or_duration 
                FROM exercise_records 
                ORDER BY timestamp DESC
            """)
            records = cursor.fetchall()
            conn.close()
            
            # 写入CSV文件
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["时间", "运动类型", "次数/时长(秒)"])
                for record in records:
                    timestamp = datetime.fromisoformat(record[0]).strftime("%Y-%m-%d %H:%M:%S")
                    writer.writerow([timestamp, record[1], record[2]])
                
            # 显示成功消息
            self.show_message("数据导出成功！")
            
        except Exception as e:
            self.show_message(f"导出失败: {str(e)}", "error")
        
    def show_message(self, message, level="info"):
        """显示提示消息"""
        colors = {
            "info": "#4ECDC4",
            "error": "#FF6B6B"
        }
        
        msg_frame = ctk.CTkFrame(
            self,
            fg_color=colors.get(level, "#4ECDC4")
        )
        msg_frame.place(relx=0.5, rely=0.1, anchor="center")
        
        ctk.CTkLabel(
            msg_frame,
            text=message,
            text_color="#ffffff",
            font=ctk.CTkFont(size=14)
        ).pack(padx=20, pady=10)
        
        # 3秒后自动消失
        self.after(3000, msg_frame.destroy) 