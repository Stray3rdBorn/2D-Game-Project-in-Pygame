import pygame

from paths import asset_folder

# files in the assets folder, written without the extension
MUSIC = ("menu", "play", "game_over", "victory")
EFFECTS = ("shoot", "kill", "hurt", "wave")
EXTENSIONS = (".ogg", ".mp3", ".wav")    # the first one that exists is used, so any of these formats works

MUSIC_VOLUME = 0.5
# the shoot sound plays all the time, so it is the quietest
EFFECT_VOLUME = {"shoot": 0.05, "kill": 0.3, "hurt": 0.4, "wave": 0.2}


class Audio:
    def __init__(self, folder=None):
        self.folder = folder or asset_folder()
        self.ready = False          # stays False until start() works, until then every method does nothing
        self.muted = False
        self.sounds = {}
        self.current_music = None

    def find(self, kind, name):
        # looks for assets/<kind>/<name> with each extension and returns the first file that exists
        for extension in EXTENSIONS:
            path = self.folder / kind / (name + extension)
            if path.exists():
                return path
        return None

    def start(self):
        # start the mixer here and not on import, so tests and CI never need a sound device
        try:
            pygame.mixer.init()
        except pygame.error:
            return      # no sound device, the game just runs without sound
        pygame.mixer.set_num_channels(16)    # more channels so many effects can overlap
        self.ready = True
        for name in EFFECTS:
            path = self.find("sounds", name)
            if path is None:
                continue    # a missing file only means that one sound stays silent
            try:
                sound = pygame.mixer.Sound(str(path))
            except pygame.error:
                continue    # a broken file is skipped the same way
            sound.set_volume(EFFECT_VOLUME[name])
            self.sounds[name] = sound

    def play(self, name):
        sound = self.sounds.get(name)
        if sound and not self.muted:
            sound.play()

    def play_loop(self, name):
        sound = self.sounds.get(name)
        if sound and not self.muted:
            sound.play(loops=-1)     # -1 repeats until stopped, so any file length works

    def stop(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.fadeout(300)       # fades out in 300 ms so the siren does not cut with a click

    def play_music(self, name):
        if not self.ready:
            return
        # same track is still playing, so leave it alone, this keeps the menu music going between screens
        if name == self.current_music and pygame.mixer.music.get_busy():
            return
        path = self.find("music", name)
        try:
            if path is None:
                raise pygame.error("no file")
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(0 if self.muted else MUSIC_VOLUME)
            pygame.mixer.music.play(-1)      # -1 means loop forever
        except pygame.error:
            pygame.mixer.music.stop()        # the old track must not keep playing on the wrong screen
            self.current_music = None
            return
        self.current_music = name

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
         self.stop("wave")
        if self.ready:
            # the music keeps running at volume 0, so unmuting continues the same track
            pygame.mixer.music.set_volume(0 if self.muted else MUSIC_VOLUME)


# one shared object, every file imports this one
audio = Audio()