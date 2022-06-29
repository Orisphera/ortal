import sys

import pygame

from main import Ray, get_range_bounds, TILE_SIZE, VIEW_DIST, SCREEN_SIZE


def terminate():
    pygame.quit()
    sys.exit()


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    while True:
        screen.fill(pygame.Color('#772953'))
        mx, my = pygame.mouse.get_pos()
        tx, ty = mx // TILE_SIZE - VIEW_DIST, my // TILE_SIZE - VIEW_DIST
        left = Ray(tx * 2 + (1 if (ty, tx) < (0, 0) else -1),
                   ty * 2 + (1 if (-tx, ty) < (0, 0) else -1))
        right = Ray(tx * 2 + (1 if (-ty, tx) < (0, 0) else -1),
                    ty * 2 + (1 if (tx, ty) < (0, 0) else -1))
        left_t = left.transpose()
        right_t = right.transpose()
        for px in range(SCREEN_SIZE):
            for line_start, line_end in get_range_bounds(right_t, left_t, px, 0, SCREEN_SIZE):
                pygame.draw.line(screen, pygame.Color('#000000'), (px, line_start), (px, line_end))
        pygame.draw.rect(screen, pygame.Color('#FFFFFF'), pygame.Rect(((tx + VIEW_DIST) * TILE_SIZE,
                                                                       (ty + VIEW_DIST) * TILE_SIZE),
                                                                      (TILE_SIZE, TILE_SIZE)), 4)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()


if __name__ == '__main__':
    main()
