from src.ui.main_window import MainWindow
from src.core.database import DatabaseManager
import customtkinter as ctk
from config.dev_config import DEV_MODE, DEV_CONFIG
import sys
import os
import logging

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 设置 TensorFlow 日志级别
logging.getLogger('tensorflow').setLevel(logging.ERROR)  # 设置 TensorFlow 日志级别

def setup_error_logging():
    """设置错误日志"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_file = os.path.join('logs', 'error.log')
    sys.stderr = open(log_file, 'a')

def main():
    try:
        from src.core.logger import logger
        logger.info("应用启动")
        
        # 设置错误日志
        setup_error_logging()
        
        # 初始化数据库
        db_manager = DatabaseManager()
        db_manager.init_database()
        
        # 开发模式：生成测试数据
        if DEV_MODE and DEV_CONFIG["generate_test_data"]:
            try:
                from tools.generate_test_data import generate_test_data
                generate_test_data()
            except ImportError:
                print("开发工具未找到，跳过测试数据生成")
        
        # 创建数据库备份
        success, backup_result = db_manager.backup_database()
        if not success:
            print(f"数据库备份失败: {backup_result}")
        
        # 设置全局样式
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 创建并运行应用
        app = MainWindow()
        
        # 设置任务栏图标
        if os.name == 'nt':  # Windows系统
            import ctypes
            myappid = 'mycompany.smartexercise.1.0'  # 可以自定义
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            
            # 设置窗口图标
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                app.window.iconbitmap(icon_path)
        
        # 添加异常处理
        def handle_exception(exc_type, exc_value, exc_traceback):
            logger.error("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
            
        import sys
        sys.excepthook = handle_exception
        
        app.window.mainloop()
        
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 