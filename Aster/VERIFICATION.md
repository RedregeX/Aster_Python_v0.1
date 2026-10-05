# Verification — version 0.1.0

Checked on 5 October 2026 using Python 3.12 on Linux.

Environment:

- ModernGL 5.12.0, GLFW 2.10.2
- NumPy 2.3.5, Pillow 12.3.0
- Mesa llvmpipe OpenGL 4.5, with an offscreen EGL context

Results:

- 18 automated tests passed, including real OpenGL renders of all three scenes.
- Actual 1280 × 800 renders were inspected for galaxy, nebula and star system.
- Particle generation is deterministic, finite and changes with the seed.
- Camera movement is normalized, and each opening view centers its scene.
- Settings survive a write/read round trip; damaged preference files reset.
- Input routing, mouse movement calculations, scroll bounds and UI hit regions
  were checked with OS input calls mocked.
- Bloom and density alter the actual rendered pixels as expected.
- Consecutive frames retain the same viewport and image when animation is fixed.
- Scene replacement and framebuffer resizing complete without OpenGL errors.
- Python syntax compilation, shell launcher syntax and CLI help were checked.

The rendering checks use actual shaders and the same renderer as the desktop
app. They are not generated mockups.

Not checked on this host:

- A native Windows or macOS window, mouse capture and fullscreen.
- The Windows batch launcher running in cmd.exe.
- A Windows PyInstaller EXE build.
- Performance on a physical GPU.

The available host has no desktop display, so the graphical window was not
opened here. Use Start_Aster.bat on your Windows desktop for that final check.
