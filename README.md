# 🎹 SynthFET 3000

**SynthFET 3000** is a browser-compatible audio synthesizer and tracker built with Python and Pygame CE. It lets you design custom waveforms, shape envelopes, add some effects, and compose full multi-track songs using an intuitive tracker interface — all without writing any code.

I made a video about it on [YouTube](www.youtube.com/watch?v=gzugOKLWTTs "Everything Is AWESOME")

## ✨ Features

* **Realtime Keyboard Interface**
  Play notes using your computer keyboard or touchscreen, with adjustable octave range.

* **Waveform Editor**
  Draw your own wave shapes or choose from presets (sine, square, saw, triangle, noise). Smooth and apply them interactively.

* **Envelope Editor**
  Shape the volume dynamics (ADSR, tremolo, pluck, ramp) over time. Smooth and apply envelopes just like waveforms.

* **Tracker Module**
  Compose songs using a familiar grid system:

  * Multi-track pattern editor
  * Per-track instrument selection
  * Infinite song length with section navigation
  * Adjustable tempo (BPM), pitch range, and export options

* **Instrument Manager**
  Save and load up to 6 custom instruments. Instantly swap them in or edit live.

* **Effects**
  Add reverb, overdrive and tremolo with tunable parameters.

* **Web-Compatible**
  Runs in the browser (via GitHub Pages or Itch.io). Installable as a Progressive Web App (PWA).

* **Export to WAV**
  Export full songs or individual tracks to `.wav` files, with separate channels for easy mixing in DAWs like Audacity.

## 📦 Try It Out

* ▶️ [Play it on Itch.io](https://finfetchannel.itch.io/synthfet-3000)
* 💾 [Play or Install PWA via GitHub Pages](https://finfetchannel.github.io/SynthFET3000/)
* 🧠 [Source Code](https://github.com/FinFetChannel/SynthFET3000)

## 🧰 Tech Stack

* **Python** + **Pygame CE**
* **NumPy** (for waveform math and resampling)
* **Wave** (for exporting tracks)
* Uses `pygame.sndarray` to generate custom sounds in real-time

## 🔧 Development Notes

* Designed for experimentation and learning sound synthesis.
* Inspired by *Bosca Ceoil* and classic music trackers.
* Still evolving — implementation details may change.
