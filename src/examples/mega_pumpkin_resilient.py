# MEGA PUMPKIN FACTORY (10x10)
# FEATURES: Infinite Loop, Smart 'Search & Clean' Logic

# Target Config
SIZE = 10         # 10x10 Mega Pumpkin
GROWTH_WAIT = 8.0 # Maturity time
FUSION_WAIT = 2.0 # Extra time for fusion

print(f"=== MEGA PUMPKIN SYSTEM ({SIZE}x{SIZE}) ===")

def return_to_start():
    """Returns to (0,0)"""
    if drone.x > 0 or drone.y > 0:
        while drone.x > 0: drone.move("West")
        while drone.y > 0: drone.move("North")

def scan_and_fix():
    """
    Search grid for issues (Rot/Empty/Unfused) and fix them.
    Logic:
    - Try harvest.
    - If success (Healthy Small Pumpkin): Replant immediately (Refresh).
    - If fail (Rot/Empty): Destroy & Replany (Clean).
    """
    print(">> Scanning & Fixing Grid...")
    replanted = 0
    
    for y in range(SIZE):
        direction = "East"
        if y % 2 == 1: direction = "West"
        
        for x in range(SIZE):
            # Check cell status via harvest interaction
            if drone.harvest():
                # Was healthy small pumpkin -> Replant
                drone.plant("pumpkin")
            else:
                # Was Empty or Rotten -> Fix
                drone.destroy()
                drone.plant("pumpkin")
                replanted += 1
            
            if x < SIZE - 1: drone.move(direction)
        
        if y < SIZE - 1: drone.move("South")
        
    print(f"   Scan Complete. Fixed {replanted} bad cells.")

def attempt_mega_harvest():
    """Try to harvest the Mega Pumpkin"""
    print(">> Attempting Mega Harvest...")
    # Just try harvesting current spot (should be in grid).
    # If 10x10 fused, any point works.
    inventory_before = drone.inventory.get("Pumpkin", 0)
    
    if drone.harvest():
        inventory_after = drone.inventory.get("Pumpkin", 0)
        diff = inventory_after - inventory_before
        
        if diff > 10: # Arbitrary threshold for "Big Harvest"
            print(f"*** MEGA HARVEST SUCCESS! (+{diff}) ***")
            return True
        else:
            print(f"   Harvested small pumpkin (+{diff}). Fusion didn't happen.")
            return False
    return False

# === INFINITE LOOP ===
cycle = 1
return_to_start()

while True:
    print(f"\n<<< CYCLE {cycle} >>>")
    
    # 1. MAINTENANCE (Search & Fix)
    scan_and_fix() # Ensures 100% fresh seeds
    return_to_start()
    
    # 2. WAIT
    print(f">> Maturation ({GROWTH_WAIT}s)...")
    import time
    time.sleep(GROWTH_WAIT)
    
    print(f">> Fusion Alignment ({FUSION_WAIT}s)...")
    time.sleep(FUSION_WAIT)
    
    # 3. HARVEST
    if attempt_mega_harvest():
        print("   Production Goal Met.")
    else:
        print("   Retrying next cycle...")
    
    return_to_start()
    cycle += 1
