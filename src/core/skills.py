class SkillNode:
    def __init__(self, skill_id, name, description, cost, parent_id=None, x=0, y=0):
        self.id = skill_id
        self.name = name
        self.description = description
        self.cost = cost
        self.parent_id = parent_id
        self.unlocked = False
        
        # Helper for UI positioning (relative 0-1 or grid)
        self.x = x
        self.y = y

class SkillManager:
    def __init__(self):
        self.skills = {}
        self._init_skills()

    def _init_skills(self):
        # Basic Tech Tree
        # Root
        self.add_skill("speed_1", "Motor Upgrade I", 
            "Optimizes drone rotors.\n\nEffect: Drone moves 10% faster.\nRequired for advanced operations.", 
            {'carrot': 10}, x=0.5, y=0.8)
        
        # Left Branch (Farming)
        self.add_skill("unlock_pumpkin", "Pumpkin Seeds", 
            "Unlocks genetically modified Pumpkin seeds.\n\nMechanic: Fusion\nPumpkins fuse into giant structures (2x2, 3x3...) for exponential yield.\nWarning: Prone to rotting if left unharvested.", 
            {'carrot': 50}, parent_id="speed_1", x=0.3, y=0.6)
            
        self.add_skill("unlock_sunflower", "Sunflower Seeds", 
            "Unlocks Sunflower seeds.\n\nMechanic: Phytoremediation\nSunflowers consume pollution. Requires optimized sorting algorithms.", 
            {'pumpkin': 20, 'carrot': 50}, parent_id="unlock_pumpkin", x=0.2, y=0.4)
        
        # Right Branch (Efficiency)
        self.add_skill("speed_2", "Motor Upgrade II", 
            "Advanced aerodynamics package.\n\nEffect: Drone moves 20% faster.\nEssential for large-scale logistics.", 
            {'pumpkin': 10}, parent_id="speed_1", x=0.7, y=0.6)
            
        self.add_skill("auto_charge", "Solar Panel", 
            "Photovoltaic coating.\n\nEffect: Drone recharges energy while idle.\n(Currently Passive)", 
            {'sunflower': 10}, parent_id="speed_2", x=0.8, y=0.4)

    def add_skill(self, sid, name, desc, cost, parent_id=None, x=0, y=0):
        self.skills[sid] = SkillNode(sid, name, desc, cost, parent_id, x, y)

    def can_unlock(self, skill_id, inventory):
        if skill_id not in self.skills: return False
        skill = self.skills[skill_id]
        
        if skill.unlocked: return False
        
        # Check inventory costs
        for item, amount in skill.cost.items():
            if inventory.get(item, 0) < amount:
                return False
        
        if skill.parent_id:
            parent = self.skills.get(skill.parent_id)
            if not parent or not parent.unlocked:
                return False
                
        return True

    def unlock(self, skill_id, inventory):
        if self.can_unlock(skill_id, inventory):
            # Consume items
            for item, amount in self.skill_manager.skills[skill_id].cost.items(): 
                # Note: skill object is local, but self.skills contains actual reference
                # Wait, simply:
                inventory[item] -= amount
                
            self.skills[skill_id].unlocked = True
            return True
        return False

    def get_skill(self, skill_id):
        return self.skills.get(skill_id)
