import numpy as np
import pygame as pg

def synth(frequency, base_wave, envelope, duration=1, base_freq=65.4, sampling_rate=44100, reverb=0):    
    wave_len = len(base_wave)
    phase_inc = frequency / base_freq

    arr = np.zeros(int(duration * sampling_rate))
    indices = (np.arange(int(duration * sampling_rate)) * phase_inc) % wave_len
    arr = (-np.interp(indices, np.arange(wave_len), base_wave))
    
    arr *= np.interp(np.linspace(0, len(envelope), len(arr)), np.arange(len(envelope)), envelope)
    
    if reverb == 1:
        arr = add_reverb(arr, sampling_rate)
    elif reverb == 2: # overdrive
        arr = np.clip(arr*4, arr.min(), arr.max())*4
        #arr = (arr*2)%1
    
    arr /= np.abs(arr).max()*3
    
    return arr

def add_reverb(signal, sampling_rate=44100, delay_sec=0.02, decay=0.8, num_echoes=10):
    delay_samples = int(delay_sec * sampling_rate)
    output = np.copy(signal)

    for i in range(1, num_echoes + 1):
        echo = np.zeros_like(signal)
        start = delay_samples * i
        if start < len(signal):
            echo[start:] = signal[:-start] * (decay ** i)
            output += echo
    output = output-(np.convolve(output, np.ones(1000)/1000, "same")) # bring back to middle
    return output


def make_sound(arr):
    sound_data = np.asarray([32767 * arr, 32767 * arr]).T.astype(np.int16)
    return pg.sndarray.make_sound(sound_data.copy())

def gen_sounds(noteslist, base_wave, envelope, duration=5, base_freq=65.4, sampling_rate=44100, reverb=0):
    notes = {} 
    freq = 65.4
    for note in noteslist:
        freq = freq * 2 ** (1/12)
        sound = make_sound(synth(freq, base_wave, envelope, duration, base_freq, sampling_rate, reverb))
        notes[note] = [sound, freq]
    
    return notes

def gen_sound_arrays(noteslist, base_wave, envelope, duration=0.25, base_freq=65.4, sampling_rate=44100, reverb=0):
    notes = {} 
    freq = 65.4
    for note in noteslist:
        freq = freq * 2 ** (1/12)
        sound = synth(freq, base_wave, envelope, duration, base_freq, sampling_rate, reverb)
        notes[note] = [sound, freq]
    
    return notes

def gen_sine(base_frames):
    return -np.sin(base_frames)

def gen_square(base_frames):
    wave = np.ones_like(base_frames)
    wave[:int(len(base_frames)*0.5)] *= -1
    return -wave*0.5

def gen_triangle(base_frames):
    wave = np.linspace(3,-1, len(base_frames))
    wave[:len(base_frames)//2] = 2-wave[:len(base_frames)//2]
    return -wave

def gen_sawtooth(base_frames):
    return np.linspace(1,-1,len(base_frames))*0.5

def gen_pyano(base_frames, seed=31):
    wave = gen_noise(base_frames, seed)
    wave = smoothen(smoothen(smoothen(wave, 200),100))
    wave = 2*((wave-wave.min())/(wave.max()-wave.min()))-1
    wave = np.roll(wave, -np.argmin(np.abs(wave)))

    return wave

def gen_noise(base_frames, seed=30):
    np.random.seed(int(seed))
    return np.random.uniform(1,-1,len(base_frames))

def smoothen(base_wave, lenght=20):
    temp_wave = np.ones(len(base_wave)+lenght*2)
    temp_wave[:lenght] = base_wave[-lenght:]
    temp_wave[-lenght:] = base_wave[:lenght]
    temp_wave[lenght:-lenght] = base_wave
    temp_wave = np.convolve(temp_wave, np.ones(lenght)/lenght, mode="same")
    return temp_wave[lenght:-lenght]/np.max(np.abs(temp_wave))

def gen_adsr(envelope, sampling_rate=674):
    attack, sustain, release = 0.02, 0.1, 0.6
    envelope = np.ones_like(envelope)*0.5
    envelope[:int(attack*sampling_rate)] = np.linspace(0,1,int(attack*sampling_rate))
    envelope[int(attack*sampling_rate):int(sustain*sampling_rate)] = np.linspace(1,0.5,int(sustain*sampling_rate)-int(attack*sampling_rate))
    envelope[-int(release*sampling_rate):] = 2*np.linspace(0.5,0, int(release*sampling_rate))**2

    return envelope

def gen_ramp(envelope):
    return np.linspace(1,0,len(envelope))

def gen_plucked(envelope):
    return np.linspace(1,0,len(envelope))**2

def gen_noise_env(envelope):
    #envelope = np.convolve(np.random.uniform(0,1,len(envelope)), np.ones(20)/20, mode="same")
    envelope = np.random.uniform(0,1,len(envelope))
    return envelope/envelope.max()

def gen_tremolo(envelope, duration, freq=4):
    envelope *= (-np.cos(np.linspace(0, np.pi*duration*2*freq, len(envelope))) / 4 + 0.75)

    return envelope

"""from matplotlib import pyplot as plt

base_freq = 65.4
sampling_rate = 44100
base_frames = np.linspace(0,2*np.pi, int(sampling_rate/base_freq))
base_wave = gen_siano(base_frames)
envelope = gen_plucked(base_frames)
arr = synth(440, base_wave, envelope, 1, reverb=1)

plt.plot(arr)
plt.show()"""