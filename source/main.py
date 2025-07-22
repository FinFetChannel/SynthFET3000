# /// script
# dependencies = [
# "pygame-ce",
# "numpy",
# ]
# ///

import pygame as pg
import numpy as np
import pygame.sndarray
import asyncio
import sys
import wave
from synth import *
from screens import *

async def main():
    pg.init()
    pg.mixer.init(44100, -16, 16, 512)
    pg.mixer.set_num_channels(64)

    WEB = False
    if sys.platform in ["wasi", "emscripten"]:
        WEB = True
        from platform import window
        #window.canvas.style.imageRendering = "pixelated"
        screen = pg.display.set_mode((1280, 660))
    else:
        screen = pg.display.set_mode((1280, 660), pg.SCALED)
    
    font = pg.font.Font(None, 36)
    logo = pg.image.load("logo.png").convert_alpha()
    logo_scaled = pg.transform.scale_by(logo, 2)
    logo_scaled.set_alpha(4)
    
    
    base_freq = 65.4
    sampling_rate = 44100
    base_frames = np.linspace(0,2*np.pi, int(sampling_rate/base_freq))
    duration = 0.5
    max_keys = 26
    start_key = 12
    reverb = 0
    sustain = 0
    tremolo_freq = 5
    instruments = [None, None, None, None, None, None]
    base_wave = gen_noise(base_frames, 31)
    base_wave = smoothen(smoothen(smoothen(base_wave, 200),100))
    envelope = gen_plucked(base_wave)
    
    click_sound = make_sound(synth(131, base_wave, envelope, duration=0.05, base_freq=65.4, sampling_rate=44100, reverb=1))
    click_sound.set_volume(0.2)
    notes = gen_sounds(noteslist, base_wave, envelope, 1, base_freq, sampling_rate, 0)
    instruments[0] = ["Guitry", notes, base_wave.copy(), envelope.copy(), 0, 1, 1.]

    screen.fill((25,00,25))
    for i in range(60):
        screen.blit(logo_scaled, (450,105))
        pg.display.update()
        if i%10 == 0:
            notes[noteslist[i//2+5]][0].set_volume(0.1+i/100)
            notes[noteslist[i//2+5]][0].play()
        await asyncio.sleep((not WEB)*1/60)
    logo_scaled.set_alpha(15)

    
    envelope = gen_adsr(base_wave)
    base_wave = np.sin(np.linspace(0, np.pi*duration*13, len(envelope)))
    base_wave = smoothen(smoothen(gen_tremolo(base_wave, duration, 5.3)))
    notes = gen_sounds(noteslist, base_wave, envelope, duration, base_freq, sampling_rate, 0)
    instruments[1] = ["Saxophony", notes, base_wave.copy(), envelope.copy(), 0, sustain, duration]
    envelope = gen_adsr(base_wave)
    
    for i, last_instrument in enumerate(["Square", "Triangle", "Sawtooth", "Pyano"]):
        base_wave = [gen_square, gen_triangle, gen_sawtooth, gen_pyano][i](base_frames)
        notes = gen_sounds(noteslist, base_wave, envelope, duration, base_freq, sampling_rate, reverb)
        instruments[5-i] = [last_instrument, notes, base_wave.copy(), envelope.copy(), reverb, sustain, duration]

    tracks = []
    for i in range(6):
        tracks.append([i, [], False])
        for j in range(16):
            tracks[i][1].append([])    
    current_track = 0
    current_page = 0
    tracker_start = 23
    bpm = 80
    current_play, max_play, next_play = 0, 0, 0

    
    running = 1


    
    clock = pg.Clock()
    notes_playing = []
    click_time = 0
    total_time = 0
    current_screen = "Keyboard"
    pressed_keys = []
    fingers = {}
    full_refresh = 1
    while running:
        delta_time = clock.tick()/1000
        click_time += delta_time
        total_time += delta_time
        redraw = 0
        if full_refresh:
            full_refresh = 0
            redraw = 1
        mouse_click = 0
        mouse_pos = pg.mouse.get_pos()

        if click_time > 0.3:
            redraw = mouse_click = pg.mouse.get_pressed(3)[0]

        for event in pg.event.get():
            
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = False
            if event.type == pg.KEYDOWN:
                pressed_keys.append(event.key)
                if event.key == pg.K_SPACE:
                    if current_screen in ["Wave editor", "Envelope Fx"]:
                        notes = gen_sounds(noteslist, base_wave, envelope, duration, base_freq, sampling_rate, reverb)
                    elif current_screen == "Tracker":
                        if current_play < max_play:
                            max_play, next_play = 0,0
                        else:
                            current_play = section_play = current_page
                            max_play = current_page + 16
                if event.key == pg.K_LEFT:
                    start_key = max(0, start_key-12)
                    redraw = 1
                if event.key == pg.K_RIGHT:
                    start_key = min(36+12*(max_keys==13), start_key+12)
                    redraw = 1
                key = str(event.unicode).lower()
                if key in overlap.keys():
                    key = overlap[key]
                
                if key != "" and key in keylist and keylist.index(key)+start_key < len(noteslist):
                    redraw = play_key(key, start_key, notes_playing, notes)
                        
            if event.type == pg.KEYUP:
                pressed_keys.remove(event.key)
                key = str(event.unicode).lower()
                if key in overlap.keys():
                    key = overlap[key]
                redraw = stop_key(key, start_key, notes_playing, notes, sustain)
            
            if event.type == pg.FINGERDOWN:
                x = event.x * 1280
                y = event.y * 660
                if current_screen=="Keyboard" and x>=80 and x<1200 and y>=95 and y<600:
                    key = get_pressed_key(x, y, max_keys)
                    redraw = play_key(key, start_key, notes_playing, notes)
                    click_time = 0
                    fingers[event.finger_id] = key
            if event.type == pygame.FINGERUP:
                if event.finger_id in fingers:
                    redraw = stop_key(fingers[event.finger_id], start_key, notes_playing, notes, sustain)
                    fingers.pop(event.finger_id, None)
            if event.type == pg.FINGERMOTION:
                if event.finger_id in fingers:
                    x = event.x * 1280
                    y = event.y * 660
                    if current_screen=="Keyboard" and x>=80 and x<1200 and y>=95 and y<600:
                        key = get_pressed_key(x, y, max_keys)
                    if fingers[event.finger_id] != key:
                        redraw = stop_key(fingers[event.finger_id], start_key, notes_playing, notes, sustain)
                        fingers.pop(event.finger_id, None)
                        redraw = play_key(key, start_key, notes_playing, notes)
                        fingers[event.finger_id] = key
        
        x, y = mouse_pos
        if len(fingers) == 0 and mouse_click and current_screen=="Keyboard" and x>=80 and x<1200 and y>=95 and y<600:
            key = get_pressed_key(x, y, max_keys)
            if noteslist[keylist.index(key)+start_key] not in notes_playing:
                redraw = play_key(key, start_key, notes_playing, notes)

        if len(pressed_keys)==0 and not mouse_click and len(notes_playing)>0 and len(fingers)==0 and click_time > duration:
            notes_playing = mute_sounds(notes_playing, notes)
            redraw = True
        
        buttons = ["<<", "Keyboard", "Wave editor", "Envelope", "Tracker", "Options", ">>"]
        for i in range(len(buttons)):
            rect = pg.rect.Rect(20+i*180, 10, 170, 70)
            if mouse_click and rect.collidepoint(mouse_pos):
                notes_playing = mute_sounds(notes_playing, notes)
                click_sound.play(1)
                click_time, mouse_click, redraw, full_refresh = 0, 0, 1, 1
                current_play, max_play, next_play = 0, 0, 0
                if buttons[i] == "<<":
                    start_key = max(0, start_key-12)
                elif buttons[i] == "Keyboard":
                    if current_screen in ["Wave editor", "Envelope", "Options"]:
                        notes = gen_sounds(noteslist, base_wave, envelope, duration, base_freq, sampling_rate, reverb)
                    current_screen = "Keyboard"
                elif buttons[i] == "Wave editor":
                    current_screen = "Wave editor"
                elif buttons[i] == "Envelope":
                    current_screen = "Envelope"
                elif buttons[i] == "Tracker":
                    current_screen = "Tracker"
                elif buttons[i] == "Options":
                    current_screen = "Options"
                elif buttons[i] == ">>":
                    start_key = min(36, start_key+12)

            if redraw or click_time < 0.2:
                pg.draw.rect(screen, (255-50*(current_screen==buttons[i]),255,255),rect, border_radius=5)
                text = buttons[i]
                text = font.render(text, 1, (0,0,0))
                text_rect = text.get_rect()
                text_rect.center = rect.center
                screen.blit(text, text_rect)

        if current_screen == "Wave editor":
            buttons = ["Sine", "Square", "Triangle", "Sawtooth", "Pyano", "Noise", "Smoothen", "Apply"]
            if redraw:
                pg.draw.rect(screen, (0,0,0), [0, 80, 1280, 580])
                screen.blit(logo_scaled, (450,105))
            for i in range(len(buttons)):
                rect = pg.rect.Rect(40+i*150, 600, 140, 55)
                if mouse_click and rect.collidepoint(mouse_pos):
                    click_sound.play(1)
                    notes_playing = mute_sounds(notes_playing, notes)
                    click_time, mouse_click, redraw, full_refresh = 0, 0, 1, 1
                    if buttons[i] not in ["Smoothen", "Apply"]:
                        last_instrument = buttons[i]
                    if buttons[i] == "Sine":
                        base_wave = gen_sine(base_frames)
                    elif buttons[i] == "Square":
                        base_wave = gen_square(base_frames)
                    elif buttons[i] == "Triangle":
                        base_wave = gen_triangle(base_frames)
                    elif buttons[i] == "Sawtooth":
                        base_wave = gen_sawtooth(base_frames)
                    elif buttons[i] == "Pyano":
                        base_wave = gen_pyano(base_frames, mouse_pos[0]+total_time)
                    elif buttons[i] == "Noise":
                        base_wave = gen_noise(base_frames, mouse_pos[0]+total_time)
                    elif buttons[i] == "Smoothen":
                        base_wave = smoothen(base_wave)
                    #elif buttons[i] == "Apply":
                    notes = gen_sounds(noteslist, base_wave, envelope, duration, base_freq, sampling_rate, reverb)
                if redraw or click_time < 0.2:
                    pg.draw.rect(screen, (255,255,255),rect, border_radius=5)
                    text = font.render(buttons[i], 1, (0,0,0))
                    text_rect = text.get_rect()
                    text_rect.center = rect.center
                    screen.blit(text, text_rect)
            if mouse_click and click_time > 0.2 and mouse_pos[1]>=95 and mouse_pos[1]<600:
                update_wave(base_wave, mouse_pos, wrap=True)
                redraw = 1
            if redraw or click_time < 0.2:
                draw_wave(base_wave, screen, (255,255,255), True)
        elif current_screen == "Envelope":
            buttons = ["ADSR", "Ramp", "Plucked", "Noise", f"Tremolo\n   {tremolo_freq} Hz", "Smoothen", "Apply"]
            if redraw:
                pg.draw.rect(screen, (0,0,0), [0, 80, 1280, 580])
                screen.blit(logo_scaled, (450,105))
            for i in range(len(buttons)):
                rect = pg.rect.Rect(100+i*160, 600, 150, 55)
                if mouse_click and rect.collidepoint(mouse_pos):
                    click_sound.play(1)
                    notes_playing = mute_sounds(notes_playing, notes)
                    click_time, mouse_click, redraw, full_refresh = 0, 0, 1, 1
                    if buttons[i] == "ADSR":
                        envelope = gen_adsr(envelope)
                    elif "Tremolo" in buttons[i]:
                        envelope = gen_tremolo(envelope, duration, tremolo_freq)
                    elif buttons[i] == "Plucked":
                        envelope = gen_plucked(envelope)
                    elif buttons[i] == "Ramp":
                        envelope = gen_ramp(envelope)
                    elif buttons[i] == "Noise":
                        envelope = gen_noise_env(envelope)
                    elif buttons[i] == "Smoothen":
                        envelope = np.convolve(envelope, np.ones(20)/20, "same")
                    #elif buttons[i] == "Apply":
                    notes = gen_sounds(noteslist, base_wave, envelope, duration, base_freq, sampling_rate, reverb)
                if redraw or click_time < 0.2:
                    pg.draw.rect(screen, (255,255,255),rect, border_radius=5)
                    text = font.render(buttons[i], 1, (0,0,0))
                    text_rect = text.get_rect()
                    text_rect.center = rect.center
                    screen.blit(text, text_rect)
            if mouse_click and click_time > 0.2 and mouse_pos[1]>=95 and mouse_pos[1]<600 and mouse_pos[0]>=140 and mouse_pos[0]<1140:
                update_wave(envelope, (mouse_pos[0], 630-mouse_pos[1]/2))
                envelope = np.clip(envelope, 0, 1)
                redraw = 1
            if redraw or click_time < 0.2:
                draw_wave(-envelope*2+1, screen)
        elif current_screen == "Options":
            buttons = [[f"Number of keys: {max_keys}", f"< Sample lenght: {duration}s >", f"< Sustain: {sustain}s >",
                        f"Effect: {["off", "Reverb", "Overdrive"][reverb]}", f"< Tremolo: {tremolo_freq}Hz >","Apply"],
                        [" \nCopy to editor instrument "]*6,
                        ["--> Overwrite"]*6]
            if redraw:
                pg.draw.rect(screen, (0,0,0), [0, 80, 1280, 580])
                screen.blit(logo, (1045, 200))
            for i in range(len(buttons)):
                for j in range(len(buttons[i])):
                    rect = pg.rect.Rect(25+400*i, 100+90*j, 340, 80)
                    if mouse_click and rect.collidepoint(mouse_pos):
                        click_sound.play(1)
                        notes_playing = mute_sounds(notes_playing, notes)
                        click_time, mouse_click, redraw, full_refresh = 0, 0, 1, 1
                        increment = int(mouse_pos[0]>rect.centerx)-int(mouse_pos[0]<rect.centerx)
                        if "Sustain" in buttons[i][j]:
                            sustain = max(0,min(duration,(sustain+0.25*increment)))
                        elif "lenght" in buttons[i][j]:
                            duration = max(0.25,min(3.,(duration+0.25*increment)))
                            sustain = min(sustain, duration)
                        elif "Number" in buttons[i][j]:
                            max_keys = {13:26, 26:13}[max_keys]
                        elif "Effect" in buttons[i][j]:
                            reverb = (reverb+1)%3
                        elif "Tremolo" in buttons[i][j]:
                            tremolo_freq = min(25,max(1,(tremolo_freq+increment)))
                        elif buttons[i][j] == "Apply":
                            notes = gen_sounds(noteslist, base_wave, envelope, duration, base_freq, sampling_rate, reverb)
                        elif "Overwrite" in buttons[i][j]:
                            instruments[j] = [last_instrument, notes, base_wave.copy(), envelope.copy(), reverb, sustain, duration]
                        elif "Copy" in buttons[i][j] and not instruments[j] is None:
                            last_instrument, notes2, base_wave, envelope, reverb, sustain, duration = instruments[j]
                        #if not "Overwrite" in buttons[i][j] and not "Number" in buttons[i][j] and not "Tremolo" in buttons[i][j]:
                            notes = gen_sounds(noteslist, base_wave, envelope, duration, base_freq, sampling_rate, reverb)
                            #click_time = -0.2

                    if redraw or click_time < 0.2:
                        text_color = (0,0,0)
                        if "Overwrite" in buttons[i][j]:
                            rect.x -= 50
                            rect.width -= 100
                            text_color = (255, 100, 100)
                        pg.draw.rect(screen, (255,255,235),rect, border_radius=5)
                        text = buttons[i][j]
                        if "Copy" in buttons[i][j]:
                            text += str(j)
                            screen.blit(font.render(instruments[j][0], 1, (55,155,0)), (rect.centerx-40, rect.y+10))

                        text = font.render(text, 1, text_color)
                        text_rect = text.get_rect()
                        text_rect.center = rect.center
                        screen.blit(text, text_rect)
        elif current_screen == "Tracker":
            if current_play < max_play and total_time > next_play-delta_time/2:
                next_play = total_time + 15/bpm
                redraw = 1
                for track in tracks:
                    if track[2] == 0:
                        continue
                    track_inst = track[0]
                    volume = min(0.5, 1/(len(track[1][current_play])+1))
                    for note in track[1][current_play]:
                        instruments[track_inst][1][note][0].set_volume(volume)
                        instruments[track_inst][1][note][0].play()
                        instruments[track_inst][1][note][0].fadeout(int(15000/bpm+100+instruments[track_inst][5]*1000))
                current_play = (current_play+1)%max_play
                if current_play == 0:
                    current_play = section_play
                    current_page = section_play
                if current_play >= current_page + 16:
                    current_page = min(len(tracks[0][1])-16, current_page + 16)

            if redraw:
                pg.draw.rect(screen, (0,0,0), [0, 80, 1280, 580])
                for i in range(12):
                    rect = pg.rect.Rect(145, 85+47*i, 45, 45)
                    pg.draw.rect(screen, (255,255,255),rect,0,5)
                    note = noteslist[tracker_start-i]
                    text = font.render(note, 1, (0,9,9) )
                    text_rect = text.get_rect()
                    text_rect.center = rect.center
                    screen.blit(text, text_rect)
                    rect.width = 66
                    rect.x -= 21
                    for j in range(16):
                        rect.x += 68
                        playing = ((current_play == current_page+j) and (current_play < max_play)) or note in notes_playing
                        if mouse_click and rect.collidepoint(mouse_pos):
                            click_time, mouse_click, redraw, full_refresh = 0, 0, 1, 1
                            if note in tracks[current_track][1][current_page+j]:
                                tracks[current_track][1][current_page+j].remove(note)
                                click_sound.play(1)
                            else:
                                tracks[current_track][2] = 1
                                tracks[current_track][1][current_page+j].append(note)
                                track_inst = tracks[current_track][0]
                                instruments[track_inst][1][note][0].play()
                                instruments[track_inst][1][note][0].fadeout(int(60000/bpm)+100)
                        if note in tracks[current_track][1][current_page+j]:
                            pg.draw.rect(screen, (55+j%4*20,50+100*playing,155-j%4*20),rect,0,5)
                        elif (note in tracks[(current_track+1)%6][1][current_page+j] or note in tracks[(current_track+2)%6][1][current_page+j] or 
                              note in tracks[(current_track+3)%6][1][current_page+j] or note in tracks[(current_track+4)%6][1][current_page+j] or 
                              note in tracks[(current_track+5)%6][1][current_page+j]):
                            pg.draw.rect(screen, (255-j%4*25,150+50*playing,255),rect,0,5)
                        else:
                            pg.draw.rect(screen, (255-j%4*50,200+50*playing,255),rect,0,5)
                screen.blit(logo_scaled, (450,105))
            buttons = [" < Play >\nSect.|  All", f"< Instr. {tracks[current_track][0]} >\n"+instruments[tracks[current_track][0]][0],
                       f"<<  |  >>\n{current_page//4+1}-{current_page//4+4}:{len(tracks[current_track][1])//4}","< V  |  Λ >", 
                        f"< {bpm}BPM >", f"< Current >\n   Track: {current_track}", " < Clear >\nTrack | All  ", "< Export >\nTrack | All  "]
            for i in range(len(buttons)):
                rect = pg.rect.Rect(5, 100+67*i, 136, 62)
                if mouse_click and rect.collidepoint(mouse_pos):
                    click_sound.play(1)
                    notes_playing = mute_sounds(notes_playing, notes)
                    click_time, mouse_click, redraw, full_refresh = 0, 0, 1, 1
                    increment = int(mouse_pos[0]>rect.centerx)-int(mouse_pos[0]<rect.centerx)
                    if "<<" in buttons[i]:
                        if increment > 0:
                            current_page = max(0, current_page+8)
                            if current_page + 9 > len(tracks[current_track][1]):
                                for track in tracks:
                                    for k in range(8):
                                        track[1].append([])
                        else:
                            current_page = max(0, current_page-8)
                    elif "Λ" in buttons[i]:
                        tracker_start = max(11, min(len(noteslist)-1, tracker_start + 6*increment))
                    elif "Play" in buttons[i]:
                        total_time, next_play = 0, 0.5
                        if current_play < max_play:
                            max_play, next_play = 0,0
                        elif increment == -1:
                            current_play = section_play = current_page
                            max_play = current_page + 16
                        else:
                            current_play = section_play = current_page = 0
                            max_play = len(tracks[0][1])
                    elif "Instr." in buttons[i]:
                        tracks[current_track][0] = (tracks[current_track][0] + increment)%len(instruments)
                    elif "BPM" in buttons[i]:
                        bpm = max(1,min(300, bpm+increment))
                    elif "Current" in buttons[i]:
                        current_track = (current_track+increment)%len(tracks)
                    elif "Clear" in buttons[i]:
                        current_page = max_play = next_play = 0
                        if increment == 1:
                            tracks = []
                            for i in range(6):
                                tracks.append([i, [], 0])
                                for j in range(16):
                                    tracks[i][1].append([])
                        else:
                            #tracks[current_track][1] = []
                            tracks[current_track][2] = 0

                            for j in range(len(tracks[current_track][1] )):#16):
                                tracks[current_track][1][j] = []

                    elif "Export" in buttons[i]:
                        if increment == 1:
                            arrays = gen_song(tracks, instruments, bpm)
                            name = "song_synthfet3000"
                        else:
                            arrays = gen_song([tracks[current_track]], instruments, bpm)
                            name = f"track{current_track}_synthfet3000"
                        if len(arrays) > 0:
                            export_song(arrays, WEB, name)

                if redraw:
                    pg.draw.rect(screen, (255,255,255),rect, 0,5)
                    text = buttons[i]
                    if "Play" in text and current_play < max_play:
                        text = "Stop"
                    if ">>" in text and current_page + 17 > len(tracks[current_track][1]):
                        text = text.replace(">>","++")
                    text = font.render(text, 1, (0,9,9) )
                    text_rect = text.get_rect()
                    text_rect.center = rect.center
                    screen.blit(text, text_rect)
        elif current_screen == "Keyboard":
            if redraw or click_time < 0.2:
                draw_keyboard(start_key, max_keys, notes_playing, screen, font)            
        
        #screen.blit(font.render(str(int(clock.get_fps())), 1, (255,255,255), (0,0,0)), (0,640))
        pg.display.update()

        await asyncio.sleep(0)

        
    pg.mixer.quit()
    pg.quit()

def gen_song(tracks, instruments, bpm, sampling_rate=44100):
    rendered_list = []
    total_duration = (len(tracks[0][1])+5)*15/bpm
    for track in tracks:
        if track[2] == 0:
            continue
        last_instrument, notes, base_wave, envelope, reverb, sustain, duration = instruments[track[0]]
        frame_len = max(0.25, sustain)
        notes = gen_sound_arrays(notes.keys(), base_wave, envelope, frame_len, reverb=reverb)
        
        
        big_arr = np.zeros(int(total_duration*sampling_rate))
        for i, frame in enumerate(track[1]):
            if len(frame) > 0:
                frame_arr = np.zeros(int(frame_len*sampling_rate))
                for note in frame:
                    frame_arr += notes[note][0]
                if int(sampling_rate*i*15/bpm)+len(frame_arr) < len(big_arr):
                    big_arr[int(sampling_rate*i*15/bpm):int(sampling_rate*i*15/bpm)+len(frame_arr)]=frame_arr/len(frame)
        rendered_list.append(big_arr.copy())
    
    return np.column_stack(rendered_list)


def export_song(array: np.ndarray, WEB, filename="song_synthfet3000", samplerate=44100):
    if array.ndim == 1:
        num_channels = 1
        array = array[:, np.newaxis]
    else:
        num_channels = array.shape[1]

    array = array / np.max(np.abs(array))
    array = np.int16(array * 32767)
    
    filename += ".w"+"av"
    buf = filename
    if WEB:
        import js, io
        buf = io.BytesIO()
    
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(num_channels)  # mono
        wf.setsampwidth(2)  # 2 bytes = 16 bits
        wf.setframerate(samplerate)
        wf.writeframes(array.tobytes())

    if WEB:
        js.eval(f"""
        (() => {{
            const data = new Uint8Array({list(buf.getvalue())});
            const blob = new Blob([data], {{ type: 'audio/wav' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = '{filename}';
            link.click();
        }})();
        """)

def play_key(key, start_key, notes_playing, notes):
    if key in keylist and keylist.index(key)+start_key < len(noteslist):
        note = noteslist[keylist.index(key)+start_key]
        if note in notes_playing:
            notes[note][0].fadeout(300)
            notes_playing.remove(note)
        notes_playing.append(note)
        """if len(notes_playing)> 1:
            for note in notes_playing:
                notes[note][0].set_volume(min(0.5, (notes[note][0].get_volume() + 1/len(notes_playing))/2))"""
        notes[note][0].play()
        return 1

def stop_key(key, start_key, notes_playing, notes, sustain=0):
    if key in keylist and keylist.index(key)+start_key < len(noteslist) and noteslist[keylist.index(key)+start_key] in notes_playing:
        note = noteslist[keylist.index(key)+start_key]
        notes[note][0].fadeout(300+int(sustain*1000))
        notes_playing.remove(note)
        return 1

def mute_sounds(notes_playing, notes):
    for note in notes_playing:
        notes[note][0].fadeout(300)
    return []

def get_pressed_key(x, y, max_keys):
    if y < 400:
        key = "234567asdfghjkl"[int((max_keys/2+0.5+0.5*(max_keys==26))*(x-80)/1120)]
        if not key in "23567sdghj":
            key = white_keys[int((max_keys/2+0.5+0.5*(max_keys==26))*(x-40)/1120)]
    else:
        key = white_keys[int((max_keys/2+0.5+0.5*(max_keys==26))*(x-40)/1120)]
    return key

if __name__=="__main__":
    asyncio.run(main())
