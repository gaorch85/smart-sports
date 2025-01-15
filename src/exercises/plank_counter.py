from ..core.exercise_counter import ExerciseCounter
import numpy as np
import time
from ..core.logger import logger

class PlankCounter(ExerciseCounter):
    def __init__(self):
        super().__init__("平板支撑")
        self.start_time = None
        self.last_valid_time = None
        self.total_time = 0
        self.is_valid_pose_flag = False
        self.last_announce_time = 0
        self.is_finished = False
        self.debug = True
        
    def calculate_time(self):
        """计算当前有效时间"""
        if not self.start_time:
            return 0
        if self.is_valid_pose_flag:
            return int(time.time() - self.start_time)
        return self.total_time
        
    def process_pose(self, landmarks):
        if self.is_finished:
            return None, f"本次平板支撑已结束，坚持了 {self.total_time} 秒", None, True
            
        if not landmarks:
            self.handle_invalid_pose()
            return None, "未检测到姿势"
            
        try:
            # 获取姿势验证结果
            valid_result = self.is_valid_pose(landmarks)
            is_valid = valid_result[0] if isinstance(valid_result, tuple) else valid_result
            debug_info = valid_result[1] if isinstance(valid_result, tuple) else ""
            
            # 更新时间
            current_time = time.time()
            
            if not is_valid:
                # 处理无效姿势
                if self.is_valid_pose_flag:  # 如果之前是有效姿势
                    self.is_valid_pose_flag = False
                    if self.start_time:
                        self.total_time = int(current_time - self.start_time)
                    if self.total_time > 0:
                        self.is_finished = True
                        return None, f"姿势不正确，本次平板支撑结束，坚持了 {self.total_time} 秒", None, True
                return None, f"请保持平板支撑姿势 {debug_info}"
            
            # 有效姿势处理
            if not self.is_valid_pose_flag:
                self.is_valid_pose_flag = True
                if self.start_time is None:
                    self.start_time = current_time
                    self.last_announce_time = current_time
            
            # 计算当前时间
            current_duration = self.calculate_time()
            
            # 每5秒播报一次时间
            should_announce = False
            if current_duration >= 5 and (current_duration - self.last_announce_time) >= 5:
                self.last_announce_time = current_duration
                should_announce = True
            
            message = f"已坚持 {current_duration} 秒 {debug_info}"
            return None, message, should_announce if should_announce else None
            
        except Exception as e:
            logger.error(f"姿势检测错误: {str(e)}")
            self.handle_invalid_pose()
            return None, f"姿势检测错误: {str(e)}"
            
    def handle_invalid_pose(self):
        """处理无效姿势"""
        if self.is_valid_pose_flag:
            self.is_valid_pose_flag = False
            if self.start_time:
                self.total_time = int(time.time() - self.start_time)
                
    def get_final_time(self):
        """获取最终坚持时间"""
        if self.total_time > 0:
            return f"本次平板支撑坚持了 {self.total_time} 秒"
        return "未完成有效的平板支撑"
        
    def reset(self):
        """重置计数器"""
        self.start_time = None
        self.last_valid_time = None
        self.total_time = 0
        self.is_valid_pose_flag = False
        self.last_announce_time = 0
        self.is_finished = False 
        
    def is_valid_pose(self, landmarks):
        """检查是否是有效的平板支撑姿势"""
        try:
            # 获取关键点
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
            left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
            
            # 降低可见性要求
            key_points = [left_shoulder, left_hip, left_ankle, left_elbow]
            if any(point.visibility < 0.5 for point in key_points):
                return False, "关键点不可见"
            
            # 计算身体角度
            body_angle = abs(np.arctan2(left_hip.y - left_shoulder.y,
                                      left_hip.x - left_shoulder.x) * 180 / np.pi)
                                      
            # 计算腿部角度
            leg_angle = abs(np.arctan2(left_ankle.y - left_hip.y,
                                     left_ankle.x - left_hip.x) * 180 / np.pi)
                                     
            # 计算手臂角度
            arm_angle = self.calculate_angle(
                [left_shoulder.x, left_shoulder.y],
                [left_elbow.x, left_elbow.y],
                [left_hip.x, left_hip.y]
            )
            
            # 记录调试信息
            debug_info = (f"身体角度: {body_angle:.1f}° 腿部角度: {leg_angle:.1f}° "
                         f"手臂角度: {arm_angle:.1f}°")
            logger.debug(debug_info)
            
            # 判断各个部位是否符合要求
            is_body_straight = abs(180 - body_angle) < 30
            is_leg_straight = abs(180 - leg_angle) < 30
            is_arm_valid = 75 < arm_angle < 105
            
            # 构建详细的反馈信息
            feedback = []
            if not is_body_straight:
                feedback.append("请保持身体平直")
            if not is_leg_straight:
                feedback.append("请伸直双腿")
            if not is_arm_valid:
                feedback.append("请调整手臂角度")
                
            result = is_body_straight and is_leg_straight and is_arm_valid
            
            # 返回结果和调试信息
            if not result:
                feedback_str = "，".join(feedback)
                logger.debug(f"姿势无效: {debug_info} - {feedback_str}")
                return False, f"{feedback_str} ({debug_info})"
                
            return True, debug_info
            
        except Exception as e:
            logger.error(f"姿势检测错误: {str(e)}")
            return False, f"检测错误: {str(e)}" 