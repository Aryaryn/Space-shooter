#!/usr/bin/env python

"""This is a much simpler version of the aliens.py
example. It makes a good place for beginners to get
used to the way pygame works. Gameplay is pretty similar,
but there are a lot less object types to worry about,
and it makes no attempt at using the optional pygame
modules.
It does provide a good method for using the updaterects
to only update the changed parts of the screen, instead of
the entire screen surface. This has large speed benefits
and should be used whenever the fullscreen isn't being changed."""


#import
import random, os.path, sys
import pygame
from pygame.locals import *

if not pygame.image.get_extended():
    raise SystemExit("Requires the extended image loading from SDL_image")


#constants
FRAMES_PER_SEC = 40
PLAYER_SPEED   = 12
MAX_SHOTS      = 5
SHOT_SPEED     = 10
ALIEN_SPEED    = 12
ALIEN_ODDS     = 45
EXPLODE_TIME   = 6
SCREENRECT     = Rect(0, 0, 600, 600)


#some globals for friendly access
dirtyrects = [] # list of update_rects
next_tick = 0   # used for timing
class Img: pass # container for images
main_dir = os.path.split(os.path.abspath(__file__))[0]  # Program's diretory


#first, we define some utility functions
    
def load_image(file, transparent):
    "loads an image, prepares it for play"
    file = os.path.join(main_dir, 'data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s' %
                         (file, pygame.get_error()))
    if transparent:
        corner = surface.get_at((0, 0))
        surface.set_colorkey(corner, RLEACCEL)
    return surface.convert()



# The logic for all the different sprite types

class Actor:
    "An enhanced sort of sprite class"
    def __init__(self, image):
        self.image = image
        self.rect = image.get_rect()
        
    def update(self):
        "update the sprite state for this frame"
        pass
    
    def draw(self, screen):
        "draws the sprite into the screen"
        r = screen.blit(self.image, self.rect)
        dirtyrects.append(r)
        
    def erase(self, screen, background):
        "gets the sprite off of the screen"
        r = screen.blit(background, self.rect, self.rect)
        dirtyrects.append(r)


class Player(Actor):
    "Cheer for our hero"
    def __init__(self):
        Actor.__init__(self, Img.player)
        self.alive = 1
        self.reloading = 0
        self.rect.centerx = SCREENRECT.centerx
        self.rect.bottom = SCREENRECT.bottom - 10

    def move(self, direction):
        self.rect = self.rect.move(direction*PLAYER_SPEED, 0).clamp(SCREENRECT)


class Alien1(Actor):
    "Destroy him or suffer"
    def __init__(self):
        Actor.__init__(self, Img.alien1)
        self.facing = random.choice((-1,1)) * ALIEN_SPEED
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self):
        global SCREENRECT
        self.rect[0] = self.rect[0] + self.facing
        if not SCREENRECT.contains(self.rect):
            self.facing = -self.facing;
            self.rect.top = self.rect.bottom + 3
            self.rect = self.rect.clamp(SCREENRECT)


class Alien2(Actor):
    "Destroy him or suffer"

    def __init__(self):
        Actor.__init__(self, Img.alien2)
        self.facing = random.choice((-1, 1)) * ALIEN_SPEED
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self):
        global SCREENRECT
        self.rect[0] = self.rect[0] + self.facing
        if not SCREENRECT.contains(self.rect):
            self.facing = -self.facing;
            self.rect.top = self.rect.bottom + 3
            self.rect = self.rect.clamp(SCREENRECT)


class Explosion(Actor):
    "Beware the fury"
    def __init__(self, actor):
        Actor.__init__(self, Img.explosion)
        self.life = EXPLODE_TIME
        self.rect.center = actor.rect.center
        
    def update(self):
        self.life = self.life - 1


class Shot(Actor):
    "The big payload"
    def __init__(self, player):
        Actor.__init__(self, Img.shot)
        self.rect.centerx = player.rect.centerx
        self.rect.top = player.rect.top - 10

    def update(self):
        self.rect.top = self.rect.top - SHOT_SPEED
        



def main():
    "Run me for adrenaline"
    global dirtyrects

    # Initialize SDL components
    pygame.init()
    screen = pygame.display.set_mode(SCREENRECT.size, 0)
    clock = pygame.time.Clock()

    # Load the Resources
    Img.background = load_image('newspace.png', 0)
    Img.shot = load_image('shot.gif', 1)
    Img.bomb = load_image('bomb.gif', 1)
    Img.danger = load_image('danger.gif', 1)
    Img.alien1 = load_image('newalien.png', 1)
    Img.alien2 = load_image('newalien2.png', 1)
    Img.player = load_image('theship.png', 1)
    Img.explosion = load_image('esplosion.png', 2)

    # Create the background
    background = pygame.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, Img.background.get_width()):
        background.blit(Img.background, (x, 0))
    screen.blit(background, (0,0))
    pygame.display.flip()

    # Initialize Game Actors
    player = Player()
    aliens1 = [Alien1()]
    aliens2 = [Alien2()]
    shots = []
    explosions = []

    # Main loop
    while player.alive or explosions:
        clock.tick(FRAMES_PER_SEC)

        # Gather Events
        pygame.event.pump()
        keystate = pygame.key.get_pressed()
        if keystate[K_ESCAPE] or pygame.event.peek(QUIT):
            break

        # Clear screen and update actors
        for actor in [player] + aliens1 + aliens2 + shots + explosions:
            actor.erase(screen, background)
            actor.update()
        
        # Clean Dead Explosions and Bullets
        for e in explosions:
            if e.life <= 0:
                explosions.remove(e)
        for s in shots:
            if s.rect.top <= 0:
                shots.remove(s)

        # Move the player
        direction = keystate[K_RIGHT] - keystate[K_LEFT]
        player.move(direction)

        # Create new shots
        if not player.reloading and keystate[K_SPACE] and len(shots) < MAX_SHOTS:
            shots.append(Shot(player))
        player.reloading = keystate[K_SPACE]

        # Create new alien
        if not int(random.random() * ALIEN_ODDS):
            aliens1.append(Alien1())

        # Create new alien
        if not int(random.random() * ALIEN_ODDS):
            aliens2.append(Alien2 ())

        # Detect collisions
        alien1rects = []
        for a in aliens1:
            alien1rects.append(a.rect)

        alien2rects = []
        for a in aliens2:
            alien2rects.append(a.rect)

        hit = player.rect.collidelist(alien1rects)
        if hit != -1:
            alien = aliens1[hit]
            alien = aliens2[hit]
            explosions.append(Explosion(alien1))
            explosions.append(Explosion(alien2))
            explosions.append(Explosion(player))
            aliens1.remove(alien1)
            aliens2.remove(alien2)
            player.alive = 0
        for shot in shots:
            hit = shot.rect.collidelist(alien1rects)
            if hit != -1:
                alien1 = aliens1[hit]
                explosions.append(Explosion(alien1))
                shots.remove(shot)
                aliens1.remove(alien1)
                break
            hit = shot.rect.collidelist(alien2rects)
            if hit != -1:
                alien2 = aliens2[hit]
                explosions.append(Explosion(alien2))
                shots.remove(shot)
                aliens2.remove(alien2)
                break


        # Draw everybody
        for actor in [player] + aliens1 + aliens2 + shots + explosions:
            actor.draw(screen)

        pygame.display.update(dirtyrects)
        dirtyrects = []

    pygame.time.wait(50)
    

#if python says run, let's run!
if __name__ == '__main__':
    main()
    
