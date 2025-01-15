import sqlite3
import json
import os
from datetime import datetime
import shutil

class DatabaseManager:
    def __init__(self, db_path='exercise_data.db'):
        self.db_path = db_path
        self.backup_dir = 'backups'
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercise_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                exercise_type TEXT NOT NULL,
                count_or_duration INTEGER NOT NULL,
                exercise_time INTEGER NOT NULL,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_exercise_record(self, exercise_type, count_or_duration, exercise_time, notes=""):
        """保存运动记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO exercise_records 
                (timestamp, exercise_type, count_or_duration, exercise_time, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), exercise_type, count_or_duration, exercise_time, notes))
            
            conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"数据库错误: {str(e)}")
            raise
            
        finally:
            if 'conn' in locals():
                conn.close()
    
    def backup_database(self):
        """创建数据库备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'exercise_data_{timestamp}.db')
        
        try:
            shutil.copy2(self.db_path, backup_path)
            return True, backup_path
        except Exception as e:
            return False, str(e)
    
    def export_to_json(self, filepath):
        """导出数据为JSON格式"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, exercise_type, count_or_duration, notes
            FROM exercise_records
            ORDER BY timestamp DESC
        """)
        
        records = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        data = []
        for record in records:
            data.append({
                'id': record[0],
                'timestamp': record[1],
                'exercise_type': record[2],
                'count_or_duration': record[3],
                'notes': record[4]
            })
        
        # 写入JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# 创建全局数据库管理器实例
db_manager = DatabaseManager()

def save_exercise_record(exercise_type, count_or_duration, exercise_time, notes=""):
    """全局保存运动记录函数"""
    db_manager.save_exercise_record(exercise_type, count_or_duration, exercise_time, notes) 