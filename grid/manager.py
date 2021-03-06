import math
from typing import Union, List

import easygui
import pygame

from core import Vector2D, Switch
from widgets import Text
from .algorithm import AStarAlgorithm
from .memory import AppDatabase, key_map
from .tile import Tile


class GridManager:
    def __init__(self, size: Vector2D, info_text: Text, position=Vector2D(0, 20), padding=Vector2D(0, 0)):

        self.size = size
        self.position = position
        self.padding = padding

        self.info_text = info_text
        self.info_text.text = 'Select start'

        self.tilepadding = Vector2D(0, 0)
        screen_size = Vector2D.tuple(pygame.display.get_surface().get_rect().size)
        space = Vector2D(
            screen_size.x - position.x - padding.x,
            screen_size.y - position.y - padding.y
        )

        self.tilesize = Vector2D(
            int((space.x - (self.size.x * self.tilepadding.x)) / self.size.x),
            int((space.y - (self.size.y * self.tilepadding.y)) / self.size.y),
        )

        self.grid = []
        for x in range(size.x):
            l = [0] * size.y
            self.grid.append(l)

        self.tiles = []
        for x in range(size.x):
            l = [None] * size.y
            self.tiles.append(l)

        self.remake_tiles(self.grid)

        self.drawable = Switch(True)

        self.mouse_left_down = Switch(False)
        self.mouse_left_down_type = None

        self.start = None
        self.end = None

        self.algorithm = None

        def onflip(val):
            if self.algorithm.solution_length == -1:
                self.info_text.text = 'No solution found'
                return

            self.info_text.text = 'Running' if val else f'Found solution of length {self.algorithm.solution_length}'

        self.running = Switch(False, onflip=onflip)

        self.misc = {}

    def remake_tiles(self, grid):
        """
        recreates the whole tile grid for :param grid:

        :param grid: blueprint for recreation
        :return: None
        """
        size = Vector2D(len(grid), len(grid[0]))

        for x in range(size.x):
            for y in range(size.y):
                position = Vector2D(
                    y * self.tilesize.x + y * self.tilepadding.x + self.position.x + self.padding.x,
                    x * self.tilesize.y + x * self.tilepadding.y + self.position.y + self.padding.y,
                )

                tile = Tile(Tile.int_to_state(self.grid[x][y]), gridpos=Vector2D(x, y), position=position,
                            padding=Vector2D.zero())

                tile.size = self.tilesize

                self.tiles[x][y] = tile

    def update_tiles(self, positions):
        """
        updates the tile states in :param positions: to match that of self.grid

        :param positions: positions to update
        :return: None
        """
        for gridposition in positions:
            x, y = gridposition

            tile = self.tiles[x][y]
            tile.state = Tile.int_to_state(self.grid[x][y])

            # tile.text.text = f'{self.algorithm.costgrid[x][y]:.1f}'
            # tile.text.text = str(self.algorithm.gcost[(x, y)])
            # tile.text.text = f'{self.algorithm.gcost[(x, y)]}+{self.algorithm.h(Vector2D(x, y))}'

            self.tiles[x][y] = tile

    def clean_grid(self, types, to=Tile.UNVISITED):
        """
        replaces all the state types in :param types: with state :param to:

        :param types: state types to replace
        :param to: replacement state
        """

        if Tile.END in types:
            self.end = None
            self.info_text.text = 'Select end'

        if Tile.START in types:
            self.start = None
            self.info_text.text = 'Select start'

        to = Tile.state_to_int(to)

        size = Vector2D(len(self.grid), len(self.grid[0]))
        for x in range(size.x):
            for y in range(size.y):
                tile = self.grid[x][y]

                if Tile.int_to_state(tile) in types:
                    self.grid[x][y] = to

    def update_grid(self):
        """
        updates :var self.grid: to match the current :var self.tiles:
        """
        for tile in self.iter_tiles():
            x, y = tile.gridpos
            self.grid[x][y] = Tile.state_to_int(tile.state)

    def event(self, event):
        """
        event handling

        :param event: event to handle
        """
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                if not self.drawable.get():
                    easygui.msgbox('Press either Left Ctrl or Left Shift to clear the current grid'
                                   '\nLeft Ctrl: Everything excluding walls'
                                   '\nLeft Shift: Everything including walls', 'Clear grid', ok_button='CLOSE')
                    return

                self.update_grid()

                if self.start is None or self.end is None:
                    easygui.msgbox('Starting point or End point not specified', 'Missing inputs', 'CLOSE')
                    return

                # lock input and start the a* algorithm
                self.drawable.set(False)

                self.algorithm = AStarAlgorithm(self.grid)
                self.running.set(True)

            elif event.key == pygame.K_LSHIFT:
                if self.running.get():
                    return

                self.update_grid()
                self.clean_grid([Tile.VISITED, Tile.START, Tile.END, Tile.PATH, Tile.NEIGHBOURS, Tile.WALL])
                self.remake_tiles(self.grid)
                self.drawable.set(True)

            elif event.key == pygame.K_LCTRL:
                if self.running.get():
                    return

                self.update_grid()
                self.clean_grid([Tile.VISITED, Tile.START, Tile.END, Tile.PATH, Tile.NEIGHBOURS])
                self.remake_tiles(self.grid)
                self.drawable.set(True)

            elif event.key == pygame.K_s:
                if self.running.get():
                    return

                slot = easygui.buttonbox('Pick a slot to load', 'Load', list(key_map.values()))
                if slot is None:
                    return

                self.update_grid()
                self.save(slot)

            elif event.key == pygame.K_l:
                if self.running.get():
                    return

                slot = easygui.buttonbox('Pick a slot to load', 'Load', list(AppDatabase.database().data.keys()))
                if slot is None:
                    return

                self.load(slot)

        if event.type == pygame.MOUSEBUTTONDOWN:

            # left
            if event.button == 1:
                self.mouse_left_down.set(True)

                if self.drawable.get():

                    tile = self.tile(event.pos)
                    if tile is None:
                        return

                    # applying
                    currentstate = tile.state
                    if currentstate == Tile.WALL:
                        self.mouse_left_down_type = Tile.UNVISITED
                    elif currentstate == Tile.UNVISITED:
                        self.mouse_left_down_type = Tile.WALL

                    if self.mouse_left_down_type is not None:
                        tile.state = self.mouse_left_down_type

            # right
            elif event.button == 3:
                if self.drawable.get():
                    tile = self.tile(event.pos)

                    if self.start is None:
                        self.start = tile
                        tile.state = Tile.START

                        self.info_text.text = 'Select end'
                    elif tile.state != Tile.START:
                        self.end = tile
                        tile.state = Tile.END
                        self.info_text.text = 'Ready'

        if event.type == pygame.MOUSEBUTTONUP:
            # left
            if event.button == 1:
                self.mouse_left_down.set(False)
                self.mouse_left_down_type = None

        if event.type == pygame.MOUSEMOTION:
            # left mouse button down
            if self.mouse_left_down.get():
                if self.drawable.get():

                    tile = self.tile(event.pos)
                    if tile is None:
                        return

                    # apply if state does not equal to target
                    if self.mouse_left_down_type is not None:

                        # dont replace [start] and [end] node
                        if tile.state in [Tile.START, Tile.END]:
                            return

                        tile.state = self.mouse_left_down_type

    def update(self):
        if self.running.get():
            try:
                affected = self.algorithm.next()
                self.update_tiles(affected)
            except StopIteration:
                self.running.set(False)

            # not further actions allowed
            # when algorithms is running
            return
        else:
            # get current mouse position
            mouse_pos = Vector2D.tuple(pygame.mouse.get_pos())

            # get tile in mouse position position
            tile = self.tile(mouse_pos)
            if tile is None:
                return

            # update tile to indicate hover
            if not tile.hover:
                tile.enter()

            # revert previous hover previous hover tile
            try:
                inbound = self.misc['over']
                if tile.position != inbound.position:
                    inbound.exit()
            except KeyError:
                pass

            self.misc['over'] = tile

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LALT]:
            for key in key_map.keys():
                # save
                if keys[key]:
                    value = key_map[key]
                    self.update_grid()
                    self.save(value)
                    break
        else:
            for key in key_map.keys():
                # load
                if keys[key]:
                    value = key_map[key]
                    self.load(value)
                    break

    def draw(self, surface):
        """
        draws all the tiles on to :param surface:

        :param surface: surface to draw the grid on
        """
        surface.blits([self.tiles[x][y].blit_sequence for x in range(self.size.x) for y in range(self.size.y)])

    def tile(self, coord) -> Union[Tile, None]:
        """
        :returns: tile depending on value

        in case of tuple :return: tile in pixel positon (x, y)
        """

        # finding tile
        position = Vector2D.tuple(coord)

        x = (position.y - self.position.y - self.padding.y) / (self.tilesize.y + self.tilepadding.y)
        y = (position.x - self.position.x - self.padding.x) / (self.tilesize.x + self.tilepadding.x)

        ix = math.floor(x)
        iy = math.floor(y)

        # out of bounds
        if ix < 0 or ix >= self.size.x or iy < 0 or iy >= self.size.y:
            return

        return self.tiles[ix][iy]

    def iter_tiles(self) -> List[Tile]:
        """
        :return: generator, returns all the tiles of this grid
        """
        for x in range(len(self.tiles)):
            for y in range(len(self.tiles[0])):
                yield self.tiles[x][y]

    def save(self, slot):
        """
        :return: saves grid to :param slot:
        """

        copy = []
        for row in self.grid:
            copy.append(row[:])

        AppDatabase.database().save_grid(slot, copy, self.drawable.get())

        easygui.msgbox(f'Successfully saved the grid to slot {slot}', 'Success', 'CLOSE')

    def load(self, slot):
        """
        :return: loads grid saved at :param slot:
        """
        try:
            grid, drawable = AppDatabase.database().load_grid(slot)
        except TypeError:
            easygui.msgbox('Unable to load', 'Missing data', 'CLOSE')
            return

        sizex, sizey = len(grid), len(grid[0])
        if sizex != self.size.x or sizey != self.size.y:
            action = easygui.buttonbox(f'Expected {self.size}, however got {sizex, sizey}', 'Grid size mismatch', ['DELETE', 'CLOSE'])
            if action == 'DELETE':
                AppDatabase.database().delete(slot)
                AppDatabase.database().save()
            return

        # copy to avoid overwriting on database
        self.grid = [row[:] for row in grid]

        # recreate whole grid
        self.remake_tiles(self.grid)

        self.drawable.set(drawable)

        # easygui.msgbox(f'Successfully loaded the grid from slot {slot}', 'Success', 'CLOSE')

    @staticmethod
    def print_grid(grid):
        size = Vector2D(len(grid), len(grid[0]))
        for x in range(size.x):
            print('[', end='')
            for y in range(size.y):
                value = grid[x][y]
                print(value, end='')
                if y != size.y - 1:
                    print(', ', end='')
            print(']')
