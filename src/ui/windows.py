import pygame
import pygame_gui
from src.config import *
from src.entities.crops import CROP_FACTORY
from src.core.skills import SkillManager
from src.ui.visuals import get_visual_manager
import glob
import os
import shutil


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
            visible=1,  # Initialize visible to avoid UIScrollingContainer init crash
        )
        # Allow shrinking to title bar height
        self.window.set_minimum_dimensions((400, 30))

        # --- Full Window Dragging State ---
        self.is_dragging = False
        self.drag_offset = (0, 0)

        # We can add a "Close" callback if needed, but pygame_gui handles the X button.
        # DO NOT hide here. Container children crash if added to hidden window.

    def show(self):
        self.window.show()

    def hide(self):
        self.window.hide()

    def destroy(self):
        self.window.kill()

    def handle_event(self, event):
        """Handle full-window dragging logic."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left Click
                # Only drag if clicking on the window itself
                if self.window.rect.collidepoint(event.pos):
                    # Check if click was on a specialized element?
                    # pygame_gui elements handle their own but we can check z-index or just 'bg'
                    # For now, let's allow dragging from anywhere unless it's explicitly blocked.
                    self.is_dragging = True
                    start_x, start_y = event.pos
                    self.drag_offset = (
                        self.window.rect.x - start_x,
                        self.window.rect.y - start_y,
                    )

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                new_x, new_y = event.pos
                self.window.set_position(
                    (new_x + self.drag_offset[0], new_y + self.drag_offset[1])
                )


class CodeEditorWindow(BaseModal):
    """
    Independent Code Editor Window.
    Uses UITextEntryBox for native editing (perfect cursor/scrolling) at the cost of syntax highlighting.
    """

    def __init__(self, manager, filename, initial_code, ide_ref):
        offset = len(ide_ref.editor_windows) * 30
        super().__init__(manager, f"Editor: {filename}", 500, 600)

        # Cascade windows
        start_x = SCREEN_WIDTH - 520 - offset
        start_y = 50 + offset
        self.window.set_position((start_x, start_y))

        self.ide = ide_ref
        self.filename = filename

        # --- Manual Undo/Redo Stacks ---
        self.undo_stack = [initial_code]
        self.redo_stack = []
        self._last_pushed_text = initial_code
        self._ignore_changes = False  # Flag to avoid recursion during undo/redo

        self._build_ui()
        self.text_box.set_text(initial_code)

    def _build_ui(self):
        # 1. Editor Text Entry Box (Multiline)
        # This provides native cursor positioning, scrolling, and copy-paste.
        self.text_box = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((10, 10), (480, 500)),
            manager=self.manager,
            container=self.window,
        )

        # 2. Buttons (Bottom)
        self.btn_run = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 520), (100, 35)),
            text="RUN",
            manager=self.manager,
            container=self.window,
        )

        self.btn_save = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((120, 520), (100, 35)),
            text="SAVE",
            manager=self.manager,
            container=self.window,
        )

        self.btn_stop = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((230, 520), (100, 35)),
            text="STOP",
            manager=self.manager,
            container=self.window,
        )

    def handle_event(self, event):
        """Handle keyboard shortcuts and track text changes for Undo/Redo."""
        super().handle_event(event)  # Enable full-window dragging

        # 1. Track Text Changes via USEREVENT from pygame_gui
        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if event.ui_element == self.text_box:
                if not self._ignore_changes:
                    current = self.text_box.get_text()
                    # Only push if meaningful change (prevent excessive stacks)
                    if current != self._last_pushed_text:
                        self.undo_stack.append(current)
                        self._last_pushed_text = current
                        self.redo_stack.clear()  # Clear redo on new edit
                        if len(self.undo_stack) > 100:
                            self.undo_stack.pop(0)

        # 2. Handle Shortcuts
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            is_ctrl = mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META

            if is_ctrl and self.text_box.is_focused:
                if event.key == pygame.K_z:
                    self._perform_undo()
                elif event.key == pygame.K_y:
                    self._perform_redo()

    def _perform_undo(self):
        if len(self.undo_stack) > 1:
            # Current state is top of stack, pop it and move to redo
            self.redo_stack.append(self.undo_stack.pop())
            # Restore previous state
            prev_text = self.undo_stack[-1]

            self._ignore_changes = True
            self.text_box.set_text(prev_text)
            self._last_pushed_text = prev_text
            self._ignore_changes = False

    def _perform_redo(self):
        if self.redo_stack:
            next_text = self.redo_stack.pop()
            self.undo_stack.append(next_text)

            self._ignore_changes = True
            self.text_box.set_text(next_text)
            self._last_pushed_text = next_text
            self._ignore_changes = False

    def save_to_disk(self):
        """Save content from the text box widget to disk."""
        target_dir = "user_scripts"
        filepath = os.path.join(target_dir, self.filename)

        try:
            content = self.text_box.get_text()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Failed to write file {filepath}: {e}")
            return False


class CropDetailWindow(BaseModal):
    """Draggable window showing specific crop details."""

    def __init__(self, manager, crop_cls, visuals):
        super().__init__(manager, f"Analysis: {crop_cls().name}", 400, 300)
        self.crop_cls = crop_cls
        self.visuals = visuals
        self._build_ui()

    def _build_ui(self):
        dummy = self.crop_cls()
        img_surf = self.visuals.get_asset(f"crop_{dummy.name.lower()}_stage4")
        if img_surf:
            img_surf = pygame.transform.scale(img_surf, (96, 96))

        # Layout
        # Top: Icon + Name
        pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect((20, 20), (96, 96)),
            image_surface=img_surf,
            manager=self.manager,
            container=self.window,
        )

        pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((130, 20), (250, 40)),
            html_text=f"<b><font size=6>{dummy.name}</font></b>",
            manager=self.manager,
            container=self.window,
        )

        # Stats
        stats_html = (
            f"<b>Growth Time:</b> {dummy.max_growth}s<br>"
            f"<b>Base Value:</b> ${dummy.value}<br>"
            f"<b>Harvest Yield:</b> 1 unit"
        )
        if dummy.name == "Pumpkin":
            stats_html += "<br><br><b><font color='#FFA500'>[SPECIAL TRAIT: FUSION]</font></b><br>"
            stats_html += "Plant in NxN grid to fuse into Mega structures.<br>Size correlates to exponential value."
        elif dummy.name == "Sunflower":
            stats_html += "<br><br><b><font color='#FFFF00'>[SPECIAL TRAIT: PURIFIER]</font></b><br>"
            stats_html += "Absorbs toxins. Complex root systems."

        pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((130, 70), (250, 200)),
            html_text=stats_html,
            manager=self.manager,
            container=self.window,
        )


class CropGuideWindow(BaseModal):
    def __init__(self, manager):
        super().__init__(manager, "Agricultural Database", 600, 450)
        self.visuals = get_visual_manager()
        self.detail_window = None  # Track child window
        self._build_ui()
        self.hide()  # Safe to hide now that children are added

    def _build_ui(self):
        # Create a scrollable container
        container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect((0, 0), (self.width - 32, self.height - 40)),
            manager=self.manager,
            container=self.window,
        )

        y_offset = 10
        for name, crop_cls in CROP_FACTORY.items():
            # Instantiate dummy to get stats
            dummy = crop_cls()

            # Panel for each crop (Compact)
            panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect((10, y_offset), (540, 70)),
                manager=self.manager,
                container=container,
            )

            # Icon
            asset_name = f"crop_{name}_stage4"
            img_surf = self.visuals.get_asset(asset_name)
            img_surf = pygame.transform.scale(img_surf, (48, 48))

            pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect((10, 11), (48, 48)),
                image_surface=img_surf,
                manager=self.manager,
                container=panel,
            )

            # Text Info
            # Name (Increased W/H to avoid clipping)
            pygame_gui.elements.UITextBox(
                relative_rect=pygame.Rect((70, 8), (250, 35)),
                html_text=f"<b><font size=4>{dummy.name}</font></b>",
                manager=self.manager,
                container=panel,
            )

            # Stats (Simplified, no Value)
            stats = f"Growth Time: {dummy.max_growth}s"
            if name == "pumpkin":
                stats += " | <b>Traits: Fusion</b>"
            if name == "sunflower":
                stats += " | <b>Traits: Purifier</b>"

            pygame_gui.elements.UITextBox(
                relative_rect=pygame.Rect((70, 38), (350, 30)),
                html_text=f"<font color='#DDDDDD' size=2>{stats}</font>",
                manager=self.manager,
                container=panel,
            )

            # Button to open detail
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((460, 15), (70, 40)),
                text="Details",
                manager=self.manager,
                container=panel,
            )
            # Monkey patch
            btn.crop_cls = crop_cls
            btn.object_id = "btn_detail"

            y_offset += 80

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
        # Allocated Area: 760 x 300 (Top section)
        self.bg_surf = pygame.Surface((760, 300), pygame.SRCALPHA)
        self.bg_image = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect((20, 20), (760, 300)),
            image_surface=self.bg_surf,
            manager=self.manager,
            container=self.window,
        )

        # 2. Description Panel (Bottom)
        self.desc_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((20, 330), (760, 140)),
            manager=self.manager,
            container=self.window,
        )
        self.desc_box = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((10, 10), (740, 120)),
            html_text="Select a skill to view details.",
            manager=self.manager,
            container=self.desc_panel,
        )

        # 3. Draw Connections & Place Buttons
        skills = self.skill_manager.skills

        # Define layout area
        area_w = 760
        area_h = 300

        # Helper to get pos
        def get_pos(node):
            return (int(node.x * area_w), int(node.y * area_h))

        # Draw Lines
        self.bg_surf.fill((0, 0, 0, 0))  # Clear
        for sid, node in skills.items():
            if node.parent_id and node.parent_id in skills:
                parent = skills[node.parent_id]
                start = get_pos(parent)
                end = get_pos(node)
                # Offset for button center (approx 20, 15)
                start = (start[0] + 0, start[1] + 15)
                end = (end[0] + 0, end[1] + 15)

                color = (100, 100, 100)
                if parent.unlocked:
                    color = (100, 200, 100)  # Green path

                pygame.draw.line(self.bg_surf, color, start, end, 4)

        self.bg_image.set_image(self.bg_surf)  # Update texture

        # Place Node Buttons
        for sid, node in skills.items():
            px, py = get_pos(node)
            # Center button
            btn_w, btn_h = 140, 40
            rect = pygame.Rect((px - btn_w // 2, py), (btn_w, btn_h))

            # Style based on state
            text = node.name

            # Check unlock status using drone inventory if available
            can_afford = False
            if self.drone:
                can_afford = self.skill_manager.can_unlock(sid, self.drone.inventory)

            if node.unlocked:
                text = f"[V] {text}"
            elif not can_afford:
                # text = f"[LOCKED]" # Show name so user knows what they are aiming for
                pass

            btn = pygame_gui.elements.UIButton(
                relative_rect=rect,
                text=text,
                manager=self.manager,
                container=self.window,
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


class NewFileModal(BaseModal):
    """
    Modal for creating a new file with custom name.
    """

    def __init__(self, manager, ide_ref):
        super().__init__(manager, "Create New File", 400, 160)
        self.ide = ide_ref

        self.lbl_name = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 20), (360, 30)),
            text="Enter Filename (.py):",
            manager=manager,
            container=self.window,
        )

        self.entry_name = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((20, 50), (360, 35)),
            manager=manager,
            container=self.window,
        )
        self.entry_name.set_allowed_characters("letters_digits_plus_underscore_period")

        self.btn_create = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((20, 100), (100, 35)),
            text="Create",
            manager=manager,
            container=self.window,
        )

        self.btn_cancel = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((130, 100), (100, 35)),
            text="Cancel",
            manager=manager,
            container=self.window,
        )

    def on_create(self):
        filename = self.entry_name.get_text()
        if not filename:
            return
        if not filename.endswith(".py"):
            filename += ".py"

        # Check duplicate
        for win in self.ide.editor_windows:
            if win.filename == filename:
                print("Window already exists")
                # Ideally show error standard, but for now just console or ignore
                return

        # Create
        new_win = CodeEditorWindow(
            self.ide.ui_manager, filename, "# New Script\n", self.ide
        )
        self.ide.editor_windows.append(new_win)
        new_win.show()
        self.ide.print_to_console(f"Created {filename}")
        self.destroy()

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_create:
                self.on_create()
            elif event.ui_element == self.btn_cancel:
                self.destroy()


class FileBrowserWindow(BaseModal):
    """
    Browser for opening User Files or Examples.
    """

    def __init__(self, manager, ide_ref):
        super().__init__(manager, "File Browser", 600, 400)  # Widen for 2 cols
        self.ide = ide_ref

        # --- Column 1: My Files ---
        self.lbl_my = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 10), (250, 25)),
            text="My Files (user_scripts/):",
            manager=manager,
            container=self.window,
        )

        # Scan user_scripts
        user_files = []
        if os.path.exists("user_scripts"):
            user_files = [os.path.basename(f) for f in glob.glob("user_scripts/*.py")]

        self.list_my = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect((20, 40), (270, 300)),
            item_list=user_files,
            manager=manager,
            container=self.window,
        )

        # --- Column 2: Examples ---
        self.lbl_ex = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((310, 10), (250, 25)),
            text="Examples (Read Only):",
            manager=manager,
            container=self.window,
        )

        # Scan examples
        ex_files = [os.path.basename(f) for f in glob.glob("src/examples/*.py")]

        self.list_ex = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect((310, 40), (270, 300)),
            item_list=ex_files,
            manager=manager,
            container=self.window,
        )

        self.btn_open = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((480, 350), (100, 35)),
            text="Open",
            manager=manager,
            container=self.window,
        )

    def open_selected(self):
        # Check My Files first
        sel_my = self.list_my.get_single_selection()
        filepath = None
        is_read_only = False

        if sel_my:
            filepath = os.path.join("user_scripts", sel_my)
        else:
            sel_ex = self.list_ex.get_single_selection()
            if sel_ex:
                filepath = os.path.join("src", "examples", sel_ex)
                is_read_only = True  # Examples are reference

        if not filepath:
            return

        filename = os.path.basename(filepath)

        # Check if already open
        for win in self.ide.editor_windows:
            if win.filename == filename:
                win.show()
                win.window.move_to_front()
                self.ide.print_to_console(f"Activated {filename}")
                self.destroy()
                return

        # Load content
        content = ""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Create window
            new_win = CodeEditorWindow(self.ide.ui_manager, filename, content, self.ide)
            self.ide.editor_windows.append(new_win)
            new_win.show()
            self.ide.print_to_console(f"Opened {filename}")
            if is_read_only:
                self.ide.print_to_console(
                    "<font color='#AAAAAA'>(Read Only Mode)</font>"
                )
            self.destroy()
        else:
            print(f"Error: File not found {filepath}")

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_open:
                self.open_selected()
        elif event.type == pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION:
            if event.ui_element == self.list_my or event.ui_element == self.list_ex:
                self.open_selected()
