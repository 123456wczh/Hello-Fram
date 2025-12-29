import pygame
from src.config import *
import random

class DialogBox:
    def __init__(self, visual_manager=None):
        self.visual_manager = visual_manager
        self.active = False
        self.text = ""
        self.display_text = ""
        self.char_index = 0
        self.typing_speed = 2 # chars per frame
        self.timer = 0
        
        # Use default system font to guarantee rendering if Consolas fails
        self.font = pygame.font.Font(None, 24) 
        self.font_bold = pygame.font.Font(None, 24)
        self.font_bold.set_bold(True)
        
        # Appearance
        self.rect = pygame.Rect(100, SCREEN_HEIGHT - 160, SCREEN_WIDTH - 200, 140)
        self.bg_color = (10, 15, 20, 230) # Dark semi-transparent
        self.border_color = (0, 255, 200) # Cyan cyberpunk-ish

        
        self.speaker = "SYSTEM"
        self.waiting_for_input = False

    def show(self, speaker, text):
        self.active = True
        self.speaker = speaker
        self.text = text
        self.display_text = ""
        self.char_index = 0
        self.waiting_for_input = False
        self.timer = 0

    def update(self):
        if not self.active: return
        
        if self.char_index < len(self.text):
            self.timer += 1
            if self.timer % 2 == 0: # Speed control
                self.char_index += 1
                self.display_text = self.text[:self.char_index]
                if self.visual_manager and self.timer % 4 == 0: # Play every other char to avoid machine gun
                    self.visual_manager.play_sound("blip")
        else:
            self.waiting_for_input = True
            # Auto-append " [CLICK]" if no special condition
            if self.waiting_for_input and "CLICK" not in self.display_text and self.speaker != "SYSTEM":
                 self.display_text += " [CLICK]" # UX Hint

    def draw(self, surface):
        if not self.active: return
        
        # Box Background
        s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        s.fill(self.bg_color)
        surface.blit(s, self.rect)
        
        # Border
        pygame.draw.rect(surface, self.border_color, self.rect, 2, border_radius=4)

        
        # Speaker Label
        label_surf = self.font_bold.render(f"[{self.speaker}]", True, self.border_color)
        surface.blit(label_surf, (self.rect.x + 20, self.rect.y + 15))
        
        # Text Content (Rudimentary wrap)
        words = self.display_text.split(' ')
        lines = []
        curr_line = ""
        for word in words:
            test_line = curr_line + word + " "
            if self.font.size(test_line)[0] < self.rect.w - 40:
                curr_line = test_line
            else:
                lines.append(curr_line)
                curr_line = word + " "
        lines.append(curr_line)
        
        y = self.rect.y + 50
        for line in lines:
            txt_surf = self.font.render(line, True, (240, 255, 240))
            surface.blit(txt_surf, (self.rect.x + 20, y))
            y += 25
            
        # Blinking Cursor
        if self.waiting_for_input:
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                pygame.draw.rect(surface, (0, 255, 0), (self.rect.right - 30, self.rect.bottom - 30, 10, 20))


class CutsceneManager:
    def __init__(self, ide_ref):
        self.ide = ide_ref
        self.dialog = DialogBox(ide_ref.visual_manager)
        self.state = "IDLE" 
        self.step = 0
        self.wait_condition = None
        self.triggers_enabled = False # Only listen to triggers after basic tutorial

    def trigger(self, event_name):
        if not self.triggers_enabled: return
        
        # Reactive Events
        if event_name == "skill_unlocked":
             self.dialog.show("AI ASSISTANT", "Genetic template integrated. New seeds available in CROP_FACTORY.")
             self.state = "PLAYING"
             
        elif event_name == "first_harvest":
             if self.step == 9: # Only if waiting for harvest
                 self.next_step()

    def start_intro(self):
        self.state = "PLAYING"
        self.step = 0
        self.next_step()

    def update(self, dt):
        if self.state == "IDLE": return
        
        self.dialog.update()
        
        # Auto-advance for Boot Sequence (Step 1)
        if self.step == 1 and self.dialog.waiting_for_input:
             # Delay slightly then next
             if self.dialog.timer > 60: # Artificial wait
                 self.next_step()
        
        # Check specific wait conditions
        if self.state == "WAITING_ACTION":
            if self.wait_condition == "OPEN_EDITOR":
                if len(self.ide.editor_windows) > 0:
                    self.wait_condition = None
                    self.next_step()

            elif self.wait_condition == "RUN_CODE":
                # Hacky check: has drone moved?
                # Ideally IDE triggers this
                 if self.ide.drone.x != 0 or self.ide.drone.y != 0:
                     self.wait_condition = None
                     self.next_step()
            
            elif self.wait_condition == "PLANT":
                # Check for any crop
                if self.ide.farm.has_any_crop():
                    self.wait_condition = None
                    self.next_step()
            
            elif self.wait_condition == "HARVEST":
                # Handled by trigger usually, or poll inventory
                if self.ide.drone.inventory:
                     self.wait_condition = None
                     self.next_step()

            elif self.wait_condition == "OPEN_GUIDE":
                if self.ide.windows['guide'].window.visible:
                     self.wait_condition = None
                     self.next_step()

    def draw(self, surface):
        if self.state == "IDLE": return
        self.dialog.draw(surface)

    def next_step(self):
        self.step += 1
        self.state = "PLAYING"
        
        if self.step == 1:
            self.dialog.show("SYSTEM", "Boot sequence initiated... Kernel loading... OK.")
        elif self.step == 2:
            self.dialog.show("AI ASSISTANT", "PILOT STATUS: ONLINE. Welcome back. Cryo-sleep duration: 9999 days.")
        elif self.step == 3:
            self.dialog.show("AI ASSISTANT", "Farm infrastructure degraded. Initiating neural interface calibration...")
        elif self.step == 4:
            self.dialog.show("TUTORIAL", "Click the [+] button (Top-Right) to initialize a new Neural Script.")
            self.state = "WAITING_ACTION"
            self.wait_condition = "OPEN_EDITOR"
            self.dialog.waiting_for_input = True # Keep showing text

        elif self.step == 5:
            self.dialog.show("AI ASSISTANT", "Neural pathways synchronized. Executing motor diagnostics...")
        elif self.step == 6:
            self.dialog.show("MISSION", "Enter valid python code to move the drone. Try: drone.move('East')")
            self.state = "WAITING_ACTION"
            self.wait_condition = "RUN_CODE"
        elif self.step == 7:
            self.dialog.show("AI ASSISTANT", "MOVEMENT VERIFIED. Actuator response: optimal. Soil analysis: fertile.")
        elif self.step == 8:
            self.dialog.show("MISSION", "Plant a seed. Try: drone.plant('carrot')")
            self.state = "WAITING_ACTION"
            self.wait_condition = "PLANT"
        elif self.step == 9:
            self.dialog.show("AI ASSISTANT", "Seed planted successfully. Growth cycle initiated. Testing harvester module...")
        elif self.step == 10:
             self.dialog.show("MISSION", "Harvest the crop using: drone.harvest()")
             self.state = "WAITING_ACTION"
             self.wait_condition = "HARVEST"
        elif self.step == 11:
             self.dialog.show("AI ASSISTANT", "HARVEST COMPLETE. Biological matter catalogued. Network uplink: RESTORED.")
        elif self.step == 12:
             self.dialog.show("MISSION", "Click the [GUIDE] button to access the Agricultural Database.")
             self.state = "WAITING_ACTION"
             self.wait_condition = "OPEN_GUIDE"
        elif self.step == 13:
             self.dialog.show("AI ASSISTANT", "AUTHORIZATION CONFIRMED. Full system access granted. The Algorithm Age begins.")
             self.triggers_enabled = True # Enable random triggers
        elif self.step == 14:
             self.dialog.show("AI ASSISTANT", "CALIBRATION COMPLETE. Access standard protocols via [FILES]. The Algorithm Age begins.")
        elif self.step == 15:
             # End
             self.state = "IDLE"
             self.dialog.active = False
             self.triggers_enabled = True

        else:
            self.state = "IDLE"
            self.dialog.active = False

    def handle_event(self, event):
        if self.state == "IDLE": return
        
        # Skip/Next on Click or Space
        if self.state == "PLAYING" and self.dialog.waiting_for_input:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    self.next_step()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    self.next_step()
