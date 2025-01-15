import mediapipe as mp
import numpy as np

class ExerciseCounter:
    def __init__(self, exercise_name):
        self.exercise_name = exercise_name
        self.counter = 0
        self.mp_pose = mp.solutions.pose
        
    def calculate_angle(self, a, b, c):
        """计算三个点形成的角度"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle > 180.0:
            angle = 360-angle
            
        return angle
        
    def process_pose(self, landmarks):
        """处理姿势数据"""
        raise NotImplementedError("子类必须实现process_pose方法")
        
    def reset(self):
        """重置计数器"""
        self.counter = 0 