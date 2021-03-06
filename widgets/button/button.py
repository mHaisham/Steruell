import pygame

from core import Vector2D, Color, colors
from .hover import DIM_LIGHT, ORIGINAL_COLOR
from ..text import Text
from ..widget import Widget, Hover


class Button(Widget):
    """
    Simple button


    """

    def __init__(self, text: Text, padding: Vector2D = Vector2D(20, 10), position: Vector2D = Vector2D.zero(),
                 color: Color = None,
                 onclick=None):
        super(Button, self).__init__()

        # look
        self.text = text
        self._position = position

        self.padding = padding
        self._size = Vector2D(
            self.text.rect.size[0] + self.padding.x,
            self.text.rect.size[1] + self.padding.y
        )

        self.text.center(Vector2D.center(self.position, self.size))

        # color
        if color is None:
            color = colors.TRANSPARENT
        self._mutable_color = color
        self._original_color = color

        # behaviour
        self.onhover = Hover(DIM_LIGHT, ORIGINAL_COLOR)
        self.onclick = onclick

        if self.onclick is None:
            self.onclick = lambda button: None

        # used to draw
        self.surface = self.make()

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size
        self.surface = self.make()

    @property
    def original_color(self):
        return self._original_color

    @property
    def color(self):
        return self._mutable_color

    @color.setter
    def color(self, other):
        self._original_color = other
        self.mutate_color(other)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.text.center(Vector2D.center(self.position, self.size))

    def mutate_color(self, color):
        self._mutable_color = color
        self.surface.fill(color)

    def apply_hover(self, onhover: Hover):
        self.onhover = Hover(onhover.onenter, onhover.onexit)
        return self

    def draw(self, surface: pygame.SurfaceType):
        surface.blit(self.surface, self.position)

        # only draw if there is something to draw
        if self.text.text:
            self.text.draw(surface)

    def make(self):
        """
        :return: new pygame surface
        """
        surface = pygame.Surface(self.size, pygame.SRCALPHA)
        surface.fill(self.color)

        return surface

    def inbound(self, pos: Vector2D):
        return self.position.x + self.size.x > pos.x > self.position.x and \
               self.position.y + self.size.y > pos.y > self.position.y

    def enter(self):
        super(Button, self).enter()
        self.onhover.enter(self)

    def exit(self):
        super(Button, self).exit()
        self.onhover.exit(self)

    def clicked(self):
        self.onclick(self)
