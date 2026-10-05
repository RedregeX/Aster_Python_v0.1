# Aster — a small universe

A Python desktop app with procedural galaxies, nebula clouds, an animated
star system and mouse-controlled free flight. The scene is actual 3D geometry
and GPU particles, not a video or an image background.

## Start on Windows

1. Install **Python 3.11 or 3.12** from https://www.python.org/downloads/.
   During setup, enable **Add python.exe to PATH**.
2. Extract the entire ZIP into a normal folder.
3. Double-click **Start_Aster.bat**.

The first launch creates a private Python environment and downloads the four
dependencies. Later launches reuse it. Internet is needed for the first setup;
the app itself works offline and sends no data anywhere.

Requires a graphics driver supporting **OpenGL 3.3**. An integrated Intel or
AMD GPU can be enough; start with Low quality if needed. Actual frame rate
depends on the GPU, resolution and selected quality. It does not require CUDA.

## Start on Linux or macOS

Install Python 3.10+ and run `bash start_aster.sh` from the extracted folder.
Linux requires a working desktop OpenGL driver and X11/Wayland display. Some
Linux distributions also need their `python3-venv` package installed.

Manual setup works on all three systems:

```sh
python -m venv .venv
# Windows:
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run.py
# Linux / macOS:
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

## Explore

The app opens in a slow cinematic orbit. Click **Explore** or press **F** to
capture the mouse and fly. Press **Esc** to release it. Click the three scene
buttons to visit the other environments, or use the number keys.

| Control | Action |
|---|---|
| F / click empty scene | Enter free flight; F also releases the mouse |
| Mouse | Look around during flight |
| W / A / S / D | Forward / left / backward / right |
| Q / E | Move down / up |
| Shift / Ctrl | Fly faster / slower |
| Mouse wheel | Adjust flight speed |
| 1 / 2 / 3 | Galaxy / nebula / star system |
| Home | Return to the opening view |
| Left-click a core or named knot | Select a landmark near the click |
| O | Orbit the selected landmark |
| Space | Pause / resume cloud drift, orbit and planet motion |
| V / Settings button | Open rendering controls |
| R | Generate a new seed |
| C | Cycle three color palettes |
| H | Open controls help |
| Tab | Hide / show all interface elements |
| P | Save a PNG screenshot |
| F11 | Toggle fullscreen |
| Esc | Release mouse and close panels |

The Settings panel adjusts exposure, bloom, particle size and active density.
Quality controls how many particles are generated; density draws a subset
without regenerating the world. High uses approximately **188,500** particles
in the galaxy, **130,000** in the nebula, and **33,401** in the star system.
Ultra doubles the galaxy/nebula counts. Low reduces most counts to 35%.

Preferences are saved when the app closes to `~/.aster/settings.json`.
Screenshots go to `~/.aster/screenshots/` and errors to `~/.aster/aster.log`.
On Windows, `~` is your user folder, for example `C:\Users\YourName`.
Set `ASTER_DATA_DIR` to use a different writable folder.

**P captures exactly what is displayed.** Press Tab first for a clean shot.
The window's close button exits the app.

## What's in this first version

- Four spiral arms, a bright galaxy core and diffuse colored gas.
- A nebula of tangled 3D arcs with embedded stars and drifting cloud particles.
- Four shaded, orbiting planets, a luminous star, orbit tracks and a dust belt.
- Deterministic seeds, three palettes, adjustable render settings and HiDPI-aware UI.
- HDR render target, multi-pass bloom, exposure mapping and custom GLSL shaders.
- Per-user preferences, screenshots, Windows launcher and an optional EXE build script.
- Offscreen rendering for real GPU previews and regression checks.

This is a stylized exploration prototype. It does not simulate gravity or
physical astrophysics. The scenes are separate environments selected from the
interface; there is no seamless galaxy-to-planet transition yet. Selection
targets a small set of named landmarks rather than every individual particle.

## Project layout

```text
aster/
  app.py        desktop window, loop and input
  camera.py     view/projection and flight/orbit camera
  config.py     preferences and validation
  world.py      vectorized procedural scene generation
  renderer.py   GPU buffers, planets, bloom and compositing
  ui.py         interface texture and control hit regions
  shaders/      GLSL vertex and fragment shaders
tests/          generation, camera, preferences, controls and GPU checks
previews/       actual rendered images from this version
run.py          launch entry point
```

Particles are generated in NumPy and uploaded to GPU buffers on scene changes.
Cloud drift and point shading run in GLSL. Python updates the camera, four
planet transforms and UI state; it does not loop over all particles per frame.
The UI texture refreshes on changes and twice per second for live statistics.

## Render a still without a desktop window

```sh
python -m aster --headless nebula.png --scene nebula --seed 42 --quality high
python -m aster --headless galaxy.png --scene galaxy --clean --width 1920 --height 1080
```

Linux offscreen renders use EGL by default. `--backend` can override this.
Offscreen rendering still needs an OpenGL implementation, hardware or software.
`--time 30` renders the scene's animation state at 30 seconds.

## Checks

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

GPU tests skip on a machine with no usable offscreen OpenGL backend. This
version was rendered and tested on Linux using Mesa's software OpenGL renderer.
Native Windows mouse capture, fullscreen, and the optional EXE packaging still
need a local Windows check. See `VERIFICATION.md` for the checks performed.

## Optional Windows EXE

After running the app at least once, double-click **build_exe.bat** on Windows.
The script builds `dist\Aster\Aster.exe` with PyInstaller. Keep the **entire
dist\Aster folder** together; it contains shaders and native libraries.
This download contains source and launch scripts, not a prebuilt Windows EXE.

## If startup fails

- If Python isn't found, install it with the PATH option enabled.
- If dependencies fail, read the launcher output and check the connection.
- If the window can't create OpenGL 3.3, install the GPU manufacturer's driver
  and run the app on the local desktop rather than a remote session.
- If frame rate is low, choose Low quality, reduce density, and use a smaller
  window. Large transparent clouds can be expensive even with fewer particles.
- To reset preferences, close the app and delete `~/.aster/settings.json`.

All visual assets are procedurally generated. No external image downloads,
commercial textures, accounts or API keys are required.
