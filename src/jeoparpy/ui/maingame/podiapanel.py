"""
podiapanel.py
Author: Adam Beagle

DESCRIPTION:
    Contains the PodiaPanel class and its utility classes
    Score and Highlight, each described in detail below.


Copyright (C) 2013 Adam Beagle - All Rights Reserved
You may use, distribute, and modify this code under
the terms of the GNU General Public License,
viewable at http://opensource.org/licenses/GPL-3.0

This copyright notice must be retained with any use
of source code from this file.

"""

import pygame

from jeopgamesfc import JeopGameSurface
from ..config import ANSWER_TIME_MS
from ..constants import ANSWER_TIMEOUT, JEOP_BLUE
from ..resmaps import FONTS, IMAGES
from ..util import scale, shadow_text

###############################################################################
class PodiaPanel(JeopGameSurface):
    """
    The JeoparPy panel containing the three player podiums.
    When initialized, a background image, and the three podia
    with player names and $0 are drawn.
    A 'highlight' ability exists for when players buzz in.

    Calling the update() function on every frame with a GameState and
    GameData object will automatically update the surface as needed.

    INHERITED ATTRIBUTES:
      * baseImg
      * dirty
      * rect
      * size

    METHODS:
      * update
      
    """
    def __init__(self, size, gameData):
        """
        Constructor. Initializes the panel with a background
        and the three podia with team names and scores of '$0'
        
        """
        super(PodiaPanel, self).__init__(size)

        scalar = self._init_background()
        self._podiaRects = self._draw_podia(self._init_podia())

        self._draw_player_names([p.name for p in gameData.players],
                                132, scalar)

        self.baseImg = self.copy()

        self._highlight = pygame.sprite.GroupSingle(
            Highlight(self._podiaRects[0].size))

        self._scores = self._init_scores()
        self._scores.draw(self)

        

    def update(self, gameState, gameData):
        """
        Draws necessary changes to the panel. Makes changes only as needed
        based on gameState, so it is safely efficient to call this
        on every frame. 'dirty' attribute set to True if panel
        was changed and required redraw by caller.
        
        """
        gs = gameState

        self._timers.update(gameState, gameData)
        
        if gs.state == gs.BUZZ_IN:
            self._draw_highlight(gs.arg[0])
            self.dirty = True

        #For any type of answer clear highlight, update score, draw.
        if gs.state in gs.ANSWER:
            self._clear_highlight()
            self._scores.update(gameData)
            self._scores.draw(self)
            self.dirty = True
            
        if gs.state == gs.DELAY:
            pygame.time.delay(500)
            
    def _clear_highlight(self):
        self._highlight.clear(self, self.baseImg)

    def _draw_highlight(self, playerI):
        self._highlight.sprite.rect = self._podiaRects[playerI].copy()
        self._highlight.draw(self)

    def _draw_podia(self, podiumSfc):
        """
        Draws the 3 podia to the panel.
        Returns tuple containing the rects of the podia drawn.
        
        """
        rect = podiumSfc.get_rect()
        padding = (self.size[1] - 3*rect.h) / 4
        rect.centerx = self.rect.centerx
        rect.top = padding

        rects = []

        for i in xrange(3):
            self.blit(podiumSfc, rect)
            rects.append(rect.copy())
            
            rect.top += rect.h + padding

        return tuple(rects)

    def _draw_player_names(self, names, yOffset, scalar):
        fonts = (('team1', 42), ('team2', 33), ('team3', 40))
        fonts = tuple((FONTS[n], int(scalar*s)) for n,s in fonts)
        yOffset = int(yOffset*scalar)

        for i, pr in enumerate(self._podiaRects):
            font = pygame.font.Font(*fonts[i])
            text = font.render(names[i], 1, (255, 255, 255))
            rect = text.get_rect()

            rect.centerx = pr.centerx
            rect.y = pr.y + yOffset

            self.blit(text, rect)

    def _get_score_sprite(self, id_):
        """
        Returns pygame.sprite.Sprite object from self._scores whose
        ID attribute matches passed id_, or None if not found.
        
        """
        try:
            return [spr for spr in self._scores.sprites() if spr.ID == id_][0]
        except IndexError:
            return None
            
        
    def _init_background(self):
        img = pygame.image.load(IMAGES['rPanelBG']).convert()
        sizeScalar = float(self.size[1]) / img.get_size()[1]
        img = pygame.transform.smoothscale(img, self.size)
        self.blit(img, (0, 0))

        return sizeScalar


    def _init_podia(self):
        """
        Returns the surface of a single podium, correctly
        scaled for the height of the panel.
        
        """
        img = pygame.image.load(IMAGES['podium']).convert_alpha()
        origSize = img.get_size()

        #Scale image to be 30% height of screen
        h = int(0.3 * self.size[1])
        w = int(origSize[0] * (float(h) / origSize[1]))
        img = pygame.transform.smoothscale(img, (w, h))
        
        return img

    def _init_scores(self):
        sprites = []

        for i in xrange(3):
            sprites.append(Score(self._podiaRects[i], i))

        return pygame.sprite.OrderedUpdates(*sprites)

    def _init_timers(self):
        sprites = []

        for i in xrange(3):
            sprites.append(AnswerTimer(i, self._podiaRects[i],
                                       ANSWER_TIME_MS))

        return pygame.sprite.OrderedUpdates(*sprites)
        

###############################################################################
class Highlight(pygame.sprite.Sprite):
    """ """
    def __init__(self, size):
        super(Highlight, self).__init__()
        img = pygame.image.load(IMAGES['highlight']).convert_alpha()
        self.image = pygame.transform.smoothscale(img, size)
        
        self.rect = self.image.get_rect()

###############################################################################
class Score(pygame.sprite.DirtySprite):
    """ """
    def __init__(self, podiumRect, id_):
        super(Score, self).__init__()
        scalar = (float(podiumRect.w) /
                  pygame.image.load(IMAGES['podium']).get_size()[0])
        posOffset = tuple(int(scalar*x) for x in (64, 30))
        size = tuple(int(scalar*x) for x in (154, 47))
        self.rect = pygame.Rect(podiumRect.topleft, size)
        self.rect.move_ip(*posOffset)

        self.image = pygame.Surface(size)

        self._font = pygame.font.Font(FONTS['score'], int(32*scalar))
        self._posColor = (255, 255, 255)
        self._negColor = (230, 0, 0)

        self._text = '$0'
        self._id = id_

        self._draw_text(self._text, self._posColor)

    def update(self, gameData):
        score = gameData.players[self._id].score
        scoref = gameData.players[self._id].scoref

        if not scoref == self._text:
            color = self._posColor if score >= 0 else self._negColor
            self._text = scoref
            self._draw_text(scoref, color)
            self.dirty = 1
            
    def _draw_text(self, text, color):
        s = text
        text = self._font.render(s, 1, color)

        rect = text.get_rect()
        rect.centerx = self.rect.centerx - self.rect.x
        rect.centery = self.rect.centery - self.rect.y

        shadow, shadRect = shadow_text(s, rect, self._font, 3)

        self.image.fill(JEOP_BLUE)
        self.image.blit(shadow, shadRect)
        self.image.blit(text, rect)

    @property
    def ID(self):
        return self._id

###############################################################################
class AnswerTimer(pygame.sprite.DirtySprite):
    """
    Defines a timer sprite that counts down to 0.

    ATTRIBUTES:
      * dirty
      * ID
      * image
      * rect

    METHODS:
      * update
      
    """

    def __init__(self, id_, podiumRect, timeout, *groups):
        """'timeout' in ms."""
        super(AnswerTimer, self).__init__(*groups)
        print podiumRect
        self._offColor = (30, 30, 30)
        self._onColor = (255, 0, 0)
        self._startTime = None
        self._endTime = None

        self.ID = id_
        self._timerLen = timeout

        self.image = pygame.Surface(self._get_scaled_size(podiumRect))
        self.image.fill(self._offColor)
        self.rect = self.image.get_rect()
        self.rect.topleft = self._get_scaled_pos(podiumRect)
        print self.rect

    def update(self, gameState, gameData):
        gs = gameState

        if gs.state == gs.BUZZ_IN:
            self._endTime = pygame.time.get_ticks() + self._timerLen

        elif gs.state == gs.WAIT_ANSWER:
            currentTime = pygame.time.get_ticks()
            self._draw_bar(currentTime)
            
            if currentTime >= self._endTime:
                pygame.event.post(pygame.event.Event(ANSWER_TIMEOUT))
                self._endTime = None

        elif gs.state in gs.ANSWER:
            self._reset()
                           

    def _draw_bar(self, currentTime):
        et = self._endTime
        ct = currentTime
        tl = self._timerLen
        percDone = et - ct / float(tl)

        if percDone >= 1:
            self.image.fill(self._offColor)
            return

        rect = self.rect.copy()
        rect.w = int(percDone * rect.w)
        rect.centerx = self.rect.centerx

        self.image.fill(self._onColor, rect)

    def _get_scaled_pos(self, podiumRect):
        x = podiumRect.left + scale(83, podiumRect.h, 234)

        y = podiumRect.top + scale(6, podiumRect.h, 234)
        return (x, y)

    def _get_scaled_size(self, podiumRect):
        w = scale(116, podiumRect.h, 234)
        h = scale(9, podiumRect.h, 234)
        return (w, h)

    def _reset(self):
        self._endTime = 0
        self.image.fill(self._offColor)
        
        
