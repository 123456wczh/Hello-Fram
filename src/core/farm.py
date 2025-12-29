from src.config import GRID_WIDTH, GRID_HEIGHT
from src.entities.crops import CROP_FACTORY, Pumpkin, OccupiedSlot

class Farm:
    def __init__(self):
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        # Grid 存放 Crop 对象或 None
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
    
    def plant_crop(self, x, y, crop_obj):
        if 0 <= x < self.width and 0 <= y < self.height:
            # Prevent planting on occupied slots
            if self.grid[y][x] is None:
                self.grid[y][x] = crop_obj
                return True
        return False

    def harvest_crop(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            crop = self.grid[y][x]
            if crop:
                target_crop = crop
                # Handle Occupied Slot (Redirect to parent)
                if isinstance(crop, OccupiedSlot):
                    px, py = crop.parent_pos
                    parent = self.grid[py][px]
                    if parent and parent == crop.parent:
                        target_crop = parent
                        x, y = px, py
                    else:
                        self.grid[y][x] = None
                        return None
                
                if target_crop.is_ready:
                    # Clear grid using helper
                    self.remove_crop(x, y, target_crop)
                    return target_crop
        return None

    def destroy_crop(self, x, y):
        """Forcefully remove a crop at x,y even if not ready"""
        if 0 <= x < self.width and 0 <= y < self.height:
            crop = self.grid[y][x]
            if crop:
                target_crop = crop
                # Handle Occupied Slot
                if isinstance(crop, OccupiedSlot):
                    px, py = crop.parent_pos
                    parent = self.grid[py][px]
                    if parent and parent == crop.parent:
                        target_crop = parent
                        x, y = px, py
                    else:
                        self.grid[y][x] = None
                        return True
                
                self.remove_crop(x, y, target_crop)
                return True
        return False

    def remove_crop(self, x, y, crop_obj):
        """Internal helper to clear grid slots for a given crop"""
        if isinstance(crop_obj, Pumpkin) and crop_obj.size > 1:
            # Clear all slots for Mega Pumpkin
            for dy in range(crop_obj.size):
                for dx in range(crop_obj.size):
                    if 0 <= y+dy < self.height and 0 <= x+dx < self.width:
                        self.grid[y+dy][x+dx] = None
        else:
            self.grid[y][x] = None
    
    def update(self, dt):
        """让所有作物生长"""
        for y in range(self.height):
            for x in range(self.width):
                crop = self.grid[y][x]
                if crop and not isinstance(crop, OccupiedSlot):
                    crop.grow(dt)
        
        # Check for Infinite Fusion
        self.check_fusion()

    def check_fusion(self):
        used_crops = set() # Track processed root instances to avoid double-processing
        
        # We prefer finding largest squares first to avoid suboptimal greedy consumes?
        # Standard loop (y, x) with greedy K is usually fine if we skip 'used' tiles?
        # Actually, if we have L2+L2+L2+L2 -> L4, the (x,y) of the L4 is the top-left using finding (0,0)?
        
        # We need a 'used_tiles' to skip processed areas in this frame?
        # Actually, just modifying the grid in-place invalidates subsequent checks.
        # But we must be careful.
        # Let's use a restart approach or careful iteration.
        # Since we modify the grid, breaking and waiting for next update frame is simplest/safest.
        # But if we want to fuse multiple distinct blobs, we can continue if we track used tiles.
        
        used_tiles = set()
        
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in used_tiles: continue
                
                # Fast check: Tile must be pumpkin and ready
                c0 = self.grid[y][x]
                if not c0: continue
                
                # Resolve root
                root0 = c0
                if isinstance(c0, OccupiedSlot):
                    # We usually iterate top-left. If we hit an occupied slot, 
                    # its parent might be processed? Or maybe we are scanning inside a mega pumpkin.
                    # We should skip OccupiedSlots and only process from Roots?
                    # NO. User wants L2 + L2. L2 starts at (0,0). (0,1) is occupied.
                    # If we fuse (0,0) to (3,3), we include (0,0).
                    # If we start scan at (0,0), we find the pumpkin.
                    pass
                
                # Logic: Scan for largest valid KxK starting at (x,y)
                max_k = 0
                limit = min(self.width - x, self.height - y)
                
                # Check from K=limit down to 2? Or 2 to limit?
                # User wants "Maximum area".
                # If we have 4x4. We check K=2 (TopLeft). It is valid.
                # If we greedily take K=2, we miss K=4?
                # So we must check locally MAX K.
                
                found_k_size = 0
                
                for k in range(limit, 1, -1): # decreasing k checks for biggest first
                    # Validate Square Area
                    valid_square = True
                    involved_roots = set()
                    
                    for dy in range(k):
                        for dx in range(k):
                            tx, ty = x + dx, y + dy
                            if (tx, ty) in used_tiles:
                                valid_square = False; break
                            
                            tile_c = self.grid[ty][tx]
                            
                            # MUST be Pumpkin-related
                            if not tile_c: 
                                valid_square = False; break
                            
                            r = tile_c
                            is_pumpkin = False
                            if isinstance(r, Pumpkin): is_pumpkin = True
                            elif isinstance(r, OccupiedSlot) and isinstance(r.parent, Pumpkin):
                                r = r.parent
                                is_pumpkin = True
                            
                            if not is_pumpkin:
                                valid_square = False; break
                            
                            # Must be Mature & Healthy
                            # Note: check r (root) for status
                            if not r.is_ready or r.is_rotten:
                                valid_square = False; break
                                
                            involved_roots.add(r)
                            
                        if not valid_square: continue
                    
                    if not valid_square: continue # Try smaller K
                    
                    # INTEGRITY CHECK:
                    # Are all involved_roots FULLY contained in our (x, y, k, k) rect?
                    # We cannot chop a 4x4 pumpkin in half to make a 2x2.
                    # (Although shrinking is physically possible, game logic wise we merge UP not DOWN)
                    integrity_ok = True
                    
                    # Define our rect
                    rect_x1, rect_y1 = x, y
                    rect_x2, rect_y2 = x + k, y + k
                    
                    for root in involved_roots:
                        # Root absolute rect
                        # root is at grid[ry][rx]? No, we need its coords.
                        # We don't store x,y in Pumpkin logic explicitly except implicitly by grid pos?
                        # Wait, OccupiedSlot knows parent_pos.
                        # Pixel/Root Pumpkin doesn't know its own X,Y?
                        # We need to find root pos.
                        # Sol: Iterate involved_roots, find their position? 
                        # Or, ensuring that: Size of involved_roots <= K?
                        # No.
                        # Simple check:
                        # Area of fused rect = K*K.
                        # Sum of areas of roots = ???
                        # If a root spills out, then Sum_Area_Roots > K*K? 
                        # (Since we verified every tile in K*K IS a root part).
                        # If we touch a root, we touch part of it.
                        # If that root has parts outside, then that root is "cut".
                        # How to detect?
                        # For each tile of the root, is it inside our rect?
                        # Getting all tiles of a root is easy: root has .level (size).
                        # But we need root's origin (rx, ry).
                        
                        # We can find root origin by scanning `involved_roots` on grid? Expensive.
                        # Hack: OccupiedSlot stores parent_pos. What if we hit the Root directly?
                        # Root needs to know its own pos?
                        # We can deduce validness:
                        # If 'root' is L2. We must have found 4 tiles pointing to this root.
                        # We simply count 'tiles in selection pointing to root' vs 'root.size^2'.
                        pass
                    
                    # Count frequency of each root in the selection
                    root_counts = {}
                    for dy in range(k):
                        for dx in range(k):
                            tc = self.grid[y+dy][x+dx]
                            r = tc
                            if isinstance(tc, OccupiedSlot): r = tc.parent
                            root_counts[r] = root_counts.get(r, 0) + 1
                    
                    for root, count in root_counts.items():
                        needed = root.size * root.size
                        if count < needed:
                            integrity_ok = False; break
                    
                    if not integrity_ok:
                        continue # Integrity fail, try smaller K?
                        
                    # If we reached here, K is valid and integrity is OK.
                    # PATIENCE CHECK (Perimeter)
                    patience_needed = False
                    min_px, max_px = max(0, x-1), min(self.width, x+k+1)
                    min_py, max_py = max(0, y-1), min(self.height, y+k+1)
                    
                    for py in range(min_py, max_py):
                        for px in range(min_px, max_px):
                            if x <= px < x+k and y <= py < y+k: continue
                            
                            pc = self.grid[py][px]
                            if pc and (isinstance(pc, Pumpkin) or (isinstance(pc, OccupiedSlot) and isinstance(pc.parent, Pumpkin))):
                                # Get root
                                pr = pc
                                if isinstance(pc, OccupiedSlot): pr = pc.parent
                                
                                # Wait if neighbor is GROWING
                                if not pr.is_ready and not pr.is_rotten:
                                    patience_needed = True
                                    break
                        if patience_needed: break
                    
                    if patience_needed:
                        # Valid square but waiting for neighbor.
                        # Stop searching K, wait.
                        break 
                    else:
                        found_k_size = k
                        break # Found max K!
                
                if found_k_size > 0:
                    # Execute Fusion
                    # Check if we are "fusing" a single existing pumpkin? (e.g. 2x2 L2 found as 2x2 sq)
                    # If logic finds 1 root and root.size == k, then we are just effectively detecting the existing pumpkin.
                    # We should skip fusion if result is same level.
                    # UNLESS we are upgrading? But we are fusing area KxK into Level K.
                    # If existing is Level K, No-op.
                    
                    # Check existing composition
                    # We already computed involved_roots and integrity.
                    # If len(involved_roots) == 1 and list(involved_roots)[0].level == found_k_size:
                    #     already fused.
                    
                    # Re-detect singular optimization
                    unique_roots = set()
                    for dy in range(found_k_size):
                        for dx in range(found_k_size):
                            tc = self.grid[y+dy][x+dx]
                            r = tc
                            if isinstance(tc, OccupiedSlot): r = tc.parent
                            unique_roots.add(r)
                            
                    if len(unique_roots) == 1:
                        existing = list(unique_roots)[0]
                        if existing.level == found_k_size:
                            # Already a Level K, skip processing
                            # Mark as used to avoid re-scanning
                             for dy in range(found_k_size):
                                for dx in range(found_k_size):
                                    used_tiles.add((x+dx, y+dy))
                             continue
                    
                    self.fuse_pumpkins(x, y, found_k_size)
                    for dy in range(found_k_size):
                        for dx in range(found_k_size):
                            used_tiles.add((x+dx, y+dy))

    def fuse_pumpkins(self, x, y, size):
        mega = Pumpkin(level=size)
        mega.current_growth = mega.max_growth
        
        self.grid[y][x] = mega
        for dy in range(size):
            for dx in range(size):
                if dx == 0 and dy == 0: continue
                self.grid[y+dy][x+dx] = OccupiedSlot(mega, x, y)

    def to_dict(self):
        grid_data = []
        for y in range(self.height):
            row_data = []
            for x in range(self.width):
                crop = self.grid[y][x]
                if crop:
                    # OccupiedSlot handling?
                    # The demo loads/saves simple logic. 
                    # Complex handling requires saving parent refs or simpler:
                    # Just save the main crops, reconstruct slots on load? Or save slots?
                    # Let's save slots explicitly.
                    row_data.append(crop.to_dict())
                else:
                    row_data.append(None)
            grid_data.append(row_data)
        return grid_data

    def load_from_data(self, grid_data):
        # 1. First pass: Create main crops
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        deferred_slots = []
        
        for y in range(self.height):
            for x in range(self.width):
                cell_data = grid_data[y][x]
                if cell_data:
                    ctype = cell_data.get("type")
                    if ctype == "occupied":
                        # Defer loading occupied slots until parents exist
                        deferred_slots.append((x, y, cell_data))
                        continue
                        
                    crop_class = CROP_FACTORY.get(ctype)
                    if crop_class:
                        new_crop = crop_class()
                        new_crop.current_growth = cell_data.get("growth", 0)
                        
                        # Load extras
                        if hasattr(new_crop, "level"):
                             new_crop.level = cell_data.get("level", 1)
                             new_crop.size = new_crop.level # Sync size
                             new_crop.update_stats()
                        if hasattr(new_crop, "is_rotten"):
                             new_crop.is_rotten = cell_data.get("is_rotten", False)
                             new_crop.update_stats()
                             
                        self.grid[y][x] = new_crop

        # 2. Second pass: Reconnect OccupiedSlots
        # Actually, OccupiedSlot logic is deterministic based on parent N*N.
        # But serialization saves them as "occupied".
        # We need to link them.
        # Simplification: Only load "Mega Pumpkins" properly.
        # If we load a Mega Pumpkin at (x,y) with Size N, we should auto-fill slots?
        # Yes, safer than relying on saved slot data which might be incomplete.
        
        for y in range(self.height):
            for x in range(self.width):
                c = self.grid[y][x]
                if isinstance(c, Pumpkin) and c.size > 1:
                    # Reform slots
                    for dy in range(c.size):
                        for dx in range(c.size):
                            if dx == 0 and dy == 0: continue
                            if 0 <= y+dy < self.height and 0 <= x+dx < self.width:
                                self.grid[y+dy][x+dx] = OccupiedSlot(c, x, y)

    def has_any_crop(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is not None:
                    return True
        return False
