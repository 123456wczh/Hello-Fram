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

class Sunflower(Crop):
    def __init__(self):
        # 8秒成熟，价值50，从深绿变金黄
        super().__init__("Sunflower", 8.0, 50, (34, 139, 34), (255, 215, 0))

# 工厂映射
CROP_FACTORY = {
    "carrot": Carrot,
    "pumpkin": Pumpkin,
    "blueberry": Blueberry,
    "sunflower": Sunflower
}
