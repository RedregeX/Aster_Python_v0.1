"""Entry point for the desktop app or a genuine offscreen OpenGL render."""
import argparse
import logging
from pathlib import Path
import sys
from .config import Settings, load_settings, data_dir


def headless(args,settings):
    import moderngl
    from .camera import Camera
    from .renderer import Renderer
    from .ui import HUD
    from .world import make_world
    options={"require":330}
    if args.backend:
        options["backend"]=args.backend
    elif sys.platform.startswith("linux"):
        options["backend"]="egl"
    ctx=moderngl.create_standalone_context(**options)
    renderer=None
    try:
        renderer=Renderer(ctx,args.width,args.height)
        world=make_world(settings.scene,settings.seed,settings.quality,settings.palette)
        renderer.set_world(world)
        camera=Camera()
        camera.reset(settings.scene)
        overlay=None
        if not args.clean:
            scale=min(args.width/1280,args.height/800)
            overlay=HUD().render(int(args.width/scale),int(args.height/scale),settings,camera,world.count)
        renderer.render(camera,settings,args.time,overlay)
        destination=Path(args.headless).resolve()
        destination.parent.mkdir(parents=True,exist_ok=True)
        renderer.image().save(destination)
        print(f"Rendered {world.count:,} particles on {ctx.info['GL_RENDERER']}: {destination}")
    finally:
        if renderer:
            renderer.release()
        ctx.release()


def main():
    parser=argparse.ArgumentParser(description="Aster — a small procedural universe")
    parser.add_argument("--scene",choices=("galaxy","nebula","system"))
    parser.add_argument("--quality",choices=("low","medium","high","ultra"))
    parser.add_argument("--seed",type=int)
    parser.add_argument("--headless",metavar="PNG",help="Render a still image without opening a window")
    parser.add_argument("--backend",help="Offscreen glcontext backend, for example egl")
    parser.add_argument("--width",type=int,default=1280)
    parser.add_argument("--height",type=int,default=800)
    parser.add_argument("--time",type=float,default=0)
    parser.add_argument("--clean",action="store_true",help="Hide the HUD in headless captures")
    parser.add_argument("--frames",type=int,help="Close after N frames, for desktop smoke checks")
    parser.add_argument("--hidden",action="store_true",help="Open a hidden window for smoke checks")
    args=parser.parse_args()
    if not 320<=args.width<=7680 or not 240<=args.height<=4320:
        parser.error("Image dimensions must be 320–7680 wide and 240–4320 high")
    settings=Settings() if args.headless else load_settings()
    for key in ("scene","quality","seed"):
        value=getattr(args,key)
        if value is not None:
            setattr(settings,key,value)
    settings.validate()
    try:
        if args.headless:
            headless(args,settings)
        else:
            from .app import Application
            Application(settings,args.frames,args.hidden).run()
    except Exception as exc:
        folder=data_dir()
        logfile=folder/"aster.log"
        logging.basicConfig(filename=str(logfile),level=logging.ERROR,force=True)
        logging.exception("Aster failed")
        print(f"\nAster could not start: {exc}\nDetails: {logfile}",file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
