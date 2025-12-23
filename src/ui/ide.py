import pygame
import os
import pygame_gui
import threading
import time
import sys
import traceback
from src.config import *
from src.core.farm import Farm
from src.core.api import DroneAPI
from src.core.storage import SaveManager
from src.core.skills import SkillManager
from src.ui.windows import CropGuideWindow, SkillTreeWindow
from src.ui.cutscene import CutsceneManager
from src.ui.visuals import get_visual_manager, Tween, ease_out_back

class GameIDE:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FarmOS v3.0 - Immersive Mode")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Load Custom Theme
        theme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "ui_theme.json")
        self.ui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), theme_path=theme_path)
        
        # --- State ---
        self.editor_visible = False 
        self.editor_x = float(SCREEN_WIDTH) 
        self.active_tab = "main.py"
        self.code_buffers = {
            "main.py": "# FarmOS Automation Script\n# Press TAB to hide/show editor\n\nwhile True:\n    drone.plant('carrot')\n    drone.move('East')\n    drone.harvest()",
            "utils.py": "# Shared logic",
            "scratch.py": "# Test area"
        }

        # --- Systems ---
        self.farm = Farm()
        self.drone = DroneAPI(self.farm, self.print_to_console)
        self.skill_manager = SkillManager()
        self.thread = None

        # --- Visual Integration ---
        self.visual_manager = get_visual_manager()
        self.visual_manager.load_assets()
        self.visual_manager.load_sounds()
        self.global_timer = 0.0

        # --- UI Components ---
        self._init_ui_elements()
        # --- Cutscene System ---
        self.cutscene_mgr = CutsceneManager(self)
        self.cutscene_mgr.start_intro() # Auto-start for now

        # Initialize windows after drone is ready
        self.windows = {
            'guide': CropGuideWindow(self.ui_manager),
            'skills': SkillTreeWindow(self.ui_manager, self.skill_manager, self.drone)
        }

    def _init_ui_elements(self):
        # 1. System Bar (Top Right)
        btn_width = 70
        gap = 5
        # 4 buttons now (Save, Load, Guide, Skills)
        total_w = btn_width * 4 + gap * 3
        start_x = SCREEN_WIDTH - total_w - 20
        
        self.btn_save = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((start_x, 10), (btn_width, 30)),
                                                    text='SAVE', manager=self.ui_manager)
        self.btn_load = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((start_x + btn_width + gap, 10), (btn_width, 30)),
                                                    text='LOAD', manager=self.ui_manager)
        self.btn_guide = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((start_x + (btn_width + gap)*2, 10), (btn_width, 30)),
                                                    text='GUIDE', manager=self.ui_manager)
        self.btn_skills = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((start_x + (btn_width + gap)*3, 10), (btn_width, 30)),
                                                    text='SKILLS', manager=self.ui_manager)

        # 2. Inventory HUD (Custom Rendered, no GUI element)
        # Removed UITextBox to prevent visual clutter
        pass

        # 3. Editor Panel (Right Side Container)
        self.panel_rect = pygame.Rect(SCREEN_WIDTH - UI_PANEL_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)
        self.editor_panel = pygame_gui.elements.UIPanel(
            relative_rect=self.panel_rect,
            manager=self.ui_manager,
            starting_height=2
        )
        
        self.rebuild_tabs()
        
        # 4. Code Entry (Inside Editor Panel)
        # Squeeze height to fit console at bottom
        editor_height = SCREEN_HEIGHT - 200 
        self.code_editor = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((10, 50), (UI_PANEL_WIDTH - 20, editor_height)),
            initial_text=self.code_buffers[self.active_tab],
            manager=self.ui_manager,
            container=self.editor_panel
        )

        # 5. Run Button
        self.btn_run = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 50 + editor_height + 5), (UI_PANEL_WIDTH - 20, 35)),
            text='RUN (CTRL+ENTER)',
            manager=self.ui_manager,
            container=self.editor_panel
        )
        
        # 6. Console (Inside Panel at Bottom)
        self.console_output = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((10, 50 + editor_height + 45), (UI_PANEL_WIDTH - 20, SCREEN_HEIGHT - (50 + editor_height + 55))),
            html_text="<font color='#00FF00'>System Ready.</font>",
            manager=self.ui_manager,
            container=self.editor_panel
        )
        
        # Start Hidden
        self.editor_panel.hide()

    def rebuild_tabs(self):
        # Clear existing tabs
        if hasattr(self, 'tab_buttons'):
            for btn in self.tab_buttons:
                btn.kill()
        if hasattr(self, 'btn_add_tab'):
            self.btn_add_tab.kill()
        if hasattr(self, 'btn_del_tab'):
            self.btn_del_tab.kill()

        self.tab_buttons = []
        tab_w = 70
        
        # Create buttons
        keys = list(self.code_buffers.keys())
        for i, filename in enumerate(keys):
            # Highlight active? (pygame_gui select maybe, or just color)
            text = filename
            if filename == self.active_tab:
                text = f"[{filename}]"
                
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((10 + i*(tab_w+5), 10), (tab_w, 30)),
                text=text,
                manager=self.ui_manager,
                container=self.editor_panel
            )
            btn.filename = filename # Monkey patch for id
            self.tab_buttons.append(btn)
            
        # [+] Button
        self.btn_add_tab = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10 + len(keys)*(tab_w+5), 10), (30, 30)),
            text='+',
            manager=self.ui_manager,
            container=self.editor_panel
        )
        
        # [x] Button (Far right of tabs line)
        self.btn_del_tab = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((UI_PANEL_WIDTH - 40, 10), (30, 30)),
            text='x',
            manager=self.ui_manager,
            container=self.editor_panel
        )

    def toggle_editor(self):
        self.editor_visible = not self.editor_visible
        if self.editor_visible:
            self.editor_panel.show()
            self.editor_panel.set_position((SCREEN_WIDTH - UI_PANEL_WIDTH, 0))
        else:
            self.editor_panel.hide()

    def switch_tab(self, filename):
        # Save current buffer
        self.code_buffers[self.active_tab] = self.code_editor.get_text()
        # Switch
        self.active_tab = filename
        self.code_editor.set_text(self.code_buffers[filename])

    def print_to_console(self, text):
        self.console_output.append_html_text(f"{text}<br>")
        if self.console_output.scroll_bar:
            self.console_output.scroll_bar.scroll_position = self.console_output.scroll_bar.bottom_limit
        # Audio feedback for console logging
        self.visual_manager.play_sound("blip")

    def update_inventory_ui(self):
        # No longer updating a UI element, logic moved to draw_game_area
        pass

    def run_user_code(self):
        # Update buffer
        self.code_buffers[self.active_tab] = self.code_editor.get_text()
        code = self.code_editor.get_text()
        
        if self.thread and self.thread.is_alive():
            self.drone._stop_flag = True
            self.thread.join(timeout=1.0)
        
        self.drone._stop_flag = False
        self.console_output.set_text("")
        self.print_to_console("<font color='#00FF00'>--- Executing Sequence ---</font>")

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

    def process_drone_events(self):
        while self.drone.events:
            event = self.drone.events.pop(0)
            
            # Recalculate center based on visibility
            view_width = SCREEN_WIDTH
            if self.editor_visible:
                view_width = SCREEN_WIDTH - UI_PANEL_WIDTH
            
            start_x = (view_width - self.farm.width * GRID_SIZE) // 2
            start_y = (SCREEN_HEIGHT - self.farm.height * GRID_SIZE) // 2
            
            # ... rest is same
            grid_x, grid_y = event.get("x"), event.get("y")
            screen_x = start_x + grid_x * GRID_SIZE + GRID_SIZE // 2
            screen_y = start_y + grid_y * GRID_SIZE + GRID_SIZE // 2

            if event["type"] == "move":
                self.visual_manager.add_tween(Tween(self.drone, "visual_x", float(grid_x), 0.2))
                self.visual_manager.add_tween(Tween(self.drone, "visual_y", float(grid_y), 0.2))
            
            elif event["type"] == "plant":
                self.visual_manager.spawn_poof(screen_x, screen_y)
                self.visual_manager.spawn_floating_text(screen_x, screen_y - 30, f"Planted {event['name']}", (100, 255, 100))
                self.visual_manager.play_sound("pop")
            
            elif event["type"] == "harvest":
                self.visual_manager.spawn_spark(screen_x, screen_y)
                self.visual_manager.spawn_floating_text(screen_x, screen_y - 30, f"+1 {event['name']}", (255, 215, 0))
                self.visual_manager.play_sound("ding")

    def draw_game_area(self):
        # Squeeze Logic
        view_width = SCREEN_WIDTH
        if self.editor_visible:
            view_width = SCREEN_WIDTH - UI_PANEL_WIDTH
        
        view_rect = pygame.Rect(0, 0, view_width, SCREEN_HEIGHT)

        # Draw Background
        self.window.fill(COLOR_GAME_BG, view_rect) # Only fill visible part
        # Fill the rest (under panel) with black/dark to avoid artifacts if panel is transparent
        if self.editor_visible:
            self.window.fill((30, 30, 30), (view_width, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT))

        
        # Center the Farm Grid in the VIEW view_rect
        center_x = view_width // 2
        center_y = SCREEN_HEIGHT // 2
        
        start_x = center_x - (self.farm.width * GRID_SIZE) // 2
        start_y = center_y - (self.farm.height * GRID_SIZE) // 2
        
        tile_img = self.visual_manager.get_asset("tile_grass")
        
        # 1. Tiles & Crops
        for y in range(self.farm.height):
            for x in range(self.farm.width):
                rect_x = start_x + x * GRID_SIZE
                rect_y = start_y + y * GRID_SIZE
                
                # Tile
                self.window.blit(tile_img, (rect_x, rect_y))
                # Grid line (subtle)
                pygame.draw.rect(self.window, (80, 100, 120), (rect_x, rect_y, GRID_SIZE, GRID_SIZE), 1)
                
                # Crop
                crop = self.farm.grid[y][x]
                if crop:
                    growth_ratio = crop.current_growth / crop.max_growth if crop.max_growth > 0 else 0
                    stage = min(4, int(growth_ratio * 3) + 1)
                    asset_name = f"crop_{crop.name.lower()}_stage{stage}"
                    crop_img = self.visual_manager.get_asset(asset_name)
                    
                    # Center
                    crop_rect = crop_img.get_rect(center=(rect_x + GRID_SIZE // 2, rect_y + GRID_SIZE // 2))
                    self.window.blit(crop_img, crop_rect)

        # 2. Drone
        d_visual_x = start_x + self.drone.visual_x * GRID_SIZE
        d_visual_y = start_y + self.drone.visual_y * GRID_SIZE
        drone_img = self.visual_manager.get_animated_asset("drone_idle", self.global_timer, speed=15)
        
        # Adjust center
        drone_rect = drone_img.get_rect(center=(d_visual_x + GRID_SIZE // 2, d_visual_y + GRID_SIZE // 2))
        self.window.blit(drone_img, drone_rect)
        
        # 3. Particles
        self.visual_manager.draw(self.window)
        
        # 4. Cutscene Overlay
        self.cutscene_mgr.draw(self.window)

        # 5. Custom HUD (Top Left)
        if not hasattr(self, 'font_hud'):
             self.font_hud = pygame.font.SysFont("Consolas", 18, bold=True)
        
        lines = [
            ("FARM OS V3.2", (100, 200, 255)),
            (f"STATUS: ONLINE", (50, 255, 50)),
            ("INVENTORY:", (200, 200, 200))
        ]
        if not self.drone.inventory:
            lines.append(("  Empty", (150, 150, 150)))
        else:
            for k, v in self.drone.inventory.items():
                lines.append((f"  • {k.upper()}: {v}", (255, 255, 255)))
        
        hud_x, hud_y = 20, 20
        for text, color in lines:
            # Shadow
            s_surf = self.font_hud.render(text, True, (0, 0, 0))
            self.window.blit(s_surf, (hud_x + 2, hud_y + 2))
            # Text
            t_surf = self.font_hud.render(text, True, color)
            self.window.blit(t_surf, (hud_x, hud_y))
            hud_y += 20


    def run(self):
        while self.running:
            time_delta = self.clock.tick(60) / 1000.0
            self.global_timer += time_delta
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                self.ui_manager.process_events(event)
                self.cutscene_mgr.handle_event(event)
                
                # Hotkeys
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F5:
                        self.cutscene_mgr.start_intro() # For testing cutscene
                    if event.key == pygame.K_RETURN and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.run_user_code()
                    if event.key == pygame.K_TAB:
                        self.toggle_editor()

                # UI Events
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.btn_run:
                        self.run_user_code()
                    elif event.ui_element == self.btn_save:
                        SaveManager.save_game(self.farm, self.drone, self.code_editor.get_text())
                        self.print_to_console("<font color='#FFFF00'>System Saved.</font>")
                    elif event.ui_element == self.btn_load:
                        loaded = SaveManager.load_game(self.farm, self.drone)
                        if loaded:
                            self.code_editor.set_text(loaded)
                            self.code_buffers[self.active_tab] = loaded
                            self.print_to_console("<font color='#FFFF00'>System Loaded.</font>")
                    
                    elif event.ui_element == self.btn_guide:
                         if not self.windows['guide'].window.alive():
                             self.windows['guide'] = CropGuideWindow(self.ui_manager)
                         self.windows['guide'].show()
                         
                    elif event.ui_element == self.btn_skills:
                         if not self.windows['skills'].window.alive():
                             self.windows['skills'] = SkillTreeWindow(self.ui_manager, self.skill_manager, self.drone)
                         self.windows['skills'].show()
                    
                    # Tab Logic
                    elif event.ui_element == self.btn_add_tab:
                         new_name = f"script_{len(self.code_buffers)}.py"
                         self.code_buffers[new_name] = "# New Script\n"
                         self.switch_tab(new_name)
                         self.rebuild_tabs()
                    
                    elif event.ui_element == self.btn_del_tab:
                         if len(self.code_buffers) > 1:
                             del self.code_buffers[self.active_tab]
                             self.active_tab = list(self.code_buffers.keys())[0]
                             self.code_editor.set_text(self.code_buffers[self.active_tab])
                             self.rebuild_tabs()
                         else:
                             self.print_to_console("Cannot delete last tab.")

                             if event.ui_element == btn:
                                 self.switch_tab(btn.filename)
                                 self.rebuild_tabs() # Refresh to update [Active] bracket
                    
                    # Check Skill Tree Buttons
                    if self.windows['skills'].window.alive():
                         for btn in self.windows['skills'].buttons:
                             if event.ui_element == btn:
                                 sid = btn.skill_id
                                 if self.skill_manager.unlock(sid, self.drone.inventory):
                                     self.print_to_console(f"<font color='#00FF00'>Unlocked System: {self.skill_manager.get_skill(sid).name}</font>")
                                     self.visual_manager.play_sound("ding") # Achievement sound
                                     self.windows['skills'].refresh() # Rebuild UI
                                     # Trigger Onboarding Event for Unlock
                                     self.cutscene_mgr.trigger("skill_unlocked")
                                 else:
                                     self.print_to_console(f"<font color='#FF0000'>Insufficient Biomass.</font>")
            
            self.ui_manager.update(time_delta)
            self.cutscene_mgr.update(time_delta)
            self.farm.update(time_delta)
            self.visual_manager.update(time_delta)
            self.process_drone_events()
            self.update_inventory_ui()
            
            # Draw
            self.draw_game_area()
            self.ui_manager.draw_ui(self.window) 
            pygame.display.flip()

        if self.thread:
            self.drone._stop_flag = True
        pygame.quit()
        sys.exit()
