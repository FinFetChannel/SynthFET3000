import pygame as pg
import numpy as np

keylist = 'q2w3er5t6y7uzsxdcvgbhnjm,i'
black_keys = "23567sdghj"
white_keys = "qwertyuzxcvbnm,."
overlap = {"i":"z", "o":"x", "p":"c", "9":"s", "0":"d"}
inv_overlap = {overlap[k] : k for k in overlap}

noteslist = []
for scale in "23456":
    for note in "CDEFGAB":
        noteslist.append(note+scale)
        if note not in "EB":
            noteslist.append(note+"#"+scale)
noteslist.append("C7")


def draw_keyboard(start_key, max_keys, notes_playing, screen, font):
    pg.draw.rect(screen, (0,0,0), [0, 80, 1280, 580])
    current_notes = noteslist[start_key:min(len(noteslist), start_key+max_keys)]
    last_white = 41
    n_whites = 0
    for note in current_notes:
        if "#" not in note:
            n_whites += 1
    white_width = 1200//n_whites
    gap = 4-(max_keys>13)*2
    key_index = 0
    for note in current_notes:
        if "#" not in note:
            playing = (note in notes_playing)*2
            pg.draw.rect(screen, (255,250,250), (last_white+playing, 95, white_width-gap-playing*2, 550-playing*4),0,5)
            
            screen.blit(font.render(note,1,(0,0,0)), (last_white+5, 500))
            screen.blit(font.render(white_keys[key_index],1,(0,0,0)), (last_white+5, 550))
            if white_keys[key_index] in inv_overlap.keys():
                screen.blit(font.render(inv_overlap[white_keys[key_index]],1,(0,0,0)), (last_white+20, 550))
            key_index += 1
            last_white += white_width
    last_white = 41
    key_index = 0
    for note in current_notes[1:-1]:
        if "#" in note:
            playing = (note in notes_playing)*2
            pg.draw.rect(screen, (0,0,50), (last_white+white_width*0.65+playing, 95, white_width*0.7-playing*2, 300-playing*4),0,5)
            screen.blit(font.render(note,1,(255,250,250)), (last_white+white_width*0.65+5, 100))
            screen.blit(font.render(black_keys[key_index],1,(255,250,250)), (last_white+white_width*0.65+15, 150))
            if black_keys[key_index] in inv_overlap.keys():
                screen.blit(font.render(inv_overlap[black_keys[key_index]],1,(255,250,250)), (last_white+white_width*0.65+30, 150))
            key_index += 1
        else:
            last_white += white_width

def draw_wave(wave, screen, color=(255,0,0), extend=False):
    #pg.draw.rect(screen, (0,0,0), [0, 80, 1280, 510])
    pg.draw.rect(screen, (255,255,0), [138, 98, 1006, 486], 2)
    duration = len(wave)#int(44100/65.4)
    xs = np.linspace(0,duration, duration)
    ys = wave[:duration+1]
    points = list(zip(xs*1000/duration+140, ys*240+340))
    pg.draw.lines(screen, color, 0, points,4)
    if extend:
        points = list(zip(xs*1000/duration+140-1000, ys*240+340))+points
        points += list(zip(xs*1000/duration+1140, ys*240+340))
    pg.draw.lines(screen, color, 0, points,2)

def update_wave(wave, point, smoothing=3, wrap=False):
    x = int(len(wave)*(point[0]-140)/1000)%len(wave)
    y = np.clip((point[1]-340)/240,-1,1)
    wave[x] = (y + wave[x])/2
    for i in range(1,smoothing):
        if wrap or (x-i >= 0 and x+i < len(wave)):
            wave[x-i] = (wave[x-i] + wave[x-i+1])/2
            wave[(x+i)%len(wave)] = (wave[(x+i)%len(wave)] + wave[(x+i-1)%len(wave)])/2
