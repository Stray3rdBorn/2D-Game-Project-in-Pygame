import pygame

TEXT_COLOR = (235, 235, 240)
GREY_TEXT = (130, 130, 145)
BUTTON_COLOR = (60, 70, 110)
BUTTON_HOVER = (85, 100, 160)
BUTTON_OFF = (45, 45, 55)
BOX_COLOR = (30, 30, 42)
BORDER_COLOR = (90, 90, 110)
BORDER_FOCUS = (255, 230, 90)


class Label:
    def __init__(self, text, font, color, center):
        self.text = text
        self.font = font
        self.color = color
        self.center = center

    def draw(self, surface):
        image = self.font.render(self.text, True, self.color)
        surface.blit(image, image.get_rect(center=self.center))


class Button:
    def __init__(self, rect, text, font, on_click, color, hover_color):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.on_click = on_click
        self.enabled = True
        self.color = color
        self.hover_color = hover_color

    def handle_event(self, event):
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.on_click()

    def draw(self, surface):
        if not self.enabled:
            color = BUTTON_OFF
        elif self.rect.collidepoint(pygame.mouse.get_pos()):
            color = self.hover_color
        else:
            color = self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        image = self.font.render(self.text, True, TEXT_COLOR if self.enabled else GREY_TEXT)
        surface.blit(image, image.get_rect(center=self.rect.center))


class TextInput:
    def __init__(self, rect, font, max_length=30, hidden=False, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.max_length = max_length
        self.hidden = hidden
        self.placeholder = placeholder
        self.text = ""
        self.focused = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode and event.unicode.isprintable() and len(self.text) < self.max_length:
                self.text += event.unicode

    def clear(self):
        self.text = ""

    def shown_text(self):
        return "*" * len(self.text) if self.hidden else self.text

    def draw(self, surface):
        pygame.draw.rect(surface, BOX_COLOR, self.rect, border_radius=4)
        border = BORDER_FOCUS if self.focused else BORDER_COLOR
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=4)
        if self.text or self.focused:
            shown = self.shown_text()
            if self.focused and pygame.time.get_ticks() // 500 % 2 == 0:
                shown += "|"
            image = self.font.render(shown, True, TEXT_COLOR)
        else:
            image = self.font.render(self.placeholder, True, GREY_TEXT)
        surface.blit(image, image.get_rect(midleft=(self.rect.left + 10, self.rect.centery)))

class MuteButton:
    def __init__(self, audio, rect):
        self.audio = audio
        self.rect = pygame.Rect(rect)

    def handle_event(self, event):
        # returns True when the click was on the button, so the screen under it does not get that click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.audio.toggle_mute()
            return True
        return False

    def draw(self, surface):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, BUTTON_HOVER if hover else BUTTON_COLOR, self.rect, border_radius=6)
        x, y = self.rect.center
        # the speaker is a small box with a cone next to it
        pygame.draw.rect(surface, TEXT_COLOR, (x - 12, y - 4, 6, 8))
        pygame.draw.polygon(surface, TEXT_COLOR, [(x - 6, y - 4), (x + 2, y - 10), (x + 2, y + 10), (x - 6, y + 4)])
        if self.audio.muted:
            # a red cross means muted
            pygame.draw.line(surface, (235, 80, 80), (x + 6, y - 6), (x + 16, y + 6), 3)
            pygame.draw.line(surface, (235, 80, 80), (x + 16, y - 6), (x + 6, y + 6), 3)
        else:
            # two arcs mean the sound is on
            pygame.draw.arc(surface, TEXT_COLOR, (x - 2, y - 8, 12, 16), -1.0, 1.0, 2)
            pygame.draw.arc(surface, TEXT_COLOR, (x + 2, y - 13, 18, 26), -1.0, 1.0, 2)