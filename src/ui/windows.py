import pygame
import pygame_gui
from src.config import *
from src.entities.crops import CROP_FACTORY
from src.core.skills import SkillManager
from src.ui.visuals import get_visual_manager

class BaseModal:
    """Helper wrap for pygame_gui UIWindow to handle centering and simple show/hide."""
    def __init__(self, manager, title, width, height):
        self.manager = manager
        self.width = width
        self.height = height
        
        # Center
        x = (SCREEN_WIDTH - width) // 2
        y = (SCREEN_HEIGHT - height) // 2
        
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect((x, y), (width, height)),
            manager=manager,
            window_display_title=title,
            visible=1 # Initialize visible to avoid UIScrollingContainer init crash
        )
        # We can add a "Close" callback if needed, but pygame_gui handles the X button.
        # DO NOT hide here. Container children crash if added to hidden window.

    def show(self):
        self.window.show()

    def hide(self):
        self.window.hide()

class CropGuideWindow(BaseModal):
    def __init__(self, manager):
        super().__init__(manager, "Agricultural Database", 600, 450)
        self.visuals = get_visual_manager()
        self._build_ui()
        self.hide() # Safe to hide now that children are added

    def _build_ui(self):
        # Create a scrollable container
        container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect((0, 0), (self.width - 32, self.height - 40)),
            manager=self.manager,
            container=self.window
        )
        
        y_offset = 10
        for name, crop_cls in CROP_FACTORY.items():
            # Instantiate dummy to get stats
            dummy = crop_cls()
            
            # Panel for each crop
            panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect((10, y_offset), (540, 80)),
                manager=self.manager,
                container=container
            )
            
            # Icon (Using Asset)
            # We can't put a raw surface in pygame_gui easily without a custom class or IImage
            # So we make a UIImage
            asset_name = f"crop_{name}_stage4"
            img_surf = self.visuals.get_asset(asset_name)
            img_surf = pygame.transform.scale(img_surf, (48, 48))
            
            pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect((10, 16), (48, 48)),
                image_surface=img_surf,
                manager=self.manager,
                container=panel
            )
            
            # Text Info
            # Name
            pygame_gui.elements.UITextBox(
                relative_rect=pygame.Rect((70, 10), (200, 30)),
                html_text=f"<b><font size=5>{dummy.name}</font></b>",
                manager=self.manager,
                container=panel
            )
            
            # Stats
            stats = f"Time: {dummy.max_growth}s | Value: ${dummy.value}"
            if name == "pumpkin": stats += " | <font color='#FFA500'>Requires Fusion</font>"
            if name == "sunflower": stats += " | <font color='#FFFF00'>Sorting Challenge</font>"
            
            pygame_gui.elements.UITextBox(
                relative_rect=pygame.Rect((70, 40), (450, 40)),
                html_text=f"<font color='#DDDDDD'>{stats}</font>",
                manager=self.manager,
                container=panel
            )
            
            y_offset += 90

        # Adjust scrollable area
        container.set_scrollable_area_dimensions((540, y_offset))


class SkillTreeWindow(BaseModal):
    def __init__(self, manager, skill_manager, drone=None):
        super().__init__(manager, "Skill Tree (Neural Upgrade)", 800, 500)
        self.skill_manager = skill_manager
        self.drone = drone
        self.buttons = {}
        self._build_ui()
        self.hide()
        
    def _build_ui(self):
        # We need a surface to draw lines on.
        # pygame_gui doesn't support drawing lines between elements easily.
        # So we use a UIImage as a background for lines, then place buttons on top.
        
        # 1. Background Surface for connections
        self.bg_surf = pygame.Surface((760, 420), pygame.SRCALPHA)
        self.bg_image = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect((20, 20), (760, 420)),
            image_surface=self.bg_surf,
            manager=self.manager,
            container=self.window
        )
        
        # 2. Draw Connections & Place Buttons
        skills = self.skill_manager.skills
        
        # Define layout area
        area_w = 760
        area_h = 420
        
        # Helper to get pos
        def get_pos(node):
            return (int(node.x * area_w), int(node.y * area_h))

        # Draw Lines
        self.bg_surf.fill((0,0,0,0)) # Clear
        for sid, node in skills.items():
            if node.parent_id and node.parent_id in skills:
                parent = skills[node.parent_id]
                start = get_pos(parent)
                end = get_pos(node)
                # Offset for button center (approx 20, 20)
                start = (start[0] + 0, start[1] + 15)
                end = (end[0] + 0, end[1] + 15)
                
                color = (100, 100, 100)
                if parent.unlocked: color = (100, 200, 100) # Green path
                
                pygame.draw.line(self.bg_surf, color, start, end, 4)
        
        self.bg_image.set_image(self.bg_surf) # Update texture

        # Place Node Buttons
        for sid, node in skills.items():
            px, py = get_pos(node)
            # Center button
            btn_w, btn_h = 140, 50
            rect = pygame.Rect((px - btn_w//2, py), (btn_w, btn_h))
            
            # Style based on state
            text = node.name
            
            # Check unlock status using drone inventory if available
            can_afford = False
            if self.drone:
                 can_afford = self.skill_manager.can_unlock(sid, self.drone.inventory)
            
            if node.unlocked:
                text = f"[✓] {text}"
            elif not can_afford:
                text = f"[LOCKED]"
            
            # Format Cost
            cost_str = ", ".join([f"{v} {k.capitalize()}" for k,v in node.cost.items()])
            
            btn = pygame_gui.elements.UIButton(
                relative_rect=rect,
                text=text,
                manager=self.manager,
                container=self.window,
                tool_tip_text=f"{node.description}\nCost: {cost_str}"
            )
            # monkey patch id
            btn.skill_id = sid
            self.buttons[btn] = node

    def refresh(self):
        # Simple rebuild
        for btn in self.buttons:
            btn.kill()
        self.buttons = {}
        self._build_ui()
