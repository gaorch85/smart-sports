import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
import cv2
from PIL import Image, ImageTk
import pyttsx3
import threading
from queue import Queue
from ..exercises.squat_counter import SquatCounter
from ..core.pose_detector import PoseDetector
from ..exercises.pushup_counter import PushupCounter
from ..exercises.plank_counter import PlankCounter
import customtkinter as ctk
from ..core.database import db_manager
import logging
import os
import numpy as np
import time

logger = logging.getLogger(__name__)

class ExerciseFrame(ctk.CTkFrame):
    def __init__(self, parent, exercise_name, return_callback):
        super().__init__(parent)
        self.exercise_name = exercise_name
        self.return_callback = return_callback
        self.window = parent
        
        # 初始化基本变量
        self.pose_detector = PoseDetector()
        self.exercise_counter = None
        self.is_running = False
        self.cap = None
        self.last_count = 0
        
        # 初始化语音系统（只初始化一次）
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.speech_queue = Queue()
        self.current_speech = None
        self.speech_thread = None
        self.start_speech_thread()
        
        self.setup_ui()

    def start_speech_thread(self):
        """启动语音线程"""
        def speech_worker():
            while True:
                try:
                    text = self.speech_queue.get()
                    if text is None:  # 退出信号
                        break
                    
                    # 播报消息
                    self.engine.say(text)
                    self.engine.runAndWait()
                    
                except Exception as e:
                    logger.error(f"语音播报错误: {str(e)}")
                    continue
        
        self.speech_thread = threading.Thread(target=speech_worker, daemon=True)
        self.speech_thread.start()

    def speak(self, text):
        """将语音文本加入队列"""
        if text and self.speech_queue:
            # 如果是结束播报，清空队列
            if text.startswith("运动结束"):
                while not self.speech_queue.empty():
                    try:
                        self.speech_queue.get_nowait()
                    except:
                        pass
            self.speech_queue.put(text)

    def cleanup(self):
        """清理资源"""
        self.is_running = False
        
        # 释放摄像头资源
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        
        # 清理语音系统
        if self.speech_queue:
            # 清空队列
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                except:
                    pass
            # 发送退出信号
            self.speech_queue.put(None)
        
        # 等待语音线程结束
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=1)

    def on_return(self):
        """返回主界面"""
        # 停止运动
        if self.is_running:
            self.stop_exercise()
        
        # 立即停止语音播报
        try:
            self.engine.stop()
        except:
            pass
        
        # 清空语音队列
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except:
                pass
        
        # 清理资源
        self.cleanup()
        
        # 返回主界面
        self.return_callback()

    def stop_exercise(self):
        """停止运动"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # 立即更新界面状态
        self.control_button.configure(text="开始训练")
        self.video_label.configure(image='')
        
        # 计算运动时长（秒）
        exercise_time = int(time.time() - self.start_time) if hasattr(self, 'start_time') else 0
        
        # 准备结束信息
        if self.exercise_counter:
            if isinstance(self.exercise_counter, PlankCounter):
                duration = self.exercise_counter.total_time
                if duration > 0:
                    db_manager.save_exercise_record(
                        self.exercise_name, 
                        duration,
                        duration  # 平板支撑的运动时长就是持续时间
                    )
                end_message = f"运动结束，本次{self.exercise_name}，" + (
                    f"您坚持了{duration}秒" if duration > 0 
                    else "未完成有效记录"
                )
            else:
                count = self.exercise_counter.counter
                if count > 0:  # 只有完成有效运动才记录时长
                    db_manager.save_exercise_record(
                        self.exercise_name, 
                        count,
                        exercise_time
                    )
                end_message = f"运动结束，本次{self.exercise_name}，" + (
                    f"您完成了{count}个" if count > 0 
                    else "未完成有效记录"
                )
            
            # 播报结束信息
            self.speak(end_message)

    def setup_ui(self):
        # 顶部导航栏
        nav_frame = ctk.CTkFrame(self)
        nav_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            nav_frame,
            text="返回",
            command=self.on_return,
            width=80
        ).pack(side="left", padx=10)
        
        ctk.CTkLabel(
            nav_frame,
            text=self.exercise_name,
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(side="left", padx=20)
        
        # 主要内容区域
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 设置列宽比例 (摄像头:信息 = 8:2)
        content_frame.grid_columnconfigure(0, weight=8)
        content_frame.grid_columnconfigure(1, weight=2)
        
        # 先获取摄像头实际分辨率
        test_cap = cv2.VideoCapture(0)
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret:
                frame_h, frame_w = frame.shape[:2]
                # 设置一个合适的缩放比例，确保不会太大
                scale = min(700 / frame_w, 500 / frame_h)
                container_w = int(frame_w * scale)
                container_h = int(frame_h * scale)
            else:
                container_w, container_h = 640, 480  # 默认尺寸
            test_cap.release()
        else:
            container_w, container_h = 640, 480  # 默认尺寸
        
        # 左侧视频显示
        video_frame = ctk.CTkFrame(
            content_frame,
            fg_color="#2b2b2b",
            border_width=2,
            border_color="#3f3f3f",
            width=800,
            height=600
        )
        video_frame.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        video_frame.grid_propagate(False)  # 保持固定大小
        
        self.video_label = ctk.CTkLabel(
            video_frame,
            text="准备开始运动\n请站在合适位置",  # 恢复初始文本
            font=ctk.CTkFont(size=16)
        )
        self.video_label.place(relx=0.5, rely=0.5, anchor="center")  # 使用place而不是pack
        
        # 右侧信息显示
        info_frame = ctk.CTkFrame(content_frame)
        info_frame.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        
        # 计数显示
        counter_frame = ctk.CTkFrame(
            info_frame,
            fg_color="#1a1a1a",
            corner_radius=15
        )
        counter_frame.pack(fill="x", pady=20, padx=15)
        
        self.counter_label = ctk.CTkLabel(
            counter_frame,
            text="0",
            font=ctk.CTkFont(size=48, weight="bold")
        )
        self.counter_label.pack(pady=20)
        
        # 控制按钮
        self.control_button = ctk.CTkButton(
            info_frame,
            text="开始运动",
            command=self.toggle_exercise,
            font=ctk.CTkFont(size=18, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        self.control_button.pack(pady=30, padx=15, fill="x")

    def start_exercise(self):
        """开始新的运动"""
        if self.exercise_name == "深蹲":
            self.exercise_counter = SquatCounter()
            self.speak(f"开始{self.exercise_name}训练，请站在距离摄像头2米左右的位置，正面朝向摄像头，确保下半身在画面中")
        elif self.exercise_name == "俯卧撑":
            self.exercise_counter = PushupCounter()
            self.speak("开始俯卧撑训练，请将摄像头放置在侧面位置，确保全身在画面中")
        elif self.exercise_name == "平板支撑":
            self.exercise_counter = PlankCounter()
            self.speak("开始平板支撑训练，请将摄像头放置在侧面位置，确保全身在画面中")
        elif self.exercise_name == "跳绳":
            from ..exercises.rope_counter import RopeCounter
            self.exercise_counter = RopeCounter()
            self.speak(f"开始{self.exercise_name}训练，请站在距离摄像头3米左右的位置，正面朝向摄像头，确保全身在画面中")
            
    def toggle_exercise(self):
        """切换运动状态"""
        if self.is_running:
            self.stop_exercise()
        else:
            # 先检查摄像头
            if not self.check_camera():
                self.show_camera_error()
                return
            
            # 立即停止当前播报
            try:
                self.engine.stop()
            except:
                pass
            
            # 清空语音队列
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                except:
                    pass
            
            self.start_time = time.time()  # 记录开始时间
            self.start_exercise()
            self.start_camera()
            self.control_button.configure(text="停止运动")

    def check_camera(self):
        """检查摄像头是否可用"""
        try:
            if os.name == 'nt':  # Windows系统
                try:
                    import comtypes.client
                    # 创建 System.Device.DeviceManager
                    device_manager = comtypes.client.CreateObject("SystemDeviceManager")
                    # 获取视频设备
                    devices = device_manager.VideoInputDevices
                    if len(devices) == 0:
                        return False
                    return True
                except:
                    # 如果 COM 接口失败，回退到传统方法
                    pass
                
            # 对于其他系统或 COM 接口失败的情况，使用快速检查方法
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return False
            cap.release()
            return True
            
        except Exception as e:
            logger.error(f"摄像头检查错误: {str(e)}")
            return False

    def show_camera_error(self):
        """显示摄像头错误对话框"""
        dialog = ctk.CTkDialog(
            title="摄像头错误",
            text="未检测到可用的摄像头设备，请检查：\n\n1. 摄像头是否正确连接\n2. 是否已授予摄像头权限\n3. 是否有其他程序正在使用摄像头",
        )
        dialog.get_input()  # 等待用户确认

    def start_camera(self):
        """启动摄像头"""
        # 清空之前的显示
        self.video_label.configure(text="")
        
        # 打开摄像头
        self.cap = cv2.VideoCapture(0)
        
        # 等待摄像头预热
        self.window.after(1000, self.camera_ready)

    def camera_ready(self):
        """摄像头准备就绪"""
        self.is_running = True
        self.control_button.configure(
            text="停止",
            fg_color="#E74C3C"
        )
        
        self.person_detected = False
        self.update_frame()
        
    def update_frame(self):
        """更新视频帧"""
        if self.is_running and self.cap and self.exercise_counter:
            ret, frame = self.cap.read()
            if ret:
                # 姿势检测
                results, processed_frame = self.pose_detector.detect(frame)
                processed_frame = self.pose_detector.draw_landmarks(processed_frame, results)
                
                # 运动计数
                if results.pose_landmarks:
                    if not self.person_detected:
                        self.person_detected = True
                        self.speak("已检测到人体，请开始运动")
                        
                    if isinstance(self.exercise_counter, PlankCounter):
                        # 平板支撑特殊处理
                        result = self.exercise_counter.process_pose(
                            results.pose_landmarks.landmark
                        )
                        
                        # 更新计数显示（使用 calculate_time 方法）
                        current_time = self.exercise_counter.calculate_time()
                        self.counter_label.configure(
                            text=f"{current_time}"
                        )
                        
                        # 只在需要时播报时间
                        if result[2]:  # should_announce
                            self.speak(f"已坚持{current_time}秒")
                            
                        # 如果需要停止，自动点击停止按钮
                        if result[3]:  # should_stop
                            self.stop_exercise()
                            return
                            
                    else:
                        # 其他运动的处理
                        self.exercise_counter.process_pose(
                            results.pose_landmarks.landmark
                        )
                        
                        # 更新计数显示
                        current_count = self.exercise_counter.counter
                        self.counter_label.configure(
                            text=f"{current_count}"
                        )
                        
                        # 如果计数增加，播放语音提示
                        if current_count > self.last_count:
                            self.speak(f"完成第{current_count}个")
                            self.last_count = current_count
                
                # 显示图像
                frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                
                # 保持固定的容器大小
                container_w, container_h = 800, 600
                
                # 简单的缩放，保持宽高比
                frame = cv2.resize(frame, (container_w, container_h))
                
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image=image)
                self.video_label.configure(image=photo)
                self.video_label.image = photo
                
                self.after(10, self.update_frame)

    def update_ui_for_exercise_state(self, state="ready"):
        """更新UI状态"""
        if state == "ready":
            # 准备开始状态
            self.video_label.configure(
                text="准备开始运动\n请站在合适位置",
                font=ctk.CTkFont(size=16)
            )
            self.control_button.configure(
                text="开始运动",
                fg_color="#4CAF50",
                hover_color="#45a049"
            )
        elif state == "running":
            # 运动中状态
            self.control_button.configure(
                text="停止运动",
                fg_color="#E74C3C",
                hover_color="#c0392b"
            )
        elif state == "finished":
            # 运动结束状态
            self.control_button.configure(
                text="开始新的运动",
                fg_color="#4CAF50",
                hover_color="#45a049"
            )
            # 可以添加一些结束动画或效果

    def __del__(self):
        """析构函数"""
        self.cleanup() 