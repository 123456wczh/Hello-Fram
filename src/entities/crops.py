import random
class Crop:
    def __init__(self, name, growth_time, value):
        self.name = name
        self.max_growth = growth_time
        self.value = value
        self.current_growth = 0.0
        self.size = 1 # 1x1 defaulty

    @property
    def is_ready(self):
        return self.current_growth >= self.max_growth

    def grow(self, dt):
        if self.current_growth < self.max_growth:
            self.current_growth += dt

    @property
    def color(self):
        # Deprecated: Kept effectively None or implementing basic lerp if needed for debug?
        # User requested removal.
        return (255, 255, 255)
    
    def to_dict(self):
        """序列化：转为字典"""
        return {
            "type": self.name.lower(), # "carrot"
            "growth": self.current_growth
        }

# 占位符作物 (用于大型作物的附属格)
class OccupiedSlot:
    def __init__(self, parent_crop, px, py):
        self.parent = parent_crop # Reference to the main crop
        self.parent_pos = (px, py) # Location of the parent
        self.name = "Occupied"
        self.value = 0
    
    @property
    def is_ready(self):
        return self.parent.is_ready
    
    @property
    def current_growth(self):
        return self.parent.current_growth
        
    @property
    def max_growth(self):
        return self.parent.max_growth

    def grow(self, dt):
        pass # Grown by parent

    def get_color(self):
        return None # Should not be rendered essentially, or render same color?

    def to_dict(self):
        return {"type": "occupied"} # Save/Load handling needs care

# 具体作物定义
class Carrot(Crop):
    def __init__(self):
        # 3秒成熟，价值10
        super().__init__("Carrot", 3.0, 10)

class Pumpkin(Crop):
    def __init__(self, level=1):
        # 8s mature
        super().__init__("Pumpkin", 8.0, 30)
        self.level = level
        self.size = level
        self.is_rotten = False
        self.fate_checked = False
        
        # Recalculate value based on level
        self.update_stats()

    def update_stats(self):
        # Value = Base * Area * Level (Exponential-ish reward)
        # L1: 30 * 1 * 1 = 30
        # L2: 30 * 4 * 2 = 240
        # L3: 30 * 9 * 3 = 810
        base = 30
        area = self.level * self.level
        self.value = base * area * self.level
        
        if self.is_rotten:
            self.value = 0
            self.name = "Rotten Pumpkin"
        else:
            self.name = "Pumpkin" # Always "Pumpkin" for inventory unification
            # Level is stored in self.level and handled by size multiplier in API

    def grow(self, dt):
        was_ready = self.is_ready
        super().grow(dt)
        
        # Fate Rot check at the moment of maturity
        if self.is_ready and not was_ready and not self.fate_checked:
            self.fate_checked = True
            if random.random() < 0.2:  # 20% Chance
                self.make_rotten()

    def make_rotten(self):
        self.is_rotten = True
        # self.color_ready = (80, 50, 20) # Rot brown
        self.update_stats()

    def to_dict(self):
        d = super().to_dict()
        d['level'] = self.level
        d['is_rotten'] = self.is_rotten
        return d

class Blueberry(Crop):
    def __init__(self):
        # 5秒成熟，价值30
        super().__init__("Blueberry", 5.0, 30)

class Sunflower(Crop):
    def __init__(self):
        # 8秒成熟，价值50
        super().__init__("Sunflower", 8.0, 50)

# 工厂映射
CROP_FACTORY = {
    "carrot": Carrot,
    "pumpkin": Pumpkin,
    "blueberry": Blueberry,
    "sunflower": Sunflower
}
