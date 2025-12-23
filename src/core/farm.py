from src.config import GRID_WIDTH, GRID_HEIGHT
from src.entities.crops import CROP_FACTORY

class Farm:
    def __init__(self):
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
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

    def has_any_crop(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is not None:
                    return True
        return False
