import pygame
import os
import sys

# Initialize pygame strictly for drawing
pygame.init()

# --- Configuration ---
ASSET_SIZE = 64
PARTICLE_SIZE = 32
ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets")

# --- Palette V2: Curated Soft/Modern Colors ---
PALETTE = {
    # Crops
    "carrot":     (255, 127, 80),   # Coral
    "carrot_dark":(255, 99, 71),    # Tomato (shadow)
    "leaf":       (144, 238, 144),  # Light Green
    "leaf_dark":  (60, 179, 113),   # Medium Sea Green
    
    "pumpkin":    (255, 165, 0),    # Orange
    "pumpkin_d":  (210, 105, 30),   # Chocolate
    
    "sunflower":  (255, 215, 0),    # Gold
    "suncenter":  (139, 69, 19),    # Saddle Brown

    "blueberry":  (70, 130, 255),   # Cornflower Blue
    "blueberry_d":(25, 25, 112),    # Midnight Blue
    
    # Drone
    "drone_body": (255, 255, 255),  # White
    "drone_acc":  (50, 173, 239),   # Soft Blue
    "drone_dark": (200, 200, 210),  # Light Gray shadow
    
    # Environment
    "grass_bg":   (235, 248, 225),  # Very pale green
    "grass_acc":  (190, 220, 180),  # Subtle grass blades
    "dirt_bg":    (245, 222, 179),  # Wheat
    "dirt_acc":   (210, 180, 140),  # Tan
    
    # VFX
    "shadow":     (0, 0, 0, 40),    # Transparent Black
    "gold":       (255, 223, 0),    # Golden Yellow
    "sparkle":    (255, 250, 205),  # Lemon Chiffon
}

class AssetGenerator:
    """
    V2 Generator: Focus on simple shapes, soft shadows, and clean proportions.
    """

    @staticmethod
    def _create_surface(size=ASSET_SIZE):
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        return s

    @staticmethod
    def _draw_shadow(surf, scale=1.0):
        # Universal drop shadow for "floating" effect
        rect = pygame.Rect(16, 48, 32 * scale, 12 * scale)
        rect.centerx = 32
        pygame.draw.ellipse(surf, PALETTE["shadow"], rect)

    @staticmethod
    def draw_carrot(stage: int) -> pygame.Surface:
        surf = AssetGenerator._create_surface()
        AssetGenerator._draw_shadow(surf)
        
        # Draw Body (Rounded Triangle mostly buried)
        # Stage 1-4 impacts leaf size mostly
        
        # Leaves
        leaf_color = PALETTE["leaf"]
        leaf_dark = PALETTE["leaf_dark"]
        
        center_x, bottom_y = 32, 52
        
        if stage >= 1:
            # Small Sprouts
            h = 6 + stage * 4
            # Draw back leaves (darker)
            pygame.draw.ellipse(surf, leaf_dark, (center_x - 6, bottom_y - h - 2, 6, h))
            pygame.draw.ellipse(surf, leaf_dark, (center_x + 2, bottom_y - h - 2, 6, h))
            # Front leaves
            pygame.draw.ellipse(surf, leaf_color, (center_x - 4, bottom_y - h, 8, h + 2))

        # Body (Only visible tip if fully grown)
        if stage == 4:
             pygame.draw.circle(surf, PALETTE["carrot"], (32, 52), 6)
             pygame.draw.circle(surf, PALETTE["carrot_dark"], (30, 52), 2) # Texture dot

        return surf

    @staticmethod
    def draw_pumpkin(stage: int) -> pygame.Surface:
        surf = AssetGenerator._create_surface()
        AssetGenerator._draw_shadow(surf, scale=1.2)
        
        if stage < 4:
            # Growing green sphere
            r = 5 + stage * 5
            pygame.draw.circle(surf, PALETTE["leaf_dark"], (32, 45), r)
            pygame.draw.circle(surf, PALETTE["leaf"], (30, 43), r//2) # Highlight
        else:
            # Mature Pumpkin
            # Draw back lobes
            pygame.draw.circle(surf, PALETTE["pumpkin_d"], (22, 40), 12)
            pygame.draw.circle(surf, PALETTE["pumpkin_d"], (42, 40), 12)
            # Front lobe
            pygame.draw.circle(surf, PALETTE["pumpkin"], (32, 42), 14)
            # Highlight
            pygame.draw.ellipse(surf, (255, 200, 100), (28, 38, 8, 6))
            # Stem
            pygame.draw.rect(surf, PALETTE["leaf_dark"], (30, 26, 4, 8), border_radius=2)

        return surf

    @staticmethod
    def draw_sunflower(stage: int) -> pygame.Surface:
        surf = AssetGenerator._create_surface()
        AssetGenerator._draw_shadow(surf)
        
        # Stem
        pygame.draw.rect(surf, (80, 160, 80), (31, 35, 2, 20))
        
        if stage < 4:
            # Bud
            pygame.draw.circle(surf, (100, 200, 100), (32, 35), 4 + stage * 3)
        else:
            # Flower
            cx, cy = 32, 32
            # Petals
            for i in range(0, 360, 45):
                 # Polar coord for petals
                 import math
                 rad = math.radians(i)
                 px = cx + math.cos(rad) * 12
                 py = cy + math.sin(rad) * 12
                 pygame.draw.circle(surf, PALETTE["sunflower"], (px, py), 9)
            
            # Center
            pygame.draw.circle(surf, PALETTE["suncenter"], (cx, cy), 13)
            # Seeds detail
            pygame.draw.circle(surf, (100, 50, 10), (cx-4, cy-4), 2)
            pygame.draw.circle(surf, (100, 50, 10), (cx+4, cy+4), 2)
            pygame.draw.circle(surf, (100, 50, 10), (cx-4, cy+4), 2)
            pygame.draw.circle(surf, (100, 50, 10), (cx+4, cy-4), 2)

        return surf

    @staticmethod
    def draw_blueberry(stage: int) -> pygame.Surface:
        surf = AssetGenerator._create_surface()
        AssetGenerator._draw_shadow(surf, scale=0.9)
        
        # Bushy base
        # Overlapping circles for bush
        leaf_c = PALETTE["leaf_dark"]
        pygame.draw.circle(surf, leaf_c, (24, 45), 10 + stage*2)
        pygame.draw.circle(surf, leaf_c, (40, 45), 10 + stage*2)
        pygame.draw.circle(surf, PALETTE["leaf"], (32, 40), 12 + stage*2)

        if stage == 4:
            # Berries
            berries = [(22, 35), (42, 38), (32, 28), (28, 48), (38, 46)]
            for bx, by in berries:
                pygame.draw.circle(surf, PALETTE["blueberry_d"], (bx, by), 5)
                pygame.draw.circle(surf, PALETTE["blueberry"], (bx-1, by-1), 4)
                # Glint
                pygame.draw.circle(surf, (200, 230, 255), (bx-2, by-2), 1)

        return surf

    @staticmethod
    def draw_drone(frame_index=0) -> pygame.Surface:
        surf = AssetGenerator._create_surface()
        # Drop Shadow
        AssetGenerator._draw_shadow(surf, scale=0.8)

        cx, cy = 32, 40 # Body center (Lower than middle for prop space)
        
        # 1. Main Pod Body (Sphere/Capsule)
        pygame.draw.circle(surf, PALETTE["drone_body"], (cx, cy), 14)
        
        # 2. Eye / Core Window
        # Pulsing effect? No, simple clean look.
        pygame.draw.circle(surf, PALETTE["drone_acc"], (cx, cy), 6)
        pygame.draw.circle(surf, (255, 255, 255), (cx-2, cy-2), 2) # Glint

        # 3. Propeller Shaft
        pygame.draw.rect(surf, (100, 100, 100), (cx-2, cy-18, 4, 6))

        # 4. Single Big Propeller (Rotating)
        # We simulate rotation by squashing the ellipse width or rotating points
        # For top-down 2D, a rotating ellipses works.
        
        angle = frame_index * 45 # 0, 45, 90, 135...
        import math
        
        # Convert angle to a line visual representing the blade
        rad = math.radians(angle)
        blade_len = 24
        
        dx = math.cos(rad) * blade_len
        dy = math.sin(rad) * 4 # Perceived depth (squash Y)
        
        # Blade color
        c_blade = (50, 50, 50)
        
        # Draw Blade
        p1 = (cx + dx, cy - 18 + dy)
        p2 = (cx - dx, cy - 18 - dy)
        
        pygame.draw.line(surf, c_blade, p1, p2, 4)
        pygame.draw.circle(surf, (200, 200, 200), (cx, cy-18), 3) # Nut

        return surf

    @staticmethod
    def draw_shrub_dead() -> pygame.Surface:
        surf = AssetGenerator._create_surface()
        c = (160, 130, 110)
        pygame.draw.line(surf, c, (32, 50), (20, 30), 2)
        pygame.draw.line(surf, c, (32, 50), (44, 35), 2)
        pygame.draw.circle(surf, c, (32, 52), 4)
        return surf

    @staticmethod
    def draw_tile(kind="dirt") -> pygame.Surface:
        surf = AssetGenerator._create_surface()
        if kind == "dirt":
            surf.fill(PALETTE["dirt_bg"])
            # Subtle pattern
            pygame.draw.circle(surf, PALETTE["dirt_acc"], (10, 10), 4)
            pygame.draw.circle(surf, PALETTE["dirt_acc"], (40, 50), 6)
        elif kind == "wet":
            surf.fill(PALETTE["dirt_acc"]) # Darker
        elif kind == "grass":
            surf.fill(PALETTE["grass_bg"])
            # Cute grass Tuft
            c = PALETTE["grass_acc"]
            pygame.draw.arc(surf, c, (10, 20, 10, 10), 0, 3.14, 2)
            pygame.draw.arc(surf, c, (40, 40, 10, 10), 0, 3.14, 2)

        return surf

    @staticmethod
    def draw_particle(kind="dust") -> pygame.Surface:
        surf = AssetGenerator._create_surface(PARTICLE_SIZE)
        if kind == "dust":
            # Soft cloud
            pygame.draw.circle(surf, (240, 240, 240, 150), (16, 16), 8)
        elif kind == "spark":
            # Diamond shape star
            c = PALETTE["gold"]
            pygame.draw.line(surf, c, (16, 8), (16, 24), 2)
            pygame.draw.line(surf, c, (8, 16), (24, 16), 2)
            pygame.draw.circle(surf, (255, 255, 255), (16, 16), 2)
        
        return surf

    @classmethod
    def generate_all_and_save(cls):
        """Generate all defined assets and save to disk."""
        if not os.path.exists(ASSET_DIR):
            os.makedirs(ASSET_DIR)
            print(f"Created asset directory: {ASSET_DIR}")

        tasks = [
            ("crop_carrot_stage1", lambda: cls.draw_carrot(1)),
            ("crop_carrot_stage2", lambda: cls.draw_carrot(2)),
            ("crop_carrot_stage3", lambda: cls.draw_carrot(3)),
            ("crop_carrot_stage4", lambda: cls.draw_carrot(4)),
            
            ("crop_pumpkin_stage1", lambda: cls.draw_pumpkin(1)),
            ("crop_pumpkin_stage2", lambda: cls.draw_pumpkin(2)),
            ("crop_pumpkin_stage3", lambda: cls.draw_pumpkin(3)),
            ("crop_pumpkin_stage4", lambda: cls.draw_pumpkin(4)),

            ("crop_sunflower_stage1", lambda: cls.draw_sunflower(1)),
            ("crop_sunflower_stage2", lambda: cls.draw_sunflower(2)),
            ("crop_sunflower_stage3", lambda: cls.draw_sunflower(3)),
            ("crop_sunflower_stage4", lambda: cls.draw_sunflower(4)),

            ("crop_blueberry_stage1", lambda: cls.draw_blueberry(1)),
            ("crop_blueberry_stage2", lambda: cls.draw_blueberry(2)),
            ("crop_blueberry_stage3", lambda: cls.draw_blueberry(3)),
            ("crop_blueberry_stage4", lambda: cls.draw_blueberry(4)),

            ("shrub_dead", cls.draw_shrub_dead),
            
            # Animated Drone Frames (0-3)
            ("drone_idle_0", lambda: cls.draw_drone(0)),
            ("drone_idle_1", lambda: cls.draw_drone(1)),
            ("drone_idle_2", lambda: cls.draw_drone(2)),
            ("drone_idle_3", lambda: cls.draw_drone(3)),
            
            ("tile_dirt", lambda: cls.draw_tile("dirt")),
            ("tile_wet", lambda: cls.draw_tile("wet")),
            ("tile_grass", lambda: cls.draw_tile("grass")),
            
            ("particle_dust", lambda: cls.draw_particle("dust")),
            ("particle_spark", lambda: cls.draw_particle("spark")),
        ]

        print("Generating Assets V3 (Animated Drone)...")
        for name, func in tasks:
            path = os.path.join(ASSET_DIR, f"{name}.png")
            try:
                surf = func()
                pygame.image.save(surf, path)
                print(f"  [OK] {name}.png")
            except Exception as e:
                print(f"  [ERR] {name} - {e}")

if __name__ == "__main__":
    AssetGenerator.generate_all_and_save()
