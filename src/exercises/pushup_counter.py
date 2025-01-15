from ..core.exercise_counter import ExerciseCounter
import numpy as np

class PushupCounter(ExerciseCounter):
    def __init__(self):
        super().__init__("俯卧撑")
        self.stage = None
        self.counter = 0
        self.last_angle = None
        self.stable_count = 0
        self.angle_threshold = 20
        self.stable_threshold = 5
        
    def is_valid_pose(self, landmarks):
        """检查是否是有效的俯卧撑姿势"""
        key_points = [
            self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            self.mp_pose.PoseLandmark.LEFT_ELBOW,
            self.mp_pose.PoseLandmark.LEFT_WRIST,
            self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            self.mp_pose.PoseLandmark.RIGHT_ELBOW,
            self.mp_pose.PoseLandmark.RIGHT_WRIST
        ]
        
        visible_points = 0
        for point in key_points:
            if landmarks[point.value].visibility > 0.5:
                visible_points += 1
        
        if visible_points < 4:
            return False
            
        return True
        
    def process_pose(self, landmarks):
        if not landmarks:
            return None, "未检测到姿势"
            
        try:
            if not self.is_valid_pose(landmarks):
                return None, "请调整姿势，确保手臂在画面中"
            
            # 获取关键点
            left_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                           landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            left_elbow = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                         landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            left_wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                         landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            
            right_shoulder = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                            landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            right_elbow = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                          landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            right_wrist = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                          landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            
            # 计算手臂角度
            left_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)
            avg_angle = (left_angle + right_angle) / 2
            
            # 状态判断
            if avg_angle > 160:  # 手臂伸直
                if self.stage == "down":
                    self.stage = "up"
                    self.counter += 1
                    return avg_angle, "完成一次俯卧撑"
                self.stage = "up"
                return avg_angle, "请下压"
                
            elif avg_angle < 90:  # 手臂弯曲
                if self.stage != "down":
                    self.stage = "down"
                    return avg_angle, "请上推"
                return avg_angle, "请上推"
                
            else:  # 中间状态
                if self.stage == "up":
                    return avg_angle, "继续下压"
                elif self.stage == "down":
                    return avg_angle, "继续上推"
                else:
                    return avg_angle, "请开始动作"
            
        except Exception as e:
            return None, f"姿势检测错误: {str(e)}" 