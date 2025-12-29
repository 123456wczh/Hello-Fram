import time
import sys
from src.config import DRONE_MOVE_DELAY, GRID_WIDTH, GRID_HEIGHT
from src.entities.crops import CROP_FACTORY

class DroneAPI:
    def __init__(self, farm, output_func):
        self.farm = farm
        self.x = 0
        self.y = 0
        self.inventory = {} # 背包
        self.output = output_func
        self._stop_flag = False
        
        # --- Visual & Animation ---
        self.visual_x = float(self.x)
        self.visual_y = float(self.y)
        self.events = [] # UI will poll these events

    def _check(self):
        if self._stop_flag: 
            sys.exit()
        time.sleep(DRONE_MOVE_DELAY) # 模拟机械动作延迟

    def move(self, direction):
        self._check()
        dx, dy = 0, 0
        if direction == "North": dy = -1
        elif direction == "South": dy = 1
        elif direction == "West": dx = -1
        elif direction == "East": dx = 1
        
        nx, ny = self.x + dx, self.y + dy
        
        # Wrap around logic (Infinite Map)
        nx = nx % GRID_WIDTH
        ny = ny % GRID_HEIGHT
        
        self.x, self.y = nx, ny
        self.events.append({"type": "move", "x": nx, "y": ny})
        return True

    def plant(self, crop_name):
        self._check()
        crop_class = CROP_FACTORY.get(crop_name.lower())
        
        if crop_class:
            # Auto-Destroy existing to overwrite
            self.farm.destroy_crop(self.x, self.y)
            
            new_crop = crop_class() # 实例化对象
            if self.farm.plant_crop(self.x, self.y, new_crop):
                self.output(f"Planted {new_crop.name}")
                self.events.append({"type": "plant", "x": self.x, "y": self.y, "name": new_crop.name})
                return True
            else:
                self.output(f"Fail: Tile blocked (Bedrock?)")
        else:
            self.output(f"Fail: Unknown crop '{crop_name}'")
        return False

    def harvest(self):
        self._check()
        crop_obj = self.farm.harvest_crop(self.x, self.y)
        
        if crop_obj:
            name = crop_obj.name
            amount = 1
            if hasattr(crop_obj, 'size'):
                amount = crop_obj.size * crop_obj.size
                
            self.inventory[name] = self.inventory.get(name, 0) + amount
            self.output(f"Harvested {amount}x {name}! Bag: {self.inventory}")
            # Visuals might need to know amount? API just sends name.
            # Maybe update event to include amount?
            self.events.append({"type": "harvest", "x": self.x, "y": self.y, "name": name, "amount": amount})
            return True
        return False
    
    def get_pos(self):
        return self.x, self.y
    
    def destroy(self):
        self._check()
        if self.farm.destroy_crop(self.x, self.y):
            self.events.append({"type": "plant", "x": self.x, "y": self.y, "name": "poof"}) # Reuse plant poof?
            return True
        return False
    
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
