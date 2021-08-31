# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 16:01:02 2018

SCRIPT:
    feedback app for audio visual stimulation from movieclip

TODO:
    1-simple clip showing movie
    2-decorate with pyff feedback class
    Make a 
    Use feedback app as template nback_verbal
@author: nm.costa
"""

import pygame

FPS = 60

pygame.init()
clock = pygame.time.Clock()
movie = pygame.movie.Movie('MELT.MPG')
screen = pygame.display.set_mode(movie.get_size())
movie_screen = pygame.Surface(movie.get_size()).convert()



movie.set_display(movie_screen)
movie.play()


playing = True
while playing:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            movie.stop()
            playing = False

    screen.blit(movie_screen,(0,0))
    pygame.display.update()
    clock.tick(FPS)

pygame.quit()