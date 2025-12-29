import pygame
import random
import math
import os

# --- Tweening Logic ---

def ease_linear(t):
    return t

def ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)

def ease_out_back(t):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * math.pow(t - 1, 3) + c1 * math.pow(t - 1, 2)

class Tween:
    """
    Interpolates an attribute of an object over time.
    """
    def __init__(self, target_obj, attr_name, end_value, duration, easing=ease_out_quad):
        self.target = target_obj
        self.attr = attr_name
        
        # Check if attribute exists, if not, maybe it's a dict key or custom setter?
        # For simplicity, assume attribute access.
        if hasattr(target_obj, attr_name):
            self.start_value = getattr(target_obj, attr_name)
        else:
            self.start_value = 0 # Default fallback
            
        self.end_value = end_value
        self.duration = duration
        self.easing = easing
        self.timer = 0.0
        self.finished = False

    def update(self, dt):
        if self.finished: return
        
        self.timer += dt
        t = min(1.0, self.timer / self.duration)
        progress = self.easing(t)
        
        current = self.start_value + (self.end_value - self.start_value) * progress
        setattr(self.target, self.attr, current)
        
        if self.timer >= self.duration:
            self.finished = True
            setattr(self.target, self.attr, self.end_value) 

# --- Particle System ---

class Particle:
    def __init__(self, x, y, image, life=1.0, vel=(0,0), fade=True, scale_fade=False):
        self.x = x
        self.y = y
        self.image = image
        self.life = life
        self.max_life = life
        self.vel_x, self.vel_y = vel
        self.fade = fade
        self.scale_fade = scale_fade
        self.alive = True
        self.rot = random.uniform(0, 360)
        self.rot_vel = random.uniform(-90, 90)

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return

        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.rot += self.rot_vel * dt
        
    def draw(self, surface):
        if not self.alive or not self.image: return
        
        # Calculate Alpha
        alpha = 255
        ratio = self.life / self.max_life
        if self.fade:
            alpha = int(255 * ratio)
        
        # Copy for transform
        img = self.image.copy()
        
        # Scale Fade (Shrink as it dies)
        if self.scale_fade:
            scale = ratio
            w = int(img.get_width() * scale)
            h = int(img.get_height() * scale)
            if w <= 0 or h <= 0: return
            img = pygame.transform.scale(img, (w, h))

        # Alpha
        img.set_alpha(alpha)
        
        # Rotation (Optional, maybe expensive for thousands of particles)
        # img = pygame.transform.rotate(img, self.rot)

        # Draw centered
        rect = img.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(img, rect)

# --- Visual Manager (Singleton) ---

class VisualManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VisualManager, cls).__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        self.particles = []
        self.tweens = []
        self.assets = {}
        self.sounds = {}
        self.font = None
        self.load_assets()
        self.load_sounds()

    def load_assets(self):
        # Locate assets in root/assets
        # Assumption: __file__ is src/ui/visuals.py -> root/src/ui/visuals.py
        # root is ../../
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        asset_dir = os.path.join(root_dir, "assets")
        
        if not os.path.exists(asset_dir):
            print(f"[Visuals] Asset dir not found: {asset_dir}")
            return

        try:
            for filename in os.listdir(asset_dir):
                if filename.endswith(".png"):
                    name = filename.replace(".png", "")
                    path = os.path.join(asset_dir, filename)
                    self.assets[name] = pygame.image.load(path).convert_alpha()
            print(f"[Visuals] Loaded {len(self.assets)} assets.")
        except Exception as e:
            print(f"[Visuals] Error loading assets: {e}")

    def load_sounds(self):
        # Locate sounds in root/assets/sfx
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        sfx_dir = os.path.join(root_dir, "assets", "sfx")
        
        if not os.path.exists(sfx_dir): return

        try:
            pygame.mixer.init()
            for filename in os.listdir(sfx_dir):
                if filename.endswith(".wav"):
                    name = filename.replace(".wav", "")
                    path = os.path.join(sfx_dir, filename)
                    self.sounds[name] = pygame.mixer.Sound(path)
            print(f"[Visuals] Loaded {len(self.sounds)} sounds.")
        except Exception as e:
            print(f"[Visuals] Error loading sounds: {e}")

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def get_animated_asset(self, base_name, timer, speed=10):
        """
        Return the correct frame for an animated asset.
        Example: base_name="drone_idle", frames are "drone_idle_0", "drone_idle_1"...
        """
        # Count frames
        # This is a bit inefficient to do every frame, but fine for prototype.
        # Ideally, cache the frame count.
        frame_idx = int(timer * speed) % 4 # Assume 4 frames for now
        full_name = f"{base_name}_{frame_idx}"
        return self.get_asset(full_name)
            
        if pygame.font.get_init():
             self.font = pygame.font.SysFont("Consolas", 16, bold=True)

    def get_asset(self, name):
        """Safe retrieval of assets with fallback."""
        if name in self.assets:
            return self.assets[name]
        # Return a magenta placeholder if not found
        s = pygame.Surface((32, 32))
        s.fill((255, 0, 255))
        return s

    # --- Spawning Methods ---

    def spawn_dust(self, x, y):
        img = self.assets.get("particle_dust")
        if not img: return
        
        for _ in range(4):
             vx = random.uniform(-30, 30)
             vy = random.uniform(-30, 30)
             p = Particle(x, y, img, life=0.4 + random.random()*0.3, vel=(vx, vy), scale_fade=True)
             self.particles.append(p)

    def spawn_spark(self, x, y):
        img = self.assets.get("particle_spark")
        if not img: return
        
        for _ in range(8):
             vx = random.uniform(-80, 80)
             vy = random.uniform(-100, 50) # Mostly pop up
             p = Particle(x, y, img, life=0.6, vel=(vx, vy), fade=True)
             self.particles.append(p)
             
    def spawn_poof(self, x, y, color=(200, 200, 200)):
        # Circle poof effect using basic shapes if asset missing
        # For now assume dust asset
        self.spawn_dust(x, y)

    def spawn_floating_text(self, x, y, text, color=(255, 215, 0)):
        if not self.font: 
             if pygame.font.get_init():
                 self.font = pygame.font.SysFont("Consolas", 16, bold=True)
             else: return

        # Render text to surface
        txt_surf = self.font.render(str(text), True, color)
        # Create a particle that floats up
        p = Particle(x, y, txt_surf, life=1.5, vel=(0, -40), fade=True)
        self.particles.append(p)


    # --- Core Loop ---

    def add_tween(self, tween):
        self.tweens.append(tween)

    def update(self, dt):
        # Particles
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]
        
        # Tweens
        for t in self.tweens:
            t.update(dt)
        self.tweens = [t for t in self.tweens if not t.finished]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

# Global accessor
def get_visual_manager():
    return VisualManager()
