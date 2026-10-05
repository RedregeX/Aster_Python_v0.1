"""GLFW desktop host and input routing."""
from datetime import datetime
import math
import secrets
import time
import glfw
import moderngl
from .camera import Camera
from .config import SCENES, data_dir, load_settings, save_settings
from .renderer import Renderer
from .ui import HUD
from .world import make_world


class Application:
    def __init__(self, settings=None, frame_limit=None, hidden=False):
        self.settings=settings or load_settings()
        self.camera=Camera()
        self.hud=HUD()
        self.window=None
        self.renderer=None
        self.frame_limit=frame_limit
        self.time=0.0
        self.fps=0.0
        self.notice="Click Explore to fly. H opens the controls."
        self.notice_until=time.monotonic()+8
        self.selected=""
        self.cursor=None
        self.fullscreen=False
        self.window_rect=(100,100,1280,800)
        self.screenshot_pending=False
        self.dirty=True
        self.ui_image=None
        self.ui_tick=0.0
        self.started=False
        if not glfw.init():
            raise RuntimeError("GLFW could not open a desktop display. Run this on your desktop, or use --headless for a still image.")
        try:
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,3)
            glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT,True)
            glfw.window_hint(glfw.VISIBLE,not hidden)
            self.window=glfw.create_window(1280,800,"Aster | a small universe",None,None)
            if not self.window:
                raise RuntimeError("Aster requires an OpenGL 3.3 graphics driver. Update your Intel, AMD or NVIDIA driver and try again.")
            glfw.set_window_size_limits(self.window,960,600,glfw.DONT_CARE,glfw.DONT_CARE)
            glfw.make_context_current(self.window)
            glfw.swap_interval(1)
            self.ctx=moderngl.create_context(require=330)
            self.renderer=Renderer(self.ctx,*glfw.get_framebuffer_size(self.window))
            glfw.set_key_callback(self.window,self.on_key)
            glfw.set_cursor_pos_callback(self.window,self.on_cursor)
            glfw.set_mouse_button_callback(self.window,self.on_button)
            glfw.set_scroll_callback(self.window,self.on_scroll)
            glfw.set_window_focus_callback(self.window,self.on_focus)
            self.rebuild(reset_camera=True)
            self.started=True
        except Exception:
            self.close(save=False)
            raise

    def message(self,text):
        self.notice=text
        self.notice_until=time.monotonic()+4
        self.dirty=True

    def logical_size(self):
        width,height=glfw.get_window_size(self.window)
        scale=max(0.1,min(width/1280,height/800))
        return int(width/scale),int(height/scale),scale

    def rebuild(self,reset_camera=False):
        world=make_world(self.settings.scene,self.settings.seed,self.settings.quality,self.settings.palette)
        self.renderer.set_world(world)
        if reset_camera:
            self.set_flying(False)
            self.camera.reset(self.settings.scene)
            self.selected=""
        self.dirty=True

    def set_flying(self,flying):
        self.camera.flying=flying
        self.cursor=None
        glfw.set_input_mode(self.window,glfw.CURSOR,glfw.CURSOR_DISABLED if flying else glfw.CURSOR_NORMAL)
        if flying:
            self.hud.settings_open=self.hud.help_open=False
        else:
            # Derive orbit parameters from the current position, preventing a
            # jump when releasing the mouse after moving through the scene.
            delta=self.camera.position-self.camera.focus
            self.camera.orbit_radius=max(2.0,float(math.hypot(delta[0],delta[2])))
            self.camera.orbit_height=float(delta[1])
            self.camera.orbit_angle=math.atan2(float(delta[0]),float(delta[2]))
        self.dirty=True

    def dispatch(self,action):
        kind=action[0]
        if kind=="fly":
            self.set_flying(not self.camera.flying)
        elif kind=="scene":
            self.settings.scene=action[1]
            self.time=0
            self.rebuild(reset_camera=True)
        elif kind=="settings":
            if self.camera.flying:
                self.set_flying(False)
            self.hud.settings_open=not self.hud.settings_open
            self.hud.help_open=False
        elif kind=="help":
            if self.camera.flying:
                self.set_flying(False)
            self.hud.help_open=not self.hud.help_open
            self.hud.settings_open=False
        elif kind=="quality":
            self.settings.quality=action[1]
            self.rebuild()
            self.message("Quality: "+action[1].title())
        elif kind=="seed":
            self.settings.seed=secrets.randbelow(100000000)
            self.rebuild()
            self.message("A new field of stars. Seed "+str(self.settings.seed))
        elif kind=="palette":
            self.settings.palette=(self.settings.palette+1)%3
            self.rebuild()
            self.message(("Blue / amber","Tidal / gold","Violet / rose")[self.settings.palette])
        self.dirty=True

    def on_key(self,window,key,scancode,action,mods):
        if action!=glfw.PRESS:
            return
        routes={glfw.KEY_F:("fly",),glfw.KEY_H:("help",),glfw.KEY_V:("settings",),
                glfw.KEY_R:("seed",),glfw.KEY_C:("palette",)}
        if key in routes:
            self.dispatch(routes[key])
        elif key in (glfw.KEY_1,glfw.KEY_2,glfw.KEY_3):
            self.dispatch(("scene",SCENES[key-glfw.KEY_1]))
        elif key==glfw.KEY_ESCAPE:
            self.set_flying(False)
            self.hud.settings_open=self.hud.help_open=False
        elif key==glfw.KEY_SPACE:
            self.settings.motion=not self.settings.motion
            self.message("Motion resumed" if self.settings.motion else "Motion paused")
        elif key==glfw.KEY_HOME:
            self.set_flying(False)
            self.camera.reset(self.settings.scene)
            self.selected=""
        elif key==glfw.KEY_O:
            self.set_flying(False)
            self.camera.look_at(self.camera.focus)
            self.message("Orbiting "+(self.selected or "the scene center"))
        elif key==glfw.KEY_TAB:
            self.hud.visible=not self.hud.visible
        elif key==glfw.KEY_P:
            self.screenshot_pending=True
        elif key==glfw.KEY_F11:
            self.toggle_fullscreen()
        self.dirty=True

    def toggle_fullscreen(self):
        if not self.fullscreen:
            x,y=glfw.get_window_pos(self.window)
            w,h=glfw.get_window_size(self.window)
            self.window_rect=(x,y,w,h)
            monitor=glfw.get_primary_monitor()
            mode=glfw.get_video_mode(monitor)
            glfw.set_window_monitor(self.window,monitor,0,0,mode.size.width,mode.size.height,mode.refresh_rate)
        else:
            glfw.set_window_monitor(self.window,None,*self.window_rect,glfw.DONT_CARE)
        self.fullscreen=not self.fullscreen
        self.dirty=True

    def on_cursor(self,window,x,y):
        if self.camera.flying:
            if self.cursor is not None:
                self.camera.look(x-self.cursor[0],y-self.cursor[1])
            self.cursor=(x,y)
        elif self.hud.dragging is not None:
            _,_,scale=self.logical_size()
            action,rect=self.hud.dragging
            self.set_slider(action,rect,x/scale)

    def set_slider(self,action,rect,x):
        _,key,low,high=action
        value=low+max(0.0,min(1.0,(x-rect[0])/(rect[2]-rect[0])))*(high-low)
        setattr(self.settings,key,value)
        self.dirty=True

    def on_button(self,window,button,action,mods):
        if button!=glfw.MOUSE_BUTTON_LEFT:
            return
        if action==glfw.RELEASE:
            self.hud.dragging=None
            return
        if self.camera.flying:
            return
        x,y=glfw.get_cursor_pos(self.window)
        width,height,scale=self.logical_size()
        x,y=x/scale,y/scale
        hit=self.hud.action_at(x,y) if self.hud.visible else None
        if hit:
            command,rect=hit
            if command[0]=="slider":
                self.hud.dragging=(command,rect)
                self.set_slider(command,rect,x)
            else:
                self.dispatch(command)
        else:
            picked=self.renderer.pick(self.camera,(x,y),(width,height),self.time)
            if picked:
                self.selected,position=picked
                self.camera.focus=position.copy()
                self.set_flying(False)
                self.camera.look_at(position)
                self.message(self.selected+" selected. Press O to orbit or F to fly.")
            else:
                self.set_flying(True)

    def on_scroll(self,window,x,y):
        self.settings.speed=max(0.2,min(250.0,self.settings.speed*1.18**y))
        self.message(f"Flight speed {self.settings.speed:.1f}")

    def on_focus(self,window,focused):
        if not focused and self.camera.flying:
            self.set_flying(False)
        if not focused:
            self.hud.dragging=None

    def update(self,dt):
        if self.settings.motion:
            self.time+=dt
        if self.camera.flying:
            def down(key):
                return int(glfw.get_key(self.window,key)==glfw.PRESS)
            vector=(down(glfw.KEY_D)-down(glfw.KEY_A), down(glfw.KEY_E)-down(glfw.KEY_Q),
                    down(glfw.KEY_W)-down(glfw.KEY_S))
            speed=self.settings.speed
            if down(glfw.KEY_LEFT_SHIFT) or down(glfw.KEY_RIGHT_SHIFT):
                speed*=4
            if down(glfw.KEY_LEFT_CONTROL) or down(glfw.KEY_RIGHT_CONTROL):
                speed*=0.2
            self.camera.move(vector,dt,speed)
        elif self.settings.motion:
            self.camera.orbit(dt)

    def run(self):
        previous=time.monotonic()
        frames=0
        try:
            while not glfw.window_should_close(self.window):
                glfw.poll_events()
                now=time.monotonic()
                dt=min(now-previous,0.1)
                previous=now
                width,height=glfw.get_framebuffer_size(self.window)
                if not width or not height:
                    glfw.wait_events_timeout(0.1)
                    continue
                self.update(dt)
                self.fps=self.fps*0.92+(1/max(dt,1e-4))*0.08
                self.renderer.resize(width,height)
                uiw,uih,_=self.logical_size()
                if self.dirty or now-self.ui_tick>0.5 or self.hud.size!=(uiw,uih):
                    self.ui_image=self.hud.render(uiw,uih,self.settings,self.camera,
                        self.renderer.world.count,self.fps,self.notice if now<self.notice_until else "",self.selected)
                    self.dirty=False
                    self.ui_tick=now
                self.renderer.render(self.camera,self.settings,self.time,self.ui_image)
                self.ctx.copy_framebuffer(self.ctx.screen,self.renderer.output_fbo)
                glfw.swap_buffers(self.window)
                if self.screenshot_pending:
                    folder=data_dir()/"screenshots"
                    folder.mkdir(exist_ok=True)
                    filename=datetime.now().strftime("aster_%Y%m%d_%H%M%S_%f.png")
                    self.renderer.image().save(folder/filename)
                    self.screenshot_pending=False
                    self.message("Screenshot saved to "+str(folder))
                frames+=1
                if self.frame_limit and frames>=self.frame_limit:
                    break
        finally:
            self.close()

    def close(self,save=True):
        try:
            if save and self.started:
                save_settings(self.settings)
        finally:
            if self.renderer is not None:
                self.renderer.release()
                self.renderer=None
            if hasattr(self,"ctx"):
                self.ctx.release()
            if self.window:
                glfw.destroy_window(self.window)
                self.window=None
            glfw.terminate()
