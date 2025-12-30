import pygame
import os
import pygame_gui
import threading
import time
import sys
import traceback
from src.config import *
from src.core.farm import Farm
from src.entities.crops import Pumpkin, OccupiedSlot
from src.core.api import DroneAPI
from src.core.storage import SaveManager
from src.core.skills import SkillManager
from src.ui.windows import (
    CropGuideWindow,
    SkillTreeWindow,
    CropDetailWindow,
    CodeEditorWindow,
    NewFileModal,
    FileBrowserWindow,
)
from src.ui.cutscene import CutsceneManager
from src.ui.visuals import get_visual_manager, Tween, ease_out_back


class GameIDE:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Code Farm: The Algorithm Age")

        pygame.key.set_repeat(500, 50)

        # Managers
        theme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets",
            "ui_theme.json",
        )
        self.ui_manager = pygame_gui.UIManager(
            (SCREEN_WIDTH, SCREEN_HEIGHT), theme_path=theme_path
        )

        # --- Preload Fonts to avoid UserWarnings ---
        # Format: {'name': 'font_name', 'point_size': size, 'style': 'style'}
        self.ui_manager.add_font_paths("noto_sans", "assets/fonts/NotoSans-Regular.ttf")
        self.ui_manager.preload_fonts(
            [
                {"name": "noto_sans", "point_size": 14, "style": "bold"},
                {"name": "noto_sans", "point_size": 10, "style": "regular"},
                {"name": "noto_sans", "point_size": 10, "style": "bold"},
            ]
        )

        self.visual_manager = get_visual_manager()
        self.visual_manager.load_assets()
        self.visual_manager.load_sounds()
        self.global_timer = 0.0

        self.farm = Farm()
        self.drone = DroneAPI(self.farm, self.print_to_console)
        self.skill_manager = SkillManager()

        # Attract Mode State
        self.demo_active = False
        self.last_input_time = 0.0

        # --- Editor State ---
        self.editor_windows = []
        self.aux_windows = []

        self.clock = pygame.time.Clock()

        self.running = True

        self.thread = None

        # --- UI Components ---
        self.editor_visible = False  # Start hidden
        self._init_ui_elements()

        # --- Cutscene ---
        self.cutscene_mgr = CutsceneManager(self)
        self.cutscene_mgr.start_intro()

        # Initialize Main Windows (Stacked)
        spawn_files = {
            "main.py": "# FarmOS Automation Script\n# Press TAB to hide/show editor\n\nwhile True:\n    drone.plant('carrot')\n    drone.move('East')\n    drone.harvest()",
            "utils.py": "# Shared logic\nprint('Utils Loaded')",
            "scratch.py": "# Test area\n# Quick experiments here",
        }

        for fname, fcode in spawn_files.items():
            self.editor_windows.append(
                CodeEditorWindow(self.ui_manager, fname, fcode, self)
            )

        # Hide all initially
        for win in self.editor_windows:
            win.hide()

        self.windows = {
            "guide": CropGuideWindow(self.ui_manager),
            "skills": SkillTreeWindow(self.ui_manager, self.skill_manager, self.drone),
        }

    def run_user_code(self, code_string=None, on_finish=None):
        code = code_string if code_string else ""

        if self.thread and self.thread.is_alive():
            self.drone._stop_flag = True
            self.thread.join(timeout=1.0)

        self.drone._stop_flag = False
        if self.console_output:
            self.console_output.set_text("")
        self.print_to_console("<font color='#00FF00'>--- Executing Sequence ---</font>")

        def target():
            env = {"drone": self.drone, "time": time, "print": self.drone.log}
            try:
                exec(code, env)
            except SystemExit:
                pass
            except Exception as e:
                self.print_to_console(f"<font color='#FF0000'>Error: {e}</font>")
                traceback.print_exc()
            finally:
                if on_finish:
                    on_finish()

        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()

    def start_demo(self):
        """Standard Demo Script using Native Runner"""
        DEMO_SCRIPT = """
print("--- PROTOCOL: TACTICAL AGRICULTURE ---")

# Setup: 3x3 Mega Pumpkin Array
start_x, start_y = 2, 2

# Phase 1: Precision Planting
print(">> PHASE 1: SEEDING MATRIX (2,2)")

# Move to start
while drone.x < start_x: drone.move("East")
while drone.y < start_y: drone.move("South")

for r in range(3):
    for c in range(3):
        # drone.destroy() # Removed optimization
        drone.plant("pumpkin")
        if c < 2: drone.move("East")
    
    # Return to start of next row
    if r < 2:
        drone.move("South")
        drone.move("West"); drone.move("West")

# Phase 2: Growth & Fusion Overwatch
print(">> PHASE 2: FUSION OVERWATCH (15s)")
print("   Hold position for biological synthesis...")

# Patrol Pattern: Scan perimeter
for i in range(5):
    # Box Patrol: E->E->S->S->W->W->N->N
    drone.move("East"); drone.move("East")
    drone.move("South"); drone.move("South")
    drone.move("West"); drone.move("West")
    drone.move("North"); drone.move("North")
    
    # Visual check wiggle
    drone.move("East"); drone.move("West")

# Phase 3: Harvest
print(">> PHASE 3: HARVEST OPERATIONS")
# Move to center of mass (3,3)
drone.move("East"); drone.move("South") 

drone.harvest()
print("   TARGET ACQUIRED.")
print("--- MISSION COMPLETE ---")
"""

        # Spawn window for demo
        win = CodeEditorWindow(self.ui_manager, "demo_tactical.py", DEMO_SCRIPT, self)
        self.editor_windows.append(win)
        win.show()  # Ensure visible
        self.demo_active = True

        def on_demo_done():
            self.demo_active = False
            self.print_to_console("Demo Complete.")

        self.run_user_code(code_string=DEMO_SCRIPT, on_finish=on_demo_done)

    def _init_ui_elements(self):
        # 1. System Buttons
        # Examples Button (New V4.0) & File System
        # Layout: [FILES] [+] ... [DEMOS] [SAVE] [LOAD] [GUIDE] [SKILLS]

        # Adjust start_x to fit more buttons
        # 4 Right Buttons + Demos + Files + Plus = 7 buttons total?
        # Let's group them:
        # Left Group: [FILES] [+]
        # Right Group: [DEMOS] [SAVE] [LOAD] [GUIDE] [SKILLS]

        # Button Group (Right Aligned)
        # Order: [FILES] [+] [SAVE] [LOAD] [GUIDE] [SKILLS]
        # Widths: 70, 30, 70, 70, 70, 70
        btn_w = 70
        gap = 5

        # Calculate valid starting X
        total_w = (btn_w * 5) + 30 + (gap * 5)  # 5 standard buttons + 1 small (+)
        start_x = SCREEN_WIDTH - total_w - 20

        current_x = start_x

        self.btn_files = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((current_x, 10), (70, 30)),
            text="FILES",
            manager=self.ui_manager,
        )
        current_x += 70 + gap

        self.btn_new_file = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((current_x, 10), (30, 30)),
            text="+",
            manager=self.ui_manager,
        )
        current_x += 30 + gap

        self.btn_save = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((current_x, 10), (btn_w, 30)),
            text="SAVE",
            manager=self.ui_manager,
        )
        current_x += btn_w + gap

        self.btn_load = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((current_x, 10), (btn_w, 30)),
            text="LOAD",
            manager=self.ui_manager,
        )
        current_x += btn_w + gap

        self.btn_guide = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((current_x, 10), (btn_w, 30)),
            text="GUIDE",
            manager=self.ui_manager,
        )
        current_x += btn_w + gap

        self.btn_skills = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((current_x, 10), (btn_w, 30)),
            text="SKILLS",
            manager=self.ui_manager,
        )

        # 2. Editor Panel
        # Create a Console Window
        # Create a Console Window (Simplified)
        self.console_output = None

        # Note: Editor Windows spawned above handle their own buttons.

    def print_to_console(self, text):
        if not self.console_output:
            return
        self.console_output.append_html_text(f"{text}<br>")
        if self.console_output.scroll_bar:
            self.console_output.scroll_bar.scroll_position = (
                self.console_output.scroll_bar.bottom_limit
            )
        self.visual_manager.play_sound("blip")

    def process_drone_events(self):
        while self.drone.events:
            event = self.drone.events.pop(0)

            view_width = SCREEN_WIDTH  # Full screen, ignoring editor state

            start_x = (view_width - self.farm.width * GRID_SIZE) // 2
            start_y = (SCREEN_HEIGHT - self.farm.height * GRID_SIZE) // 2

            grid_x, grid_y = event.get("x"), event.get("y")
            screen_x = start_x + grid_x * GRID_SIZE + GRID_SIZE // 2
            screen_y = start_y + grid_y * GRID_SIZE + GRID_SIZE // 2

            if event["type"] == "move":
                self.visual_manager.add_tween(
                    Tween(self.drone, "visual_x", float(grid_x), 0.2)
                )
                self.visual_manager.add_tween(
                    Tween(self.drone, "visual_y", float(grid_y), 0.2)
                )

            elif event["type"] == "plant":
                self.visual_manager.spawn_poof(screen_x, screen_y)
                self.visual_manager.spawn_floating_text(
                    screen_x, screen_y - 30, f"Planted {event['name']}", (100, 255, 100)
                )
                self.visual_manager.play_sound("pop")

            elif event["type"] == "harvest":
                self.visual_manager.spawn_spark(screen_x, screen_y)
                self.visual_manager.spawn_floating_text(
                    screen_x, screen_y - 30, f"+1 {event['name']}", (255, 215, 0)
                )
                self.visual_manager.play_sound("ding")

    def draw_game_area(self):
        view_width = SCREEN_WIDTH
        view_rect = pygame.Rect(0, 0, view_width, SCREEN_HEIGHT)

        # Clear ENTIRE window to prevent trails/hall of mirrors
        self.window.fill(COLOR_GAME_BG)  # Fill everything

        # Grid
        start_x = (view_width - (self.farm.width * GRID_SIZE)) // 2
        start_y = (SCREEN_HEIGHT - (self.farm.height * GRID_SIZE)) // 2

        tile_img = self.visual_manager.get_asset("tile_grass")

        # Pass 1: Background Tiles
        for y in range(self.farm.height):
            for x in range(self.farm.width):
                r_x, r_y = start_x + x * GRID_SIZE, start_y + y * GRID_SIZE
                self.window.blit(tile_img, (r_x, r_y))
                pygame.draw.rect(
                    self.window, (80, 100, 120), (r_x, r_y, GRID_SIZE, GRID_SIZE), 1
                )

        # Pass 2: Crops
        for y in range(self.farm.height):
            for x in range(self.farm.width):
                r_x, r_y = start_x + x * GRID_SIZE, start_y + y * GRID_SIZE

                crop = self.farm.grid[y][x]
                if crop and not isinstance(crop, OccupiedSlot):
                    base_name = crop.name.lower()
                    scale = 1
                    is_rotten = False

                    if isinstance(crop, Pumpkin):
                        base_name = "pumpkin"
                        scale = crop.level
                        is_rotten = crop.is_rotten

                    stage = min(4, int((crop.current_growth / crop.max_growth) * 3) + 1)
                    img = self.visual_manager.get_asset(
                        f"crop_{base_name}_stage{stage}"
                    )

                    if img:
                        target_size = int(GRID_SIZE * scale)
                        # ensure pixel perfect fit
                        if img.get_width() != target_size:
                            img = pygame.transform.scale(
                                img, (target_size, target_size)
                            )

                        if is_rotten:
                            img = img.copy()
                            img.fill((80, 50, 30), special_flags=pygame.BLEND_MULT)

                        # Blit Top-Left aligned to grid
                        r_x = start_x + x * GRID_SIZE
                        r_y = start_y + y * GRID_SIZE
                        self.window.blit(img, (r_x, r_y))

                        # Debug Border for Mega Crops
                        if scale > 1:
                            pygame.draw.rect(
                                self.window,
                                (255, 215, 0),
                                (r_x, r_y, target_size, target_size),
                                2,
                            )

        # Drone
        d_x = start_x + self.drone.visual_x * GRID_SIZE
        d_y = start_y + self.drone.visual_y * GRID_SIZE
        drone_img = self.visual_manager.get_animated_asset(
            "drone_idle", self.global_timer, speed=15
        )
        self.window.blit(
            drone_img,
            drone_img.get_rect(center=(d_x + GRID_SIZE // 2, d_y + GRID_SIZE // 2)),
        )

        self.visual_manager.draw(self.window)
        self.cutscene_mgr.draw(self.window)

        # HUD
        if not hasattr(self, "font_hud"):
            self.font_hud = pygame.font.SysFont("Consolas", 18, bold=True)
        lines = [("FARM OS V3.2", (100, 200, 255)), ("STATUS: ONLINE", (50, 255, 50))]
        for k, v in self.drone.inventory.items():
            lines.append((f"  • {k.upper()}: {v}", (255, 255, 255)))

        hy = 20
        for txt, col in lines:
            self.window.blit(self.font_hud.render(txt, True, (0, 0, 0)), (22, hy + 2))
            self.window.blit(self.font_hud.render(txt, True, col), (20, hy))
            hy += 20

    def get_screen_coords(self, grid_x, grid_y):
        view_width = (
            SCREEN_WIDTH - UI_PANEL_WIDTH if self.editor_visible else SCREEN_WIDTH
        )
        start_x = (view_width - self.farm.width * GRID_SIZE) // 2
        start_y = (SCREEN_HEIGHT - self.farm.height * GRID_SIZE) // 2

        screen_x = start_x + grid_x * GRID_SIZE + GRID_SIZE // 2
        screen_y = start_y + grid_y * GRID_SIZE + GRID_SIZE // 2

        return screen_x, screen_y

    def handle_input_activity(self):
        """Reset idle timer on any input. Do NOT auto-stop showcase."""
        self.last_input_time = self.global_timer

    def run(self):
        clock = pygame.time.Clock()
        self.running = True

        while self.running:
            dt = clock.tick(60) / 1000.0
            self.global_timer += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                # Wake up on any interaction
                if event.type in (
                    pygame.KEYDOWN,
                    pygame.MOUSEBUTTONDOWN,
                    pygame.MOUSEMOTION,
                ):
                    self.handle_input_activity()

                try:
                    self.ui_manager.process_events(event)
                except Exception as e:
                    if "container_to_scroll" not in str(e):
                        print(f"UI Error: {e}")

                self.cutscene_mgr.handle_event(event)

                if event.type == pygame.KEYDOWN:
                    # Showcase Abort
                    if self.demo_active and (
                        event.key == pygame.K_ESCAPE or event.key == pygame.K_q
                    ):
                        self.drone._stop_flag = True
                        self.editor_visible = True
                        self.editor_panel.show()
                        self.print_to_console("Showcase Cancelled.")

                    elif event.key == pygame.K_F5:
                        self.cutscene_mgr.start_intro()
                    elif event.key == pygame.K_F12:
                        self.start_demo()

                    elif event.key == pygame.K_F1:
                        if self.cutscene_mgr.state != "IDLE":
                            self.cutscene_mgr.state = "IDLE"
                            self.cutscene_mgr.dialog.active = False

                    elif event.key == pygame.K_F1:
                        if self.cutscene_mgr.state != "IDLE":
                            self.cutscene_mgr.state = "IDLE"
                            self.cutscene_mgr.dialog.active = False

                    # (TAB toggling removed - using buttons now)

                    else:
                        if not self.demo_active:

                            # Forward key events to focused window?
                            # Not strictly necessary as CodeEditorWindow checks focus via its own handle_event
                            # But we call handle_event loop below
                            pass

                # Global Window Event Delegation
                # Global Window Event Delegation
                for win in self.editor_windows:
                    win.handle_event(event)

                # Aux Windows Event Delegation
                for win in self.aux_windows:
                    win.handle_event(event)

                # Window Close Handling
                if event.type == pygame_gui.UI_WINDOW_CLOSE:
                    # Check if it's one of our editor windows
                    to_remove = None
                    for win in self.editor_windows:
                        if event.ui_element == win.window:
                            to_remove = win
                            break

                    if to_remove:
                        to_remove.destroy()  # Explicit cleanup of children
                        self.editor_windows.remove(to_remove)
                        self.print_to_console(f"Closed {to_remove.filename}.")

                    # Check Aux Windows (Modals)
                    to_remove_aux = None
                    for win in self.aux_windows:
                        if event.ui_element == win.window:
                            to_remove_aux = win
                            break
                    if to_remove_aux:
                        to_remove_aux.destroy()
                        self.aux_windows.remove(to_remove_aux)

                # UI Button Handling
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    # 1. Check Editor Windows (Run/Save)
                    handled_editor = False
                    for win in self.editor_windows:
                        if event.ui_element == win.btn_run:
                            self.run_user_code(code_string=win.text_box.get_text())
                            handled_editor = True
                            break
                        elif event.ui_element == win.btn_save:
                            if win.save_to_disk():
                                self.print_to_console(f"Saved {win.filename} to disk.")
                            else:
                                self.print_to_console(f"Error saving {win.filename}.")
                            handled_editor = True
                            break

                        elif (
                            hasattr(win, "btn_stop")
                            and event.ui_element == win.btn_stop
                        ):
                            self.drone._stop_flag = True
                            self.print_to_console(
                                f"<font color='#FFA500'>Station: Stopped {win.filename}.</font>"
                            )
                            handled_editor = True
                            break

                    # 2. Check System Buttons (Only if not editor button)
                    if not handled_editor:
                        if event.ui_element == self.btn_save:
                            # Global save
                            SaveManager.save_game(
                                self.farm, self.drone, ""
                            )  # Empty code?
                            self.print_to_console("Farm State Saved.")

                        elif event.ui_element == self.btn_load:
                            l = SaveManager.load_game(self.farm, self.drone)
                            if l:
                                self.print_to_console("Loaded Farm State.")

                        elif event.ui_element == self.btn_guide:
                            if not self.windows["guide"].window.alive():
                                self.windows["guide"] = CropGuideWindow(self.ui_manager)
                            self.windows["guide"].show()

                        elif event.ui_element == self.btn_skills:
                            if not self.windows["skills"].window.alive():
                                self.windows["skills"] = SkillTreeWindow(
                                    self.ui_manager, self.skill_manager, self.drone
                                )
                            self.windows["skills"].show()

                        elif event.ui_element == self.btn_files:
                            w = FileBrowserWindow(self.ui_manager, self)
                            self.aux_windows.append(w)

                        elif event.ui_element == self.btn_new_file:
                            w = NewFileModal(self.ui_manager, self)
                            self.aux_windows.append(w)

                    # Skill Tree Logic
                    if self.windows["skills"].window.alive():
                        for btn in self.windows["skills"].buttons:
                            if event.ui_element == btn:
                                node = self.windows["skills"].buttons[btn]

                                # 1. Show Details
                                cost_str = ", ".join(
                                    [
                                        f"{v} {k.capitalize()}"
                                        for k, v in node.cost.items()
                                    ]
                                )
                                status_str = (
                                    "<font color='#00FF00'>[UNLOCKED]</font>"
                                    if node.unlocked
                                    else "<font color='#FF4444'>[LOCKED]</font>"
                                )

                                detail_html = f"<b>{node.name}</b> {status_str}<br>"
                                detail_html += f"<i>Cost: {cost_str}</i><br><br>"
                                detail_html += f"{node.description}"

                                self.windows["skills"].desc_box.set_text(detail_html)

                                # 2. Try Unlock
                                if not node.unlocked:
                                    if self.skill_manager.unlock(
                                        btn.skill_id, self.drone.inventory
                                    ):
                                        self.visual_manager.play_sound("ding")
                                        self.windows["skills"].refresh()
                                        self.cutscene_mgr.trigger("skill_unlocked")
                                        # Update text to unlocked
                                        self.windows["skills"].desc_box.set_text(
                                            detail_html.replace(
                                                "LOCKED", "UNLOCKED"
                                            ).replace("#FF4444", "#00FF00")
                                        )
                                    else:
                                        self.visual_manager.play_sound("err")

                            # Check Detail Buttons (Monkey Patched)
                            if hasattr(event.ui_element, "crop_cls"):
                                # Spawn Detail Window
                                btn = event.ui_element
                                # Close existing detail if any? Or allow one.
                                # Let's attach to guide window to track
                                if (
                                    hasattr(self.windows["guide"], "detail_window")
                                    and self.windows["guide"].detail_window
                                    and self.windows[
                                        "guide"
                                    ].detail_window.window.alive()
                                ):
                                    self.windows["guide"].detail_window.window.kill()

                                self.windows["guide"].detail_window = CropDetailWindow(
                                    self.ui_manager, btn.crop_cls, self.visual_manager
                                )
                                self.windows["guide"].detail_window.show()

            # Update UI Manager
            try:
                self.ui_manager.update(dt)
            except Exception as e:
                # Fix GUI Crash by ignoring the specific attribute error
                if (
                    "pressed_event" not in str(e)
                    and "held" not in str(e)
                    and "container_to_scroll" not in str(e)
                ):
                    print(f"GUI Update Error: {e}")

            self.cutscene_mgr.update(dt)

            # Simple State Check for UI Restoration (Falling Edge)
            if self.demo_active and not self.thread.is_alive():
                self.demo_active = False
                self.editor_visible = True
                self.editor_panel.show()
                self.print_to_console("System Control Restored.")

            self.process_drone_events()  # Universal Handler
            self.farm.update(dt)
            self.visual_manager.update(dt)

            self.draw_game_area()

            # Draw Demo Overlay
            if self.demo_active:
                font = getattr(self, "font_hud", None) or pygame.font.SysFont(
                    "Consolas", 24, bold=True
                )
                txt = font.render("ATTRACT MODE - PRESS [ESC]", True, (255, 255, 255))
                self.window.blit(
                    txt, txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
                )

            try:
                self.ui_manager.draw_ui(self.window)
            except Exception as e:
                print(f"GUI Draw Error: {e}")

            pygame.display.flip()

        pygame.quit()
        sys.exit()
