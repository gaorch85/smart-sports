from ..core.exercise_counter import ExerciseCounter
import numpy as np
from ..core.logger import logger
import time

class RopeCounter(ExerciseCounter):
    def __init__(self):
        super().__init__("跳绳")
        self.stage = "down"
        self.counter = 0
        
        # 存储上一帧的位置信息
        self.last_positions = None
        self.position_buffer = []
        self.buffer_size = 3
        
        # 调整参数
        self.min_height_change = 0.02
        self.min_jump_interval = 0.15
        
        # 状态控制
        self.last_jump_time = 0
        self.jump_detected = False
        
        # 添加可见性阈值
        self.visibility_threshold = 0.5
        
    def get_positions(self, landmarks):
        """获取关键位置信息"""
        # 计算上半身关键点的平均高度
        key_points = [
            self.mp_pose.PoseLandmark.NOSE,
            self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            self.mp_pose.PoseLandmark.LEFT_HIP,
            self.mp_pose.PoseLandmark.RIGHT_HIP
        ]
        
        # 计算所有关键点的平均y坐标
        avg_height = np.mean([landmarks[point.value].y for point in key_points])
        
        return {
            'avg_height': avg_height,
            'timestamp': time.time()
        }
        
    def detect_jump(self, current_pos):
        """检测跳跃"""
        if not self.last_positions:
            return False
            
        # 计算高度变化（注意y轴向下为正）
        height_change = current_pos['avg_height'] - self.last_positions['avg_height']
        current_time = current_pos['timestamp']
        
        # 状态机逻辑
        if self.stage == "down":
            # 检测起跳（身体上升，height_change为负）
            if (height_change < -self.min_height_change and 
                not self.jump_detected):
                self.stage = "up"
                self.jump_detected = True
                return False
                
        elif self.stage == "up":
            # 检测落地（身体下降，height_change为正）
            if (height_change > self.min_height_change and
                self.jump_detected and
                (current_time - self.last_jump_time) >= self.min_jump_interval):
                self.stage = "down"
                self.jump_detected = False
                self.last_jump_time = current_time
                return True
                
        return False
        
    def is_valid_pose(self, landmarks):
        """检查是否所有必要的关键点都可见"""
        required_points = [
            self.mp_pose.PoseLandmark.NOSE,
            self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            self.mp_pose.PoseLandmark.LEFT_HIP,
            self.mp_pose.PoseLandmark.RIGHT_HIP,
            self.mp_pose.PoseLandmark.LEFT_KNEE,
            self.mp_pose.PoseLandmark.RIGHT_KNEE,
            self.mp_pose.PoseLandmark.LEFT_ANKLE,
            self.mp_pose.PoseLandmark.RIGHT_ANKLE
        ]
        
        # 检查所有关键点的可见性
        for point in required_points:
            if landmarks[point.value].visibility < self.visibility_threshold:
                return False
        return True
        
    def process_pose(self, landmarks):
        if not landmarks:
            return None, "未检测到姿势"
            
        try:
            # 首先检查是否所有关键点都可见
            if not self.is_valid_pose(landmarks):
                # 重置状态
                self.jump_detected = False
                self.last_positions = None
                self.position_buffer.clear()
                return None, "请确保全身在画面中"
            
            # 获取当前位置信息
            current_pos = self.get_positions(landmarks)
            
            # 添加到缓冲区
            self.position_buffer.append(current_pos)
            if len(self.position_buffer) > self.buffer_size:
                self.position_buffer.pop(0)
            
            # 检测跳跃
            is_jump = False
            if self.last_positions:
                is_jump = self.detect_jump(current_pos)
                if is_jump:
                    self.counter += 1
            
            # 更新上一帧位置
            self.last_positions = current_pos
            
            # 生成调试信息
            height_change = 0
            if self.last_positions:
                height_change = (current_pos['avg_height'] - 
                               self.last_positions['avg_height'])
            
            debug_info = (
                f"高度变化: {height_change:.4f} | "
                f"状态: {self.stage} | "
                f"跳跃检测: {'是' if self.jump_detected else '否'}"
            )
            
            # 返回信息
            if is_jump:
                return None, f"跳绳完成！计数：{self.counter} ({debug_info})"
            else:
                return None, debug_info
                
        except Exception as e:
            logger.error(f"姿势检测错误: {str(e)}")
            return None, f"姿势检测错误: {str(e)}" 