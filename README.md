# Ortal
A proof-of-concept game by Orisphera.

## Description
Ortal is a 2D game where everything is aligned to a grid, like in Sokoban, Patrick's Parabox, [XOR](https://en.wikipedia.org/wiki/XOR_(video_game)), and some other games.
It has walls, through which you can't see, and glass, through which you can, but it stops movement, like walls.

The main feature of Ortal is special tiles called portals.
When you go around a portal, you get to a different point; to get to the original point, you have to go around it one more time.
You can move portals.
You can learn more about portals in various theories in [this article](https://bit.ly/3bvL2AJ).

To allow for portals and compactification, Ortal stores the level as a 2D linked list, a format designed specifically for that purpose.
The idea is that each tile stores a link to its neighbors.

## Running
To run Ortal, you need the graphic library Pygame.
To install it, run
```bash
pip install pygame
```
Note that you shouldn't run `pip` with root privileges.

You can download Ortal with
```bash
git clone https://github.com/orisphera/ortal
cd ortal
```
or by clicking on the green "Code" and then downloading and unpacking ZIP 

Run the game by running the main.py file:
```bash
python3 main.py
```

## Cheats
You can activate the "glass eater" cheat by changing the line
```python
class GlassTile(Tile):
```
in main.py into
```python
class GlassTile(EmptyTile):
```
With this cheat, you can move into glass tiles, destroying them.

## Ortal in Orisphera Wiki
There's a [page](https://orisphera.fandom.com/wiki/Ortal_(video_game)) in Orisphera wiki on Ortal.
