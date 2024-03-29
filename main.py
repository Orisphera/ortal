import random
from dataclasses import dataclass
import json
from fractions import Fraction
from functools import lru_cache
from itertools import chain, starmap

import pygame
import sys

# VIEW_DIST is in tiles; other constants here are in pixels
TILE_SIZE = 40
VIEW_DIST = 8
SCREEN_SIZE = TILE_SIZE * (VIEW_DIST * 2 + 1)
MENU_VERT_OFFSET = 80
MENU_HOR_OFFSET = 10
MENU_ITEM_HEIGHT = 20
MENU_ITEMS_SHOWN = 15
MENU_HEIGHT = MENU_ITEM_HEIGHT * MENU_ITEMS_SHOWN
MENU_WIDTH = 100
WIN_HEIGHT = 60
WIN_WIDTH = 300


class VertexSingularityWarning(UserWarning):
    pass


def terminate():
    pygame.quit()
    sys.exit()


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    with open('levels/index.json') as f:
        levels = json.load(f)
    level_select_screen(screen, levels)


def level_select_screen(screen, items):
    """
    Level select screen
    Note: play is called as a part of this function
    :param screen: the screen as Pygame surface
    :param items: JSON object representing the contents of the LSS
    :return: None
    """
    def choose_item():
        """
        Choose the selected item
        :return: True if it should exit level_select_screen
        """
        selected_item1 = items[selection]
        selected_item_type = selected_item1["type"]
        if selected_item_type == "folder":
            level_select_screen(screen, [{
                "name": "..",
                "desc_fn": selected_item1["desc_fn"],
                "type": "back"
            }] + selected_item1["contents"])
        elif selected_item_type == "level":
            play(screen, 'levels/' + selected_item1["fn"])
        elif selected_item_type == "back":
            return True
        else:
            raise ValueError(f"incorrect menu item type: {selected_item_type}")
        return False

    def go_up():
        """ Select the previous item in the list """
        nonlocal selection, offset
        if selection:
            selection -= 1
        offset = min(offset, selection)

    def go_down():
        """ Select the next item in the list """
        nonlocal selection, offset
        selection += 1
        if selection == len(items):
            selection -= 1
        offset = max(offset, selection - MENU_ITEMS_SHOWN)

    title_font = pygame.font.Font(None, 50)
    name_font = pygame.font.Font(None, 20)
    desc_font = pygame.font.Font(None, 30)

    selection = 0  # Selected item index
    offset = 0  # First shown item index
    while True:
        screen.fill(pygame.Color('#772953'))
        title_rendered = title_font.render('Ortal', True, pygame.Color('#FFFFFF'))
        title_rect = title_rendered.get_rect()
        title_rect.top = 15
        title_rect.left = MENU_HOR_OFFSET
        screen.blit(title_rendered, title_rect)
        screen.fill(pygame.Color('#000000'), pygame.Rect(
            MENU_HOR_OFFSET, MENU_VERT_OFFSET, MENU_WIDTH, MENU_HEIGHT
        ))
        screen.fill(pygame.Color('#FF0000'), pygame.Rect(
            MENU_HOR_OFFSET,
            MENU_VERT_OFFSET + (selection - offset) * MENU_ITEM_HEIGHT,
            MENU_WIDTH,
            MENU_ITEM_HEIGHT
        ))
        for menu_item_top, menu_item in zip(range(
                MENU_VERT_OFFSET,
                MENU_VERT_OFFSET + MENU_HEIGHT,
                MENU_ITEM_HEIGHT
        ), items[offset:]):
            name_rendered = name_font.render(menu_item["name"], True,
                                             pygame.Color('#FFFFFF'))
            name_rect = name_rendered.get_rect()
            name_offset = (MENU_ITEM_HEIGHT - name_rect.height) // 2
            name_rect.top = menu_item_top + name_offset
            name_rect.left = MENU_HOR_OFFSET + name_offset
            screen.blit(name_rendered, name_rect)

        selected_item = items[selection]
        with open(f'levels/{selected_item["desc_fn"]}') as f:
            description = f.read().rstrip('\n').split('\n')
        text_coord_x = MENU_HOR_OFFSET + MENU_WIDTH + 10
        text_coord_y = MENU_VERT_OFFSET + 10
        for line in description:
            string_rendered = desc_font.render(line, True, pygame.Color('white'))
            string_rect = string_rendered.get_rect()
            string_rect.top = text_coord_y
            string_rect.x = text_coord_x
            screen.blit(string_rendered, string_rect)
            text_coord_y += string_rect.height + 1
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_w, pygame.K_UP):
                    go_up()
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    go_down()
                elif event.key == pygame.K_RETURN:
                    if choose_item():
                        return
            if event.type in (pygame.MOUSEMOTION,
                              pygame.MOUSEBUTTONDOWN):
                x, y = event.pos
                # Coordinates within the menu
                xwm, ywm = x - MENU_HOR_OFFSET, y - MENU_VERT_OFFSET
                if 0 <= xwm < MENU_WIDTH and 0 <= ywm < MENU_HEIGHT:
                    selection1 = (offset + ywm) // MENU_ITEM_HEIGHT
                    if selection1 < len(items):
                        selection = selection1
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1:
                                if choose_item():
                                    return
                            elif event.button == 4:
                                if offset:
                                    offset -= 1
                            elif event.button == 5:
                                if len(items) > MENU_ITEMS_SHOWN:
                                    offset = min(offset + 1,
                                                 len(items) - MENU_ITEMS_SHOWN)


class Tile:
    see_through = True
    neighbors_n = 4

    def __init__(self, name=''):
        self.name = name
        self.neighbors = []
        """ :type: list[TileRotation] """
        self.new_neighbors = None
        """ :type: Optional[list[TileRotation]] """
        self.is_moving = False

    def __str__(self):
        return self.name

    @staticmethod
    def get_texture(size: int, rot: int = 0) -> pygame.Surface:
        return pygame.Surface((size, size))

    def verify(self, all_set=None):
        if len(self.neighbors) != self.neighbors_n:
            raise ValueError('incorrect number of neighbors')
        for rot in range(self.neighbors_n):
            TileRotation(self, rot).verify(all_set)


class EmptyTile(Tile):
    @staticmethod
    @lru_cache(None)
    def get_texture(size, rot=0):
        ans = Tile.get_texture(size, rot)
        ans.fill(pygame.Color('#101010'))
        return ans


class GlassTile(Tile):
    @staticmethod
    @lru_cache(None)
    def get_texture(size, rot=0):
        ans = Tile.get_texture(size, rot)
        ans.fill(pygame.Color('#181818'))
        pygame.draw.rect(ans, pygame.Color('#FFFFFF'), ans.get_rect(), 2)
        return ans


class WallTile(Tile):
    @staticmethod
    @lru_cache(None)
    def get_texture(size, rot=0):
        ans = pygame.Surface((size, size))
        ans.fill(pygame.Color("#000000"))
        pygame.draw.line(ans, pygame.Color("#772953"), (0, 0), (size, 0))
        y = 0
        offset_rng = random.Random(1)
        for c in range(128, 0, -40):
            for x in range(offset_rng.randint(-10, 0), size, 10):
                pygame.draw.rect(ans, (c, c, c), pygame.Rect(x + 1, y + 1, 7, 3),
                                 0, 1)
            y += 5
        ans = pygame.transform.rotate(ans, 90 * rot)
        # ans.fill(pygame.Color("#772953"))
        return ans

    see_through = False


class PortalTile(Tile):
    see_through = False
    neighbors_n = 8

    @staticmethod
    @lru_cache(None)
    def get_texture(size, rot=0):
        ans = Tile.get_texture(size, rot)
        ans.fill(pygame.Color('#000000'))
        pygame.draw.rect(ans, pygame.Color('#FFFFFF'), ans.get_rect(), 2)
        pygame.draw.circle(ans, pygame.Color('#1010FF'), (size // 2, size // 2),
                           size // 2, 2)
        return ans


class PlayerTile(Tile):
    @staticmethod
    @lru_cache(None)
    def get_texture(size, rot=0):
        ans = Tile.get_texture(size, rot)
        ans.fill(pygame.Color('#772953'))
        pygame.draw.rect(ans, pygame.Color('#FFFFFF'), ans.get_rect(), 2)
        pygame.draw.circle(
            ans, pygame.Color('#000000'), (size // 2, size // 2), 5)
        return ans


class GoalTile(Tile):
    @staticmethod
    @lru_cache(None)
    def get_texture(size, rot=0):
        ans = Tile.get_texture(size, rot)
        ans.fill(pygame.Color('#202020'))
        pygame.draw.rect(ans, pygame.Color('#F0F0F0'), ans.get_rect(), 2)
        pygame.draw.circle(
            ans, pygame.Color('#FFFFFF'), (size // 2, size // 2), 5)
        return ans


@dataclass
class TileRotation:
    tile: Tile
    rotation: int

    def __str__(self):
        return f'{self.tile.name} rotation {self.rotation}'

    def convert_neighbor_i(self, neighbor_i: int):
        return (neighbor_i + self.rotation) % self.tile.neighbors_n

    def get_neighbor(self, neighbor_i: int):
        if self.tile.new_neighbors is not None:
            return self.tile.new_neighbors[self.convert_neighbor_i(neighbor_i)]
        return self.tile.neighbors[self.convert_neighbor_i(neighbor_i)]

    def set_neighbor1w(self, neighbor_i, new_neighbor, changed_list):
        if self.tile.new_neighbors is None:
            self.tile.new_neighbors = self.tile.neighbors[:]
            changed_list.append(self.tile)
        self.tile.new_neighbors[self.convert_neighbor_i(neighbor_i)] = \
            new_neighbor

    def set_neighbor_mutual(self, neighbor_i, new_neighbor, changed_list):
        self.set_neighbor1w(neighbor_i, new_neighbor, changed_list)
        if not isinstance(new_neighbor.tile, WallTile):
            new_neighbor.set_neighbor1w(0, self.rotate(neighbor_i), changed_list)

    def rotate(self, d_rot):
        return TileRotation(self.tile,
                            (self.rotation + d_rot) % self.tile.neighbors_n)

    def verify(self, all_set):
        neighbor = self.get_neighbor(0)
        if not isinstance(neighbor.tile, WallTile):
            if neighbor.get_neighbor(0) != self:
                raise ValueError(f'incorrect connectivity: {self} -> {neighbor}'
                                 f' -> {neighbor.get_neighbor(0)}')
            if not (all_set is None or neighbor.tile in all_set):
                raise ValueError(f'removed tile {neighbor.tile} used from'
                                 f' {self.tile}')
#        return
        neighbor1 = self.get_neighbor(1)
        if not isinstance(neighbor1.tile, WallTile):
            if neighbor1 == self:
                raise VertexSingularityWarning(
                    f'90 degree CS in vertex near {self}')
            neighbor2 = neighbor1.get_neighbor(1)
            if neighbor2 == self:
                raise VertexSingularityWarning(
                    f'180 degree CS in vertex near {self}')
            if not isinstance(neighbor2.tile, WallTile):
                neighbor3 = neighbor2.get_neighbor(1)
                if (not isinstance(neighbor3.tile, WallTile) and
                        neighbor3.get_neighbor(1) != self):
                    raise VertexSingularityWarning(f'CS in vertex near {self}')


def f_input(f):
    return f.readline().rstrip('\n')


def load_level(fn: str):
    with open(fn) as f:
        version_line = f_input(f)
        if version_line == 'ortal neighbors':
            players: list[TileRotation] = []
            wall = TileRotation(WallTile('wall'), 0)
            tiles = dict()
            neighbors_names = dict()
            for line in f.readlines():
                tile_name, tile_type, tile_data = \
                    line.rstrip('\n').split(maxsplit=2)
                if tile_name in tiles.keys():
                    raise ValueError('repeating tile names')
                tiles[tile_name] = {'empty': EmptyTile,
                                    'glass': GlassTile,
                                    'portal': PortalTile,
                                    'player': PlayerTile,
                                    'goal': GoalTile}[tile_type](tile_name)
                if isinstance(tiles[tile_name], PlayerTile):
                    players.append(TileRotation(tiles[tile_name], 0))
                neighbors_names[tile_name] = tile_data.split()
            for tile_name, tile in tiles.items():
                tile.neighbors = [TileRotation(tiles[neighbor_name[1:]],
                                               int(neighbor_name[0]))
                                  if neighbor_name[1:] in tiles.keys() else wall
                                  for neighbor_name in neighbors_names[tile_name]]
            for tile in tiles.values():
                tile.verify()
            return players, tiles.values()
        else:
            raise ValueError('unknown level format')


def verify(tiles_set):
    for tile in tiles_set:
        tile.verify(tiles_set)


@dataclass
class ScreenSettings:
    screen: pygame.Surface
    tile_size: int  # in pixels
    screen_x: int  # in tiles
    screen_y: int  # in tiles
    player_x: int  # in tiles
    player_y: int  # in tiles

    @property
    def offsets(self):
        tile_offset = Fraction(self.tile_size - 1, 2)
        return (self.player_x * self.tile_size + tile_offset,
                self.player_y * self.tile_size + tile_offset)


class Ray:
    def __init__(self, x, y):
        if y:
            self.is_lower = y > 0
            self.ratio = Fraction(x, y)
        else:
            self.is_lower = x > 0
            self.ratio = float('+inf')

    def __eq__(self, other):
        return self.is_lower == other.is_lower and self.ratio == other.ratio

    def __ne__(self, other):
        return self.is_lower != other.is_lower or self.ratio != other.ratio

    def is_between(self, other1, other2):
        if other1 in (self, other2):
            return True
        if self == other2:
            return False
        r0, r1, r2 = sorted((self, other1, other2),
                            key=lambda r: (r.is_lower, r.ratio))
        # This evaluates to True for odd/negative permutations
        return (((r0 is self) or (r1 is other1) or (r2 is other2)) and
                not ((r0 is self) and (r1 is other1)))

    def transpose(self):
        sign = 1 if self.is_lower else -1
        if self.ratio == float('+inf'):
            return Ray(0, sign)
        return Ray(sign, sign * self.ratio)


def _get_range_bounds(offset_x: Fraction, offset_y: Fraction,
                      left: Ray, right: Ray, py: int, x_min: int, x_max: int):
    if left == right:
        return (x_min, x_max),
    y1 = py - offset_y  # y relative to the player
    left1 = y1 * left.ratio + offset_x
    right1 = y1 * right.ratio + offset_x
    is_lower = y1 > 0
    if not is_lower:
        left1, right1 = right1, left1
    if left.is_lower == right.is_lower:
        if left.is_lower == is_lower:
            if left.ratio < right.ratio:
                return (int(left1), int(right1)),
            else:
                return (x_min, int(right1)), (int(left1), x_max)
        elif left.ratio < right.ratio:
            return ()
        else:
            return (x_min, x_max),
    elif left.is_lower:
        return (int(left1), x_max),
    else:
        return (x_min, int(right1)),


def get_range_bounds(offset_x: Fraction, offset_y: Fraction,
                     left: Ray, right: Ray, py: int, x_min: int, x_max: int):
    """

    :param offset_x: the x coordinate of the center (player) on the screen
    :param offset_y: the y coordinate of the center (player) on the screen
    :param left: start of rendered region (clockwise)
    :param right: end of rendered region (clockwise)
    :param py: pixel y on screen
    :param x_min: left tile end
    :param x_max: right tile end
    :return: None
    """
    for line_start, line_end in _get_range_bounds(offset_x, offset_y,
                                                  left, right, py, x_min, x_max):
        line_start1, line_end1 = max(line_start, x_min), min(line_end, x_max)
        if line_start1 < line_end1:
            yield line_start1, line_end1


def get_range(offset_x: Fraction, offset_y: Fraction,
              left: Ray, right: Ray, py: int, x_min: int, x_max: int):
    return chain.from_iterable(starmap(range, get_range_bounds(offset_x, offset_y,
                                                               left, right,
                                                               py, x_min, x_max)))


def render_part(screen_settings: ScreenSettings, tile: TileRotation,
                x: int, y: int, left0: Ray, right0: Ray, rot: int = 0):
    """
    Render the part between left0 and right0, but only tile and tiles behind it
    :param screen_settings: Screen settings object
    :param tile: The closest to the player tile to render
    :param x: tile X coordinate relative to the player
    :param y: tile Y coordinate relative to the player
    :param left0: start of rendered region (clockwise)
    :param right0: end of rendered region (clockwise)
    :param rot: rotation applied to tile when rendering it
    :return: None
    """
    x_on_screen = screen_settings.player_x + x
    y_on_screen = screen_settings.player_y + y
    # Intersect the given region with the part that is rendered through tile
    if x or y:
        if not (0 <= x_on_screen < screen_settings.screen_x and
                0 <= y_on_screen < screen_settings.screen_y):
            return
        left1 = Ray(x * 2 + (1 if (y, x) < (0, 0) else -1),
                    y * 2 + (1 if (-x, y) < (0, 0) else -1))
        right1 = Ray(x * 2 + (1 if (-y, x) < (0, 0) else -1),
                     y * 2 + (1 if (x, y) < (0, 0) else -1))
        if not (left1.is_between(left0, right0) or
                not left0.is_between(right1, right0) or
                left0.is_between(left1, right1)):
            return
        left = left1 if left1.is_between(left0, right0) else left0
        right = right1 if right1.is_between(left0, right0) else right0
    else:
        left = right = Ray(1, 0)
    x_min = screen_settings.tile_size * x_on_screen
    x_max = x_min + screen_settings.tile_size
    y_min = screen_settings.tile_size * y_on_screen
    y_max = y_min + screen_settings.tile_size
    offset_x, offset_y = screen_settings.offsets
    if False and isinstance(tile.tile, WallTile):
        # Old wall rendering code
        # Can be activated by removing "False and"
        left_t = left.transpose()
        right_t = right.transpose()
        wall_c = pygame.Color('#772953')
        if x < 0:
            for line_start, line_end in get_range_bounds(offset_x, offset_y, right_t, left_t, x_max, y_min, y_max):
                pygame.draw.line(screen_settings.screen, wall_c, (x_max, line_start), (x_max, line_end))
        elif x > 0:
            for line_start, line_end in get_range_bounds(offset_x, offset_y, right_t, left_t, x_min, y_min, y_max):
                pygame.draw.line(screen_settings.screen, wall_c, (x_min, line_start), (x_min, line_end))
        if y < 0:
            for line_start, line_end in get_range_bounds(offset_x, offset_y, left, right, y_max, x_min, x_max):
                pygame.draw.line(screen_settings.screen, wall_c, (line_start, y_max), (line_end, y_max))
        elif y > 0:
            for line_start, line_end in get_range_bounds(offset_x, offset_y, left, right, y_min, x_min, x_max):
                pygame.draw.line(screen_settings.screen, wall_c, (line_start, y_min), (line_end, y_min))
        return
    # Render the tile
    texture = tile.tile.get_texture(screen_settings.tile_size, rot)
    for pyr, pya in enumerate(range(y_min, y_max)):
        for start, end in get_range_bounds(offset_x, offset_y, left, right,
                                           pya, x_min, x_max):
            screen_settings.screen.blit(
                texture,
                (start, pya, end - start, 1),
                (start - screen_settings.tile_size * x_on_screen, pyr,
                 end - start, 1)
            )
    # Recursively render the tiles behind it
    if tile.tile.see_through:
        if y >= 0:
            render_part(screen_settings, tile.get_neighbor(0).rotate(2), x, y + 1,
                        left, right, 0)
        if x >= 0:
            render_part(screen_settings, tile.get_neighbor(1).rotate(1), x + 1, y,
                        left, right, 1)
        if y <= 0:
            render_part(screen_settings, tile.get_neighbor(2).rotate(0), x, y - 1,
                        left, right, 2)
        if x <= 0:
            render_part(screen_settings, tile.get_neighbor(3).rotate(3), x - 1, y,
                        left, right, 3)


def render(screen_settings, player):
    render_part(screen_settings, player, 0, 0, Ray(1, 0), Ray(1, 0))


def move_tile(tile: TileRotation, changed_list, moving_list, remove_list,
              is_player, on_win=lambda: None):
    """
    Move a tile or, if it's empty, remove it
    :param tile: tile to be moved
    :param changed_list: List of tiles changed in this move
    :param moving_list: List of tiles moving in this move
    :param remove_list: List of tiles to remove in this move
    :param is_player: Whether the tile is a player
    :param on_win: Callback if the player won
    :return: True if (re)moved successfully
    """
    # Prevent same tile from being moved twice in one move
    if tile.tile.is_moving:
        return False
    tile.tile.is_moving = True
    moving_list.append(tile.tile)
    # Check if this can be moved
    if not isinstance(tile.tile, (PlayerTile if is_player
                                  else (EmptyTile, PortalTile))):
        return False
    # Next tiles to be (re)moved
    # (they're the same for players, but different for portals)
    next_tile1 = tile.get_neighbor(2)
    next_tile2 = tile.get_neighbor(6)
    if isinstance(tile.tile, EmptyTile):
        tile.get_neighbor(0).set_neighbor_mutual(0, next_tile1, changed_list)
        remove_list.append(tile.tile)
        return True
    if (isinstance(next_tile1.tile, WallTile) or
            isinstance(next_tile2.tile, WallTile)):
        return False  # to avoid error later
    # Insert a tile in the place the player or portal is leaving
    # (in the latter case, it leaves two tiles,
    # but one of them is where the one that pushed it goes)
    new_empty_tile = TileRotation(EmptyTile(), 0)
    new_empty_tile.tile.neighbors = [None, None, None, None]
    new_empty_tile.set_neighbor_mutual(0, tile.get_neighbor(4), changed_list)
    new_empty_tile.set_neighbor_mutual(1, tile.get_neighbor(5), changed_list)
    new_empty_tile.set_neighbor_mutual(2, tile.rotate(4), changed_list)
    new_empty_tile.set_neighbor_mutual(3, tile.get_neighbor(3), changed_list)
    # Change lateral links
    tile.set_neighbor_mutual(1, next_tile1.get_neighbor(1), changed_list)
    tile.set_neighbor_mutual(7, next_tile2.get_neighbor(7), changed_list)
    if isinstance(tile.tile, PlayerTile):
        if isinstance(next_tile1.tile, GoalTile):
            on_win()
        return move_tile(next_tile1,
                         changed_list, moving_list, remove_list, False)
    tile.set_neighbor_mutual(3, next_tile1.get_neighbor(-1), changed_list)
    tile.set_neighbor_mutual(5, next_tile2.get_neighbor(1), changed_list)
    # Push
    return (move_tile(next_tile1, changed_list, moving_list, remove_list, False)
            and
            move_tile(next_tile2, changed_list, moving_list, remove_list, False))


def move_player(player, all_set, on_win):
    changed_list = []
    moving_list = []
    remove_list = []
    success = move_tile(player,
                        changed_list, moving_list, remove_list, True, on_win)
    for tile in moving_list:
        tile.is_moving = False
    for tile in changed_list:
        if success:
            tile.neighbors = tile.new_neighbors
            all_set.add(tile)
        tile.new_neighbors = None
    if success:
        for tile in remove_list:
            all_set.remove(tile)
    verify(all_set)
    return success


def play(screen, level_fn):
    """
    :param screen: the screen as Pygame surface
    :param level_fn: Level filename
    :return: None
    """
    def on_win():
        nonlocal player_won
        player_won = True

    screen_settings = ScreenSettings(screen=screen,
                                     tile_size=TILE_SIZE,
                                     screen_x=VIEW_DIST * 2 + 1,
                                     screen_y=VIEW_DIST * 2 + 1,
                                     player_x=VIEW_DIST,
                                     player_y=VIEW_DIST)

    player_won = False
    players, tiles_list = load_level(level_fn)
    player_i = 0
    player = players[player_i]
    tiles_set = set(tiles_list)
    del tiles_list
    changed = True
    while True:
        if changed:
            screen.fill((0, 0, 0))
            render(screen_settings, player)
            pygame.display.flip()
            changed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                elif event.key == pygame.K_q:
                    player = player.rotate(1)
                    changed = True
                elif event.key == pygame.K_e:
                    player = player.rotate(-1)
                    changed = True
                elif event.key in (pygame.K_w, pygame.K_UP):
                    if move_player(player, tiles_set, on_win):
                        changed = True
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    if move_player(player.rotate(1), tiles_set, on_win):
                        changed = True
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    if move_player(player.rotate(2), tiles_set, on_win):
                        changed = True
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    if move_player(player.rotate(3), tiles_set, on_win):
                        changed = True
                elif event.key == pygame.K_SPACE:
                    player_i = (player_i + 1) % len(players)
                    player = players[player_i]
                    changed = True
                if player_won:
                    win_screen(screen)
                    return


def win_screen(screen):
    pygame.draw.rect(screen, pygame.Color('#FFFFFF'), pygame.Rect(
        (SCREEN_SIZE - WIN_WIDTH) // 2,
        (SCREEN_SIZE - WIN_HEIGHT) // 2,
        WIN_WIDTH,
        WIN_HEIGHT
    ))
    string_rendered = pygame.font.Font(None, 50).render('You won!', True,
                                                        pygame.Color('#000000'))
    string_rect = string_rendered.get_rect()
    string_rect.top = (SCREEN_SIZE - string_rect.height) // 2
    string_rect.x = (SCREEN_SIZE - string_rect.width) // 2
    screen.blit(string_rendered, string_rect)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return


if __name__ == '__main__':
    main()
