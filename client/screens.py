class Screen:
    def __init__(self, manager):
        self.manager = manager

    def on_enter(self, **data):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class ScreenManager:
    def __init__(self, session, network):
        self.session = session
        self.network = network
        self.screens = {}
        self.current = None
        self.last_run = None
        self.pending_run = None

    def add(self, name, screen):
        self.screens[name] = screen

    def switch(self, name, **data):
        self.current = self.screens[name]
        self.current.on_enter(**data)

    def handle_event(self, event):
        self.current.handle_event(event)

    def update(self, dt):
        self.network.poll()
        self.current.update(dt)

    def draw(self, surface):
        self.current.draw(surface)