# FULL SCREEN AUTO CARROT
# Features: Infinite Loop, Smart Pathing, Full Coverage (22x12)

# Grid Configuration (Matches Widescreen)
WIDTH = 22
HEIGHT = 12

print("=== FULL AUTOMATION SYSTEM ONLINE ===")
print(f"Target: {WIDTH}x{HEIGHT} Grid ({WIDTH*HEIGHT} Plots)")

def return_to_start():
    """Smart Return to (0,0) using sensors"""
    print(">> Re-calibrating Position...")
    # X Axis
    while drone.x > 0:
        drone.move("West")
    # Y Axis
    while drone.y > 0:
        drone.move("North")
    print(f"   Position Confirmed: ({drone.x}, {drone.y})")

def scan_grid_snake(action_func):
    """Traverse grid in efficient Snake/Zig-Zag pattern"""
    for y in range(HEIGHT):
        # Determine direction for this row
        # Even rows (0, 2...): East (Left -> Right)
        # Odd rows (1, 3...): West (Right -> Left)
        check_range = range(WIDTH)
        direction = "East"
        
        if y % 2 == 1: # Odd Row
            direction = "West"
        
        # Execute Action on whole row
        for i in range(WIDTH):
            action_func()
            
            # Move to next cell if not at end of row
            if i < WIDTH - 1:
                drone.move(direction)
        
        # End of Row: Move South if not at bottom
        if y < HEIGHT - 1:
            drone.move("South")

# === MAIN INFINITE LOOP ===
cycle = 1
return_to_start() # Initial Calibration

while True:
    print(f"\n[CYCLE {cycle}] INITIATED")
    
    # 1. PLANTING
    print(">> Phase 1: PLANTING (Snake Pattern)")
    scan_grid_snake(lambda: drone.plant("carrot"))
    
    # We are now at bottom-left or bottom-right depending on H.
    # Return to start early? Or wait there?
    # Better to return now so we are ready to harvest from top.
    return_to_start()
    
    # 2. GROWTH WAIT
    print(">> Phase 2: PHOTOSYNTHESIS (3.5s)")
    import time
    time.sleep(3.5)
    
    # 3. HARVESTING
    print(">> Phase 3: HARVESTING")
    scan_grid_snake(lambda: drone.harvest())
    return_to_start()
    
    print(f"[CYCLE {cycle}] COMPLETE")
    print(f"Total Inventory: {drone.inventory}")
    cycle += 1
