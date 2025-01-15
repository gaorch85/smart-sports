import sqlite3
from datetime import datetime, timedelta
import random

def generate_test_data():
    """生成测试数据"""
    conn = sqlite3.connect('exercise_data.db')
    cursor = conn.cursor()
    
    # 清空现有数据
    cursor.execute("DELETE FROM exercise_records")
    
    # 生成过去90天的数据
    exercises = ["深蹲", "俯卧撑", "平板支撑", "跳绳"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    current_date = start_date
    while current_date <= end_date:
        # 每天随机1-3次运动
        daily_exercises = random.randint(1, 3)
        
        for _ in range(daily_exercises):
            # 随机选择运动类型
            exercise = random.choice(exercises)
            
            # 随机生成运动时间（早上6点到晚上10点）
            hour = random.randint(6, 22)
            minute = random.randint(0, 59)
            timestamp = current_date.replace(hour=hour, minute=minute)
            
            # 根据运动类型生成合理的运动数据
            if exercise == "平板支撑":
                # 平板支撑时间：30秒到180秒
                duration = random.randint(30, 180)
                count = duration
            elif exercise == "跳绳":
                # 跳绳次数：50到200次
                count = random.randint(50, 200)
            else:
                # 其他运动次数：5到20次
                count = random.randint(5, 20)
            
            # 插入数据
            cursor.execute("""
                INSERT INTO exercise_records 
                (timestamp, exercise_type, count_or_duration)
                VALUES (?, ?, ?)
            """, (timestamp.isoformat(), exercise, count))
        
        current_date += timedelta(days=1)
    
    # 生成今天的数据（确保有当天数据）
    for exercise in exercises:
        if random.random() < 0.7:  # 70%概率今天有该运动记录
            hour = random.randint(6, datetime.now().hour)
            minute = random.randint(0, 59)
            timestamp = datetime.now().replace(hour=hour, minute=minute)
            
            if exercise == "平板支撑":
                count = random.randint(30, 180)
            elif exercise == "跳绳":
                count = random.randint(50, 200)
            else:
                count = random.randint(5, 20)
                
            cursor.execute("""
                INSERT INTO exercise_records 
                (timestamp, exercise_type, count_or_duration)
                VALUES (?, ?, ?)
            """, (timestamp.isoformat(), exercise, count))
    
    conn.commit()
    conn.close()
    
    print("测试数据生成完成！")
    print("数据范围：", start_date.date(), "至", end_date.date())

if __name__ == "__main__":
    generate_test_data() 