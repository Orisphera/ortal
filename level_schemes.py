TILE_TYPES = {' ': 'empty',
              '*': 'glass',
              'p': 'player',
              '@': 'portal',
              '=': 'goal'}


def get_tn(grid, prefix, x, y):
    if grid[y][x] == '#':
        return 'wall'
    return f'{prefix}{x}_{y}'


def get_trn(grid, rot, prefix, x, y):
    return get_tn(grid, f'{rot}{prefix}', x, y)


def convert(in_f, out_f, prefix):
    out_f.write('ortal neighbors\n')
    grid = in_f.read().rstrip('\n').split('\n')
    for x in range(len(grid[0])):
        for y in range(len(grid)):
            if grid[y][x] != '#':
                out_f.write(f'{get_tn(grid, prefix, x, y)} '
                            f'{TILE_TYPES[grid[y][x]]} '
                            f'{get_trn(grid, 2, prefix, x, y + 1)} '
                            f'{get_trn(grid, 3, prefix, x + 1, y)} '
                            f'{get_trn(grid, 0, prefix, x, y - 1)} '
                            f'{get_trn(grid, 1, prefix, x - 1, y)}\n')


def main():
    fn, prefix = input().split()
    with open(f'level_schemes/{fn}.in') as in_f:
        with open(f'level_schemes/{fn}.txt', 'w') as out_f:
            convert(in_f, out_f, prefix)


if __name__ == '__main__':
    main()
