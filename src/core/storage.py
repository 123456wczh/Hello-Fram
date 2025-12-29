import json
import os
from src.config import SAVE_FILE

class SaveManager:
    @staticmethod
    def ensure_user_scripts_dir():
        if not os.path.exists("user_scripts"):
            os.makedirs("user_scripts")

    @staticmethod
    def save_game(farm, drone, code_text=None):

        """
        参数:
        farm: Farm 对象
        drone: DroneAPI 对象
        code_text: 字符串 (编辑器里的代码)
        """
        data = {
            "farm": farm.to_dict(),
            "drone": drone.to_dict()
        }

        
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4) # indent=4 让文件可读性更好
            print("Game Saved Successfully!")
            return True
        except Exception as e:
            print(f"Save Failed: {e}")
            return False

    @staticmethod
    def load_game(farm, drone):
        """
        读取存档，并更新传入的 farm 和 drone 对象
        返回: True/False
        """

        if not os.path.exists(SAVE_FILE):
            print("No save file found.")
            return None

        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 恢复数据
            farm.load_from_data(data["farm"])
            drone.load_from_data(data["drone"])
            
            return True

        except Exception as e:
            print(f"Load Failed: {e}")
            return None
