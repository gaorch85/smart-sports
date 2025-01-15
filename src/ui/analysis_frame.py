import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)

class AnalysisFrame(ctk.CTkFrame):
    def __init__(self, parent, return_callback):
        super().__init__(parent)
        self.return_callback = return_callback
        self.setup_ui()
        
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
            text="数据分析",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left", padx=20)
        
        # 控制区域
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # 图表类型选择
        ctk.CTkLabel(
            control_frame,
            text="图表类型:"
        ).pack(side="left", padx=5)
        
        self.chart_var = ctk.StringVar(value="趋势图")
        chart_options = ["趋势图", "统计图", "对比图"]
        
        chart_menu = ctk.CTkOptionMenu(
            control_frame,
            values=chart_options,
            variable=self.chart_var,
            command=self.update_chart
        )
        chart_menu.pack(side="left", padx=5)
        
        # 时间范围选择
        ctk.CTkLabel(
            control_frame,
            text="时间范围:"
        ).pack(side="left", padx=5)
        
        self.time_var = ctk.StringVar(value="最近7天")
        time_options = ["最近7天", "最近30天", "最近90天"]
        
        time_menu = ctk.CTkOptionMenu(
            control_frame,
            values=time_options,
            variable=self.time_var,
            command=self.update_chart
        )
        time_menu.pack(side="left", padx=5)
        
        # 添加运动类型选择
        ctk.CTkLabel(
            control_frame,
            text="运动类型:"
        ).pack(side="left", padx=5)
        
        self.exercise_var = ctk.StringVar(value="全部")
        exercise_options = ["全部", "深蹲", "俯卧撑", "平板支撑", "跳绳"]
        
        exercise_menu = ctk.CTkOptionMenu(
            control_frame,
            values=exercise_options,
            variable=self.exercise_var,
            command=self.update_chart
        )
        exercise_menu.pack(side="left", padx=5)
        
        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False     # 用来正常显示负号
        
        # 图表显示区域
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 定义全局颜色方案
        self.color_scheme = {
            "深蹲": "#FF6B6B",    # 红色
            "俯卧撑": "#4ECDC4",  # 青色
            "平板支撑": "#45B7D1", # 蓝色
            "跳绳": "#FFB347",    # 橙色
            "总计": "#98D8AA",    # 绿色
            "平均": "#4A90E2"     # 蓝色
        }
        
        # 初始显示图表
        self.update_chart()
        
    def update_chart(self, _=None):
        # 清空现有图表
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        # 获取数据
        data = self.get_chart_data()
        
        if not data:  # 如果没有数据
            self.show_no_data_message()
            return
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        # 设置样式
        ax.spines['bottom'].set_color('#666666')
        ax.spines['top'].set_color('#666666') 
        ax.spines['right'].set_color('#666666')
        ax.spines['left'].set_color('#666666')
        ax.tick_params(colors='#666666')
        ax.yaxis.label.set_color('#666666')
        ax.xaxis.label.set_color('#666666')
        ax.title.set_color('#666666')
        
        # 根据图表类型绘制
        if self.chart_var.get() == "趋势图":
            self.draw_trend_chart(ax, data)
        elif self.chart_var.get() == "统计图":
            self.draw_stats_chart(ax, data)
        else:
            self.draw_comparison_chart(ax, data)
            
        # 调整布局
        plt.tight_layout()
        
        # 显示图表
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def get_chart_data(self):
        conn = sqlite3.connect('exercise_data.db')
        cursor = conn.cursor()
        
        # 确定时间范围
        days = 7
        if self.time_var.get() == "最近30天":
            days = 30
        elif self.time_var.get() == "最近90天":
            days = 90
            
        start_date = datetime.now() - timedelta(days=days)
        
        # 构建查询条件
        where_clause = ["timestamp >= ?"]
        params = [start_date.isoformat()]
        
        # 添加运动类型筛选
        if self.exercise_var.get() != "全部":
            where_clause.append("exercise_type = ?")
            params.append(self.exercise_var.get())
        
        # 查询数据
        query = f"""
            SELECT exercise_type, timestamp, count_or_duration 
            FROM exercise_records 
            WHERE {' AND '.join(where_clause)}
            ORDER BY timestamp
        """
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        
        return data
        
    def draw_trend_chart(self, ax, data):
        try:
            # 按运动类型和日期分组数据
            exercise_data = {}
            for exercise, timestamp, value in data:
                try:
                    date = datetime.fromisoformat(timestamp).date()
                    if exercise not in exercise_data:
                        exercise_data[exercise] = {}
                    if date not in exercise_data[exercise]:
                        exercise_data[exercise][date] = []
                    exercise_data[exercise][date].append(value)
                except Exception as e:
                    logger.error(f"日期处理错误: {str(e)}")
                    continue
            
            if not exercise_data:  # 如果没有有效数据
                return
            
            # 获取整体的日期范围
            all_dates = set()
            for dates_data in exercise_data.values():
                all_dates.update(dates_data.keys())
            if not all_dates:  # 如果没有有效日期
                return
            
            date_range = sorted(all_dates)
            
            # 绘制每种运动的趋势线
            for exercise, dates_data in exercise_data.items():
                try:
                    # 对每天的数据进行聚合
                    aggregated_data = {
                        date: {
                            'total': sum(values),
                            'count': len(values),
                            'avg': sum(values) / len(values)
                        }
                        for date, values in dates_data.items()
                    }
                    
                    # 排序日期
                    sorted_dates = sorted(dates_data.keys())
                    
                    # 根据运动类型选择合适的数据表示
                    if exercise == "平板支撑":
                        # 平板支撑使用当天最长时间
                        values = [max(dates_data[date]) for date in sorted_dates]
                        ylabel = "时长(秒)"
                    else:
                        # 其他运动使用当天总次数
                        values = [aggregated_data[date]['total'] for date in sorted_dates]
                        ylabel = "次数"
                    
                    if values:  # 确保有数据再绘制
                        # 使用移动平均平滑曲线
                        if len(values) > 3:
                            values = np.convolve(values, np.ones(3)/3, mode='valid')
                            plot_dates = sorted_dates[1:-1]  # 相应调整日期
                        else:
                            plot_dates = sorted_dates
                        
                        ax.plot(plot_dates, values,
                               label=exercise,
                               color=self.color_scheme[exercise],
                               marker='o',
                               linewidth=2,
                               markersize=6)
                
                except Exception as e:
                    logger.error(f"绘制{exercise}趋势线错误: {str(e)}")
                    continue
            
            # 设置图表属性
            ax.set_title("运动趋势分析")
            ax.set_xlabel("日期")
            ax.set_ylabel(ylabel)
            ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
            ax.grid(True, color='#666666', alpha=0.3)
            
            # 设置合适的日期范围
            if date_range:
                ax.set_xlim(min(date_range), max(date_range))
            
            # 优化日期显示
            ax.xaxis.set_major_locator(plt.AutoLocator())
            ax.xaxis.set_major_formatter(plt.DateFormatter('%Y-%m-%d'))
            plt.xticks(rotation=45)
            
        except Exception as e:
            logger.error(f"绘制趋势图错误: {str(e)}")
        
    def draw_stats_chart(self, ax, data):
        # 统计每种运动的总次数/时长和平均值
        stats = {}
        for exercise, _, value in data:
            if exercise not in stats:
                stats[exercise] = {"total": 0, "count": 0}
            stats[exercise]["total"] += value
            stats[exercise]["count"] += 1
        
        exercises = list(stats.keys())
        totals = [stats[ex]["total"] for ex in exercises]
        averages = [stats[ex]["total"]/stats[ex]["count"] for ex in exercises]
        
        x = np.arange(len(exercises))
        width = 0.35
        
        # 创建双柱状图
        ax.bar(x - width/2, totals, width, label='总计', color='#FF6B6B')
        ax.bar(x + width/2, averages, width, label='平均', color='#4ECDC4')
        
        ax.set_title("运动统计分析")
        ax.set_xticks(x)
        ax.set_xticklabels(exercises)
        ax.legend()
        
        # 添加数值标签
        for i, v in enumerate(totals):
            ax.text(i - width/2, v, str(int(v)), ha='center', va='bottom')
        for i, v in enumerate(averages):
            ax.text(i + width/2, v, f"{v:.1f}", ha='center', va='bottom')
        
    def draw_comparison_chart(self, ax, data):
        # 按周统计数据
        weekly_stats = {}
        for exercise, timestamp, value in data:
            date = datetime.fromisoformat(timestamp).date()
            week_start = date - timedelta(days=date.weekday())
            if week_start not in weekly_stats:
                weekly_stats[week_start] = {}
            if exercise not in weekly_stats[week_start]:
                weekly_stats[week_start][exercise] = 0
            weekly_stats[week_start][exercise] += value
        
        # 准备数据
        weeks = sorted(weekly_stats.keys())
        exercises = sorted(set([ex for w in weekly_stats.values() for ex in w.keys()]))
        
        # 创建堆叠柱状图
        bottom = np.zeros(len(weeks))
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for exercise, color in zip(exercises, colors):
            values = [weekly_stats[w].get(exercise, 0) for w in weeks]
            ax.bar(weeks, values, bottom=bottom, label=exercise, color=color)
            bottom += values
        
        ax.set_title("每周运动对比")
        ax.set_xlabel("周次")
        ax.set_ylabel("运动量")
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        # 自动旋转日期标签
        plt.xticks(rotation=45)
        
    def show_no_data_message(self):
        """显示无数据提示"""
        msg_frame = ctk.CTkFrame(self.chart_frame)
        msg_frame.pack(expand=True)
        
        ctk.CTkLabel(
            msg_frame,
            text="暂无数据",
            font=ctk.CTkFont(size=24)
        ).pack(pady=50) 