# config/audio.py

from pathlib import Path

import pygame


class Audio:

    def __init__(self):

        # ===============================
        # INIT MIXER
        # ===============================

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        pygame.mixer.set_num_channels(8)

        # ===============================
        # CHEMIN PROPRE (SANS config/)
        # ===============================

        self.base_path = Path(__file__).resolve().parent.parent / "assets" / "audio"

        print("🔊 Audio path:", self.base_path)

        self.sounds = {}

        sound_files = {
            "start": "pacman_beginning.wav",
            "chomp": "pacman_chomp.wav",
            "death": "pacman_death.wav",
            "eatfruit": "pacman_eatfruit.wav",
            "eatghost": "pacman_eatghost.wav",
            "extralife": "pacman_extrapac.wav",
            "intermission": "pacman_intermission.wav",
        }

        # ===============================
        # LOAD
        # ===============================

        for name, filename in sound_files.items():
            self.sounds[name] = self.load_sound(filename)

        self.volume = 0.5
        self.set_volume(self.volume)

        self.last_chomp_time = 0

    # ----------------------------------
    # LOAD SAFE
    # ----------------------------------

    def load_sound(self, filename):

        path = self.base_path / filename

        if not path.exists():
            print("❌ Missing sound:", path)
            return None

        try:
            return pygame.mixer.Sound(str(path))

        except pygame.error as e:
            print("❌ Sound load error:", filename, e)
            return None

    # ----------------------------------
    # PLAY
    # ----------------------------------

    def play(self, name):

        sound = self.sounds.get(name)

        if sound:
            sound.play()

    # ----------------------------------
    # CHOMP (anti spam)
    # ----------------------------------

    def play_chomp(self):

        now = pygame.time.get_ticks()

        if now - self.last_chomp_time > 120:

            sound = self.sounds.get("chomp")

            if sound:
                sound.play()

            self.last_chomp_time = now

    # ----------------------------------
    # SHORTCUTS
    # ----------------------------------

    def play_start(self): self.play("start")
    def play_death(self): self.play("death")
    def play_eatfruit(self): self.play("eatfruit")
    def play_eatghost(self): self.play("eatghost")
    def play_extralife(self): self.play("extralife")
    def play_intermission(self): self.play("intermission")

    # ----------------------------------
    # MUSIC
    # ----------------------------------

    def play_music(self, filename, loop=True):

        path = self.base_path / filename

        if not path.exists():
            print("❌ Music missing:", path)
            return

        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play(-1 if loop else 0)

    def stop_music(self):
        pygame.mixer.music.stop()

    # ----------------------------------
    # VOLUME
    # ----------------------------------

    def set_volume(self, volume):

        self.volume = max(0, min(volume, 1))

        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)

        pygame.mixer.music.set_volume(self.volume)