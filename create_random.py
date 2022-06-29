import random


size = int(input())
with open(input(), 'w') as f:
    print('#' * (size + 2), file=f)
    for _ in range(size):
        print('#', *(random.choice(' ' * 9 + '*') for _ in range(size)), '#', sep='', file=f)
    print('#' * (size + 2), file=f)
