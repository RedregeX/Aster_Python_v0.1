"""Texture-based desktop HUD, with matching mouse hit regions.

Pillow only redraws the HUD on state changes or a slow statistics tick; it
never draws particles. Logical coordinates keep controls consistent on HiDPI.
"""
from pathlib import Path
from functools import lru_cache
import os
from PIL import Image, ImageDraw, ImageFont

WHITE=(234,242,248,255)
MUTED=(125,151,172,255)
ACCENT=(135,224,230,255)
BORDER=(98,135,158,75)
SCENE_INFO={
    "galaxy": ("01", "The quiet spiral", "A galaxy made of starlight.", "Four arms. One luminous heart."),
    "nebula": ("02", "Between the stars", "Drift through a stellar nursery.", "Cold blue dust meets warm gas."),
    "system": ("03", "A little solar system", "Four worlds around Helios.", "Beyond them, a belt of dust."),
}
SLIDERS=(("exposure","EXPOSURE",0.3,2.5), ("bloom","BLOOM",0,1.5),
         ("size","PARTICLE SIZE",0.4,2), ("density","DENSITY",0.15,1))


@lru_cache(maxsize=48)
def font(size, mono=False):
    windir=Path(os.environ.get("WINDIR","C:/Windows"))
    name="DejaVuSansMono.ttf" if mono else "DejaVuSans.ttf"
    candidates=[windir/"Fonts"/("consola.ttf" if mono else "segoeui.ttf"),
                Path("/usr/share/fonts/truetype/dejavu")/name,
                Path("/System/Library/Fonts")/("Menlo.ttc" if mono else "Helvetica.ttc")]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate),size)
    return ImageFont.load_default(size=size)


class HUD:
    def __init__(self):
        self.settings_open=False
        self.help_open=False
        self.visible=True
        self.regions=[]
        self.size=(1280,800)
        self.dragging=None

    def action_at(self,x,y):
        for rect, action in reversed(self.regions):
            if rect[0]<=x<=rect[2] and rect[1]<=y<=rect[3]:
                return action, rect
        return None

    def render(self, width, height, settings, camera, count, fps=0, notice="", selected="", gpu=""):
        self.size=(width,height)
        self.regions=[]
        img=Image.new("RGBA",self.size,(0,0,0,0))
        if not self.visible:
            return img
        d=ImageDraw.Draw(img)
        def text(x,y,value,size=12,color=WHITE,mono=False):
            d.text((x,y),value,font=font(size,mono),fill=color)
        def panel(rect):
            d.rounded_rectangle(rect,10,fill=(8,16,26,231),outline=BORDER,width=1)
        def button(rect,label,action,active=False):
            d.rounded_rectangle(rect,6,fill=(26,53,65,225) if active else (10,21,31,210),
                                outline=ACCENT if active else BORDER,width=1)
            bounds=d.textbbox((0,0),label,font=font(12))
            text((rect[0]+rect[2]-(bounds[2]-bounds[0]))/2,rect[1]+10,label,12,ACCENT if active else WHITE)
            self.regions.append((rect,action))
        # Low-opacity edge scrims leave the scene center unobstructed.
        for x in range(300):
            a=int(140*(1-x/300)**2)
            d.line((x,0,x,height),fill=(3,10,19,a))
        for y in range(100):
            d.line((0,height-1-y,width,height-1-y),fill=(3,10,19,int(185*(1-y/100)**1.4)))
        text(30,26,"A S T E R",24)
        text(32,62,"A SMALL UNIVERSE",10,MUTED,True)
        d.line((30,93,width-30,93),fill=BORDER)
        text(width-253,32,"FIELD ATLAS  /  V0.1",11,MUTED,True)
        d.ellipse((width-42,34,width-36,40),fill=ACCENT)
        number,title,line1,line2=SCENE_INFO[settings.scene]
        text(32,133,"OBSERVATION  /  "+number,11,ACCENT,True)
        # Keep a narrow editorial column, clear of the central object.
        titles={"galaxy":("The quiet","spiral."),"nebula":("Between","the stars."),"system":("A little","solar system.")}
        for i,part in enumerate(titles[settings.scene]):
            text(30,159+i*42,part,32)
        text(32,263,line1,12,MUTED)
        text(32,283,line2,12,MUTED)
        d.line((32,321,220,321),fill=BORDER)
        text(32,342,f"{int(count*settings.density):,}",23)
        text(33,374,"ACTIVE PARTICLES",10,MUTED,True)
        text(32,410,"SEED",10,MUTED,True)
        text(100,407,f"{settings.seed:08d}",13,WHITE,True)
        text(32,440,"MODE",10,MUTED,True)
        text(100,437,"FREE FLIGHT" if camera.flying else "SLOW ORBIT",12,ACCENT,True)
        button((32,482,222,521),"Explore  /  F",("fly",))
        button((32,531,122,566),"Settings",("settings",),self.settings_open)
        button((132,531,222,566),"Help  /  H",("help",),self.help_open)
        if selected:
            text(32,589,"FOCUS  /  "+selected,10,ACCENT,True)
        # Bottom scene selector and small live instrumentation.
        bottom=height-72
        for i,(key,label) in enumerate((("galaxy","01  Galaxy"),("nebula","02  Nebula"),("system","03  System"))):
            left=32+i*128
            button((left,bottom,left+116,bottom+37),label,("scene",key),settings.scene==key)
        text(32,height-25,"WASD move  /  mouse look  /  Esc release",10,MUTED,True)
        text(width-282,bottom+4,f"{fps:5.1f} FPS   /   {settings.quality.upper()}",11,WHITE,True)
        text(width-282,bottom+27,f"FLIGHT SPEED  {settings.speed:.1f}",10,MUTED,True)
        text(width-282,height-25,"TAB clean view  /  P capture",10,MUTED,True)
        if notice:
            bounds=d.textbbox((0,0),notice,font=font(12))
            x=(width-(bounds[2]-bounds[0]))/2
            panel((x-18,107,x+bounds[2]-bounds[0]+18,142))
            text(x,116,notice,12,ACCENT)
        if self.settings_open:
            x=width-309
            panel((x,115,width-30,562))
            self.regions.append(((x,115,width-30,562),("consume",)))
            text(x+20,134,"RENDER SETTINGS",12,ACCENT,True)
            text(x+20,163,"Shape your corner of space.",12,MUTED)
            for i,(key,label,lo,hi) in enumerate(SLIDERS):
                y=207+i*56
                value=getattr(settings,key)
                text(x+20,y,label,10,MUTED,True)
                text(x+216,y,f"{value:.2f}",10,WHITE,True)
                a,b=x+22,width-53
                d.line((a,y+28,b,y+28),fill=(68,87,101,255),width=3)
                px=a+(b-a)*(value-lo)/(hi-lo)
                d.line((a,y+28,px,y+28),fill=ACCENT,width=3)
                d.ellipse((px-5,y+23,px+5,y+33),fill=WHITE)
                self.regions.append(((a,y+16,b,y+41),("slider",key,lo,hi)))
            for i,q in enumerate(("low","medium","high","ultra")):
                a=x+20+i*60
                button((a,443,a+54,477),q.title(),("quality",q),settings.quality==q)
            button((x+20,488,x+130,522),"New seed  /  R",("seed",))
            button((x+140,488,width-50,522),"Palette  /  C",("palette",))
            text(x+20,535,"Saved automatically when you exit.",10,MUTED)
        if self.help_open:
            cx=width//2
            panel((cx-250,145,cx+250,580))
            self.regions.append(((cx-250,145,cx+250,580),("consume",)))
            text(cx-225,166,"YOUR WAY THROUGH SPACE",13,ACCENT,True)
            lines=("F / click scene      Capture mouse and fly", "Esc                  Release mouse / close panel",
                   "W A S D              Forward / left / back / right", "Q / E                Down / up",
                   "Shift / Ctrl         Faster / slower", "Mouse wheel          Change flight speed",
                   "Home                 Return to opening view", "1 / 2 / 3            Switch scene",
                   "Space                Pause motion", "R / C                New seed / color palette",
                   "P / Tab              Screenshot / hide interface", "F11                  Fullscreen",
                   "Left-click core      Select a named landmark", "O                    Orbit the selected landmark")
            for i,line in enumerate(lines):
                text(cx-225,209+i*23,line,11,MUTED,True)
            button((cx-70,540,cx+70,575),"Back to space",("help",))
        if camera.flying:
            cx,cy=width//2,height//2
            d.line((cx-7,cy,cx-3,cy),fill=(200,240,245,100))
            d.line((cx+3,cy,cx+7,cy),fill=(200,240,245,100))
            d.line((cx,cy-7,cx,cy-3),fill=(200,240,245,100))
            d.line((cx,cy+3,cx,cy+7),fill=(200,240,245,100))
        return img
