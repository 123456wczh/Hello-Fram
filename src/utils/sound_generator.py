import wave
import math
import struct
import random
import os

class SoundGenerator:
    """
    Synthesizes game sound effects (retro/8-bit style) and saves to .wav.
    """
    SAMPLE_RATE = 44100
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "sfx")

    @staticmethod
    def _save_wav(filename, samples):
        if not os.path.exists(SoundGenerator.OUTPUT_DIR):
            os.makedirs(SoundGenerator.OUTPUT_DIR)
        
        path = os.path.join(SoundGenerator.OUTPUT_DIR, filename)
        with wave.open(path, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(SoundGenerator.SAMPLE_RATE)
            
            # Convert float -1.0..1.0 to int16
            data = b""
            for s in samples:
                val = int(max(min(s, 1.0), -1.0) * 32767)
                data += struct.pack('<h', val)
            
            wav_file.writeframes(data)
        return path

    @staticmethod
    def generate_pop(freq=600, decay=15):
        """
        Minecraft-like 'Pop' / 'Plop' sound.
        Quick frequency sweep down + exponential decay.
        """
        duration = 0.05
        samples = []
        num_samples = int(duration * SoundGenerator.SAMPLE_RATE)
        
        for i in range(num_samples):
            t = float(i) / SoundGenerator.SAMPLE_RATE
            
            # Pitch drops quickly
            current_freq = freq * (1.0 - (t / duration) * 0.5) 
            
            # Sine wave
            val = math.sin(2 * math.pi * current_freq * t)
            
            # Envelope (Fast attack, exp decay)
            volume = math.exp(-decay * t)
            
            samples.append(val * volume)
            
        return samples

    @staticmethod
    def generate_ding():
        """
        High pitched 'Ding' for success/harvest (Coin style).
        Two tones overlaid.
        """
        duration = 0.3
        num_samples = int(duration * SoundGenerator.SAMPLE_RATE)
        samples = []
        
        freq1 = 1200
        freq2 = 1800
        
        for i in range(num_samples):
            t = float(i) / SoundGenerator.SAMPLE_RATE
            
            v1 = math.sin(2 * math.pi * freq1 * t)
            v2 = math.sin(2 * math.pi * freq2 * t)
            
            # Decay
            env = math.exp(-8 * t)
            
            val = (v1 + v2) * 0.5 * env
            samples.append(val)
            
        return samples

    @staticmethod
    def generate_motor_hum():
        """
        Subtle drone motor hum (Low freq saw/square ish).
        """
        duration = 0.2 # Loop this? Or just play it once per move?
        num_samples = int(duration * SoundGenerator.SAMPLE_RATE)
        samples = []
        freq = 150
        
        for i in range(num_samples):
            t = float(i) / SoundGenerator.SAMPLE_RATE
            
            # Simple waveform variation
            val = math.sin(2 * math.pi * freq * t) * 0.5
            val += math.sin(2 * math.pi * (freq * 2.01) * t) * 0.2 # Disharmony for motor feel
            
            # Smooth fade in/out to avoid clicking
            env = 1.0
            if t < 0.05: env = t / 0.05
            if t > 0.15: env = (0.2 - t) / 0.05
            
            samples.append(val * env * 0.3) # Low volume
        
        return samples

    @staticmethod
    def generate_blip():
        """
        Short high-tech blip for typing.
        """
        duration = 0.05
        num_samples = int(duration * SoundGenerator.SAMPLE_RATE)
        samples = []
        freq = 800
        
        for i in range(num_samples):
            t = float(i) / SoundGenerator.SAMPLE_RATE
            val = math.sin(2 * math.pi * freq * t) * 0.1 # Low volume
            # Sharp decay
            env = math.exp(-10 * t) if t < 0.02 else 0
            samples.append(val * env)
            
        return samples

    @classmethod
    def generate_all(cls):
        print("Generating Sounds (Procedural Audio)...")
        
        # MC-like 'Pop' usually has pitch variations. We'll generate one 'base' pop.
        # Ideally engines pitch-shift it at runtime.
        pop = cls.generate_pop(600, 20)
        cls._save_wav("pop.wav", pop)
        print("  [OK] pop.wav")

        ding = cls.generate_ding()
        cls._save_wav("ding.wav", ding)
        print("  [OK] ding.wav")

        hum = cls.generate_motor_hum()
        cls._save_wav("motor.wav", hum)
        cls._save_wav("motor.wav", hum)
        print("  [OK] motor.wav")

        blip = cls.generate_blip()
        cls._save_wav("blip.wav", blip)
        print("  [OK] blip.wav")

if __name__ == "__main__":
    SoundGenerator.generate_all()
