import pygame
import pygame_gui
import threading
import time
import sys
import traceback

# --- 配置参数 ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
GAME_AREA_WIDTH = 600
UI_AREA_WIDTH = 400
GRID_SIZE = 50

# 颜色定义
COLOR_BG = (30, 30, 30)
COLOR_GAME_BG = (20, 20, 20)
COLOR_GRID = (50, 50, 50)

#存档（暂时）
import json
import os

SAVE_FILE = "savegame.json"

class SaveManager:
    @staticmethod
    def save_game(farm, drone, code_text):
        """
        参数:
        farm: Farm 对象
        drone: DroneAPI 对象
        code_text: 字符串 (编辑器里的代码)
        """
        data = {
            "farm": farm.to_dict(),
            "drone": drone.to_dict(),
            "user_code": code_text  # 直接把代码字符串存进去
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
        返回: 存档里的代码字符串 (user_code)
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
            
            return data.get("user_code", "")
        except Exception as e:
            print(f"Load Failed: {e}")
            return None


# --- 1. 模型层 (Model & OOP) ---

class Crop:
    def __init__(self, name, grow_time, value, color_start, color_ready):
        self.name = name
        self.max_growth = grow_time
        self.value = value
        self.current_growth = 0
        self.color_start = color_start
        self.color_ready = color_ready

    @property
    def is_ready(self):
        return self.current_growth >= self.max_growth

    def grow(self, dt):
        if self.current_growth < self.max_growth:
            self.current_growth += dt

    def get_color(self):
        # 颜色线性插值
        ratio = 0
        if self.max_growth > 0:
            ratio = min(1.0, self.current_growth / self.max_growth)
        
        r = self.color_start[0] + (self.color_ready[0] - self.color_start[0]) * ratio
        g = self.color_start[1] + (self.color_ready[1] - self.color_start[1]) * ratio
        b = self.color_start[2] + (self.color_ready[2] - self.color_start[2]) * ratio
        return (int(r), int(g), int(b))
    
    def to_dict(self):
        """序列化：转为字典"""
        return {
            "type": self.name.lower(), # "carrot"
            "growth": self.current_growth
        }
# 具体作物定义
class Carrot(Crop):
    def __init__(self):
        # 3秒成熟，价值10，从绿色变橙色
        super().__init__("Carrot", 3.0, 10, (50, 150, 50), (255, 140, 0))

class Pumpkin(Crop):
    def __init__(self):
        # 6秒成熟，价值30，从深绿变深橙
        super().__init__("Pumpkin", 6.0, 30, (30, 100, 30), (200, 100, 0))

class Blueberry(Crop):
    def __init__(self):
        # 5秒成熟，价值30，从青色变蓝色
        super().__init__("Blueberry", 5.0, 30, (127,255,212), (72,61,139))

# 工厂映射
CROP_FACTORY = {
    "carrot": Carrot,
    "pumpkin": Pumpkin,
    "blueberry":Blueberry
}

class Farm:
    def __init__(self):
        self.width = 10
        self.height = 10
        # Grid 存放 Crop 对象或 None
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
    
    def plant_crop(self, x, y, crop_obj):
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.grid[y][x] is None:
                self.grid[y][x] = crop_obj
                return True
        return False

    def harvest_crop(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            crop = self.grid[y][x]
            if crop and crop.is_ready:
                self.grid[y][x] = None
                return crop
        return None
    
    def update(self, dt):
        """让所有作物生长"""
        for y in range(self.height):
            for x in range(self.width):
                crop = self.grid[y][x]
                if crop:
                    crop.grow(dt)

    def to_dict(self):
        """保存整个网格的状态"""
        grid_data = []
        for y in range(self.height):
            row_data = []
            for x in range(self.width):
                crop = self.grid[y][x]
                if crop:
                    row_data.append(crop.to_dict())
                else:
                    row_data.append(None) # 空地
            grid_data.append(row_data)
        return grid_data

    def load_from_data(self, grid_data):
        """从存档数据恢复网格"""
        for y in range(self.height):
            for x in range(self.width):
                cell_data = grid_data[y][x]
                if cell_data is None:
                    self.grid[y][x] = None
                else:
                    # 使用工厂模式重建对象
                    crop_type = cell_data["type"]
                    growth = cell_data["growth"]
                    
                    # 查找对应的类
                    crop_class = CROP_FACTORY.get(crop_type)
                    if crop_class:
                        new_crop = crop_class()
                        new_crop.current_growth = growth # 恢复生长进度
                        self.grid[y][x] = new_crop
# --- 2. 控制层 (Controller/API) ---

class DroneAPI:
    def __init__(self, farm, output_func):
        self.farm = farm
        self.x = 0
        self.y = 0
        self.inventory = {} # 背包
        self.output = output_func
        self._stop_flag = False

    def _check(self):
        if self._stop_flag: 
            sys.exit()
        time.sleep(0.2) # 模拟机械动作延迟

    def move(self, direction):
        self._check()
        dx, dy = 0, 0
        if direction == "North": dy = -1
        elif direction == "South": dy = 1
        elif direction == "West": dx = -1
        elif direction == "East": dx = 1
        
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < 10 and 0 <= ny < 10:
            self.x, self.y = nx, ny
            return True
        return False

    def plant(self, crop_name):
        self._check()
        crop_class = CROP_FACTORY.get(crop_name.lower())
        
        if crop_class:
            new_crop = crop_class() # 实例化对象
            if self.farm.plant_crop(self.x, self.y, new_crop):
                self.output(f"Planted {new_crop.name}")
                return True
            else:
                self.output(f"Fail: Tile not empty")
        else:
            self.output(f"Fail: Unknown crop '{crop_name}'")
        return False

    def harvest(self):
        self._check()
        crop_obj = self.farm.harvest_crop(self.x, self.y)
        
        if crop_obj:
            name = crop_obj.name
            self.inventory[name] = self.inventory.get(name, 0) + 1
            self.output(f"Harvested {name}! Bag: {self.inventory}")
            return True
        return False
    
    def get_pos(self):
        return self.x, self.y
    
    def log(self, msg):
        self.output(str(msg))

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "inventory": self.inventory
        }

    def load_from_data(self, data):
        self.x = data.get("x", 0)
        self.y = data.get("y", 0)
        self.inventory = data.get("inventory", {})
# --- 3. 视图层 (View & GUI) ---

class GameIDE:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Farm Game - OOP Version")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.ui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # --- 布局规划 (总高度 600) ---
        # 1. 代码编辑器: 0 ~ 380 (高度 380)
        # 2. 背包显示: 380 ~ 440 (高度 60)
        # 3. 存档按钮: 440 ~ 480 (高度 40)
        # 4. 控制台: 480 ~ 550 (高度 70)
        # 5. 运行按钮: 550 ~ 600 (高度 50)

        # --- 1. 代码编辑器 (稍微改短一点，给下面腾位置) ---
        # 初始脚本
        init_code = """
# 自动种植与收割脚本
while True:
    drone.plant("carrot")
    if drone.harvest():
        print("Got one!")
    
    drone.move("East")
    if drone.get_pos()[0] >= 9:
        for _ in range(9):
             drone.move("West")
             drone.move("South")
"""
        self.code_editor = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((GAME_AREA_WIDTH, 0), (UI_AREA_WIDTH, 380)),
            initial_text=init_code.strip(),
            manager=self.ui_manager
        )
        
        # --- 2. 背包显示 ---
        self.inventory_display = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((GAME_AREA_WIDTH, 380), (UI_AREA_WIDTH, 60)),
            html_text="<b>Inventory:</b> Empty",
            manager=self.ui_manager
        )

        # --- 3. 存档/读档按钮 (放在背包和控制台之间) ---
        self.btn_save = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((GAME_AREA_WIDTH, 440), (UI_AREA_WIDTH // 2 - 5, 40)),
            text='Save',
            manager=self.ui_manager
        )
        
        self.btn_load = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((GAME_AREA_WIDTH + UI_AREA_WIDTH // 2 + 5, 440), (UI_AREA_WIDTH // 2 - 5, 40)),
            text='Load',
            manager=self.ui_manager
        )
        
        # --- 4. 控制台输出 ---
        self.console_output = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((GAME_AREA_WIDTH, 480), (UI_AREA_WIDTH, 70)),
            html_text="Console Ready...<br>",
            manager=self.ui_manager
        )
        
        # --- 5. 运行按钮 ---
        self.run_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((GAME_AREA_WIDTH, 550), (UI_AREA_WIDTH, 50)),
            text='RUN CODE (CTRL+ENTER)',
            manager=self.ui_manager
        )

        self.farm = Farm()
        self.drone = DroneAPI(self.farm, self.print_to_console)
        self.thread = None
    def print_to_console(self, text):
        self.console_output.append_html_text(f"{text}<br>")
        if self.console_output.scroll_bar:
            self.console_output.scroll_bar.scroll_position = self.console_output.scroll_bar.bottom_limit

    def update_inventory_ui(self):
        text = "<b>Inventory:</b> "
        if not self.drone.inventory:
            text += "Empty"
        else:
            items = [f"{k}: {v}" for k, v in self.drone.inventory.items()]
            text += " | ".join(items)
        self.inventory_display.set_text(text)

    def run_user_code(self):
        code = self.code_editor.get_text()
        
        if self.thread and self.thread.is_alive():
            self.drone._stop_flag = True
            self.thread.join(timeout=1.0)
        
        self.drone._stop_flag = False
        self.console_output.set_text("")
        self.print_to_console("<font color='#00FF00'>--- Script Start ---</font>")

        def target():
            env = {
                'drone': self.drone,
                'time': time,
                'print': self.drone.log
            }
            try:
                exec(code, env)
            except Exception as e:
                self.print_to_console(f"<font color='#FF0000'>Error: {e}</font>")
                traceback.print_exc()

        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()

    def save_game_action(self):
        # 1. 获取编辑器里的代码
        current_code = self.code_editor.get_text()
        
        # 2. 调用管理器
        if SaveManager.save_game(self.farm, self.drone, current_code):
            self.print_to_console("<font color='#FFFF00'>Game Saved!</font>")

    def load_game_action(self):
        # 1. 调用管理器恢复数据
        loaded_code = SaveManager.load_game(self.farm, self.drone)
        
        if loaded_code is not None:
            # 2. 恢复代码到编辑器
            self.code_editor.set_text(loaded_code)
            self.print_to_console("<font color='#FFFF00'>Game Loaded!</font>")
            # 3. 强制刷新一下UI显示（背包等）
            self.update_inventory_ui()

 
                
    
    def draw_game_area(self):
        # 绘制背景
        surface = pygame.Surface((GAME_AREA_WIDTH, SCREEN_HEIGHT))
        surface.fill(COLOR_GAME_BG)
        
        offset = 50
        
        for y in range(self.farm.height):
            for x in range(self.farm.width):
                rect_x = offset + x * GRID_SIZE
                rect_y = offset + y * GRID_SIZE
                
                # 画格子边框
                pygame.draw.rect(surface, COLOR_GRID, (rect_x, rect_y, GRID_SIZE, GRID_SIZE), 1)
                
                # 画作物 (这是你之前可能出错的地方)
                crop = self.farm.grid[y][x]
                if crop:
                    # 1. 计算圆心
                    center = (rect_x + GRID_SIZE // 2, rect_y + GRID_SIZE // 2)
                    
                    # 2. 获取颜色 (调用新写的 get_color)
                    color = crop.get_color()
                    
                    # 3. 计算大小 (根据生长比例，最小5，最大20)
                    growth_ratio = crop.current_growth / crop.max_growth if crop.max_growth > 0 else 0
                    growth_ratio = min(1.0, growth_ratio)
                    radius = 5 + 15 * growth_ratio 
                    
                    # 4. 绘制
                    pygame.draw.circle(surface, color, center, int(radius))

        # 画无人机
        d_x = offset + self.drone.x * GRID_SIZE
        d_y = offset + self.drone.y * GRID_SIZE
        # 无人机用青色空心框表示
        pygame.draw.rect(surface, (0, 255, 255), (d_x, d_y, GRID_SIZE, GRID_SIZE), 3)
        
        self.window.blit(surface, (0, 0))

    def run(self):
        while self.running:
            time_delta = self.clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # 处理快捷键
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.run_user_code()

                # 处理按钮点击 (所有按钮逻辑放在一起)
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.run_button:
                        self.run_user_code()
                    elif event.ui_element == self.btn_save:
                        self.save_game_action()
                    elif event.ui_element == self.btn_load:
                        self.load_game_action()
                
                self.ui_manager.process_events(event)
            
            # 更新逻辑
            self.ui_manager.update(time_delta)
            self.farm.update(time_delta)
            self.update_inventory_ui()
            
            # 渲染
            self.window.fill(COLOR_BG)
            self.draw_game_area()
            self.ui_manager.draw_ui(self.window)
            
            pygame.display.flip()

        if self.thread:
            self.drone._stop_flag = True
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = GameIDE()
    app.run()

