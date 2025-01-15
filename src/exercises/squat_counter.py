from ..core.exercise_counter import ExerciseCounter
import numpy as np

class SquatCounter(ExerciseCounter):
    def __init__(self):
        super().__init__("深蹲")
        self.stage = "up"  # 初始状态设为站立
        self.counter = 0
        self.last_angle = None
        self.stable_count = 0
        self.debug = True  # 开启调试信息
        
    def is_valid_pose(self, landmarks):
        """检查是否是有效的深蹲姿势"""
        # 检查关键点的可见性
        key_points = [
            self.mp_pose.PoseLandmark.LEFT_HIP,
            self.mp_pose.PoseLandmark.LEFT_KNEE,
            self.mp_pose.PoseLandmark.LEFT_ANKLE,
            self.mp_pose.PoseLandmark.RIGHT_HIP,
            self.mp_pose.PoseLandmark.RIGHT_KNEE,
            self.mp_pose.PoseLandmark.RIGHT_ANKLE
        ]
        
        # 检查关键点可见性（降低阈值）
        for point in key_points:
            if landmarks[point.value].visibility < 0.3:  # 降低可见性要求
                return False
                
        # 检查是否正面朝向（放宽要求）
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        hip_z_diff = abs(left_hip.z - right_hip.z)
        
        if hip_z_diff > 0.3:  # 放宽z坐标差异的限制
            return False
            
        return True
        
    def process_pose(self, landmarks):
        if not landmarks:
            return None, "未检测到姿势"
            
        try:
            if not self.is_valid_pose(landmarks):
                self.stable_count = 0
                return None, "请正面朝向摄像头，确保全身在画面中"
            
            # 使用左右腿的平均角度
            # 左腿角度
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            left_knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
            left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
            
            left_angle = self.calculate_angle(
                [left_hip.x, left_hip.y],
                [left_knee.x, left_knee.y],
                [left_ankle.x, left_ankle.y]
            )
            
            # 右腿角度
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            right_knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
            right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
            
            right_angle = self.calculate_angle(
                [right_hip.x, right_hip.y],
                [right_knee.x, right_knee.y],
                [right_ankle.x, right_ankle.y]
            )
            
            # 使用两腿的平均角度
            angle = (left_angle + right_angle) / 2
            
            # 添加防抖动逻辑（降低要求）
            if self.last_angle is not None:
                angle_diff = abs(angle - self.last_angle)
                if angle_diff < 15:  # 进一步放宽角度变化阈值
                    self.stable_count += 1
                else:
                    self.stable_count = 0
            
            self.last_angle = angle
            
            # 调试信息
            debug_info = f"角度: {angle:.1f}° | 状态: {self.stage} | 稳定计数: {self.stable_count}"
            
            # 状态判断和计数逻辑
            if angle > 160:  # 站立姿势
                if self.stage == "down":  # 如果之前是蹲下状态
                    self.counter += 1  # 完成一次深蹲
                    self.stage = "up"
                    self.stable_count = 0
                    return angle, f"深蹲完成！计数：{self.counter} ({debug_info})"
                
                self.stage = "up"
                return angle, f"请下蹲 ({debug_info})"
                
            elif angle < 90:  # 蹲下姿势
                if self.stage == "up":  # 如果之前是站立状态
                    self.stage = "down"
                    self.stable_count = 0
                    return angle, f"请站起 ({debug_info})"
                
                self.stage = "down"
                return angle, f"保持蹲姿 ({debug_info})"
                
            else:  # 中间状态
                if self.stage == "up":
                    return angle, f"继续下蹲 ({debug_info})"
                elif self.stage == "down":
                    return angle, f"继续站起 ({debug_info})"
                else:
                    self.stage = "up"  # 不确定时默认为站立状态
                    return angle, f"请开始动作 ({debug_info})"
            
        except Exception as e:
            return None, f"姿势检测错误: {str(e)}" 