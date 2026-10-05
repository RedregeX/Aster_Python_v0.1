"""ModernGL particle, planet, HDR bloom and UI rendering pipeline."""
from pathlib import Path
import math
import numpy as np
import moderngl
from PIL import Image
from .camera import perspective

SHADERS = Path(__file__).parent / "shaders"


class Renderer:
    def __init__(self, ctx, width, height):
        self.ctx = ctx
        self.width, self.height = 0, 0
        self.targets = []
        self.particles = []
        self.world = None
        self.ui_texture = None
        self.ui_revision = None
        self.points = self.program("particles.vert", "particles.frag")
        self.blur = self.program("fullscreen.vert", "blur.frag")
        self.composite = self.program("fullscreen.vert", "composite.frag")
        self.ui_program = self.program("fullscreen.vert", "ui.frag")
        self.planet = self.program("planet.vert", "planet.frag")
        self.lines = self.program("lines.vert", "lines.frag")
        self.blur_vao = ctx.vertex_array(self.blur, [])
        self.composite_vao = ctx.vertex_array(self.composite, [])
        self.ui_vao = ctx.vertex_array(self.ui_program, [])
        self.sphere_buffer, self.sphere_vao = self.make_sphere()
        self.orbit_buffer, self.orbit_vao = self.make_orbits()
        self.resize(width, height)

    def program(self, vertex, fragment):
        return self.ctx.program(vertex_shader=(SHADERS / vertex).read_text(),
                                fragment_shader=(SHADERS / fragment).read_text())

    def make_sphere(self):
        vertices = []
        lat, lon = 32, 64
        def at(a, b):
            theta, phi = a/lat*math.pi, b/lon*math.pi*2
            return (math.sin(theta)*math.cos(phi), math.cos(theta), math.sin(theta)*math.sin(phi))
        for i in range(lat):
            for j in range(lon):
                vertices.extend((at(i,j), at(i+1,j), at(i+1,j+1), at(i,j), at(i+1,j+1), at(i,j+1)))
        buf = self.ctx.buffer(np.array(vertices, dtype="f4").tobytes())
        return buf, self.ctx.vertex_array(self.planet, [(buf, "3f", "in_position")])

    def make_orbits(self):
        vertices = []
        for radius in (10, 17, 27, 33):
            for j in range(256):
                for step in (j, j+1):
                    t=step/256*math.pi*2
                    vertices.append([radius*math.cos(t), 0, radius*math.sin(t)])
        buf = self.ctx.buffer(np.array(vertices, dtype="f4").tobytes())
        return buf, self.ctx.vertex_array(self.lines, [(buf, "3f", "in_position")])

    def resize(self, width, height):
        width, height = max(1, width), max(1, height)
        if (width, height) == (self.width, self.height):
            return
        previous_targets = self.targets
        self.targets = []
        self.width, self.height = width, height
        def target(size, depth=False, dtype="f2"):
            texture = self.ctx.texture(size, 4, dtype=dtype)
            texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            texture.repeat_x = texture.repeat_y = False
            dep = self.ctx.depth_renderbuffer(size) if depth else None
            frame = self.ctx.framebuffer([texture], dep)
            self.targets.extend([texture] + ([dep] if dep else []) + [frame])
            return texture, frame
        self.scene_texture, self.scene_fbo = target((width, height), True)
        self.glow_a, self.glow_a_fbo = target((max(1,width//2), max(1,height//2)))
        self.glow_b, self.glow_b_fbo = target((max(1,width//2), max(1,height//2)))
        self.output_texture, self.output_fbo = target((width, height), dtype="f1")
        # ModernGL tracks the bound framebuffer in the context. Bind a live
        # replacement before deleting a previously active framebuffer.
        self.output_fbo.use()
        for resource in reversed(previous_targets):
            resource.release()

    def set_world(self, world):
        for _, buf, vao, _ in self.particles:
            vao.release()
            buf.release()
        self.particles = []
        self.world = world
        for data, kind in ((world.background,0), (world.stars,0), (world.clouds,1)):
            buf = self.ctx.buffer(data.tobytes())
            vao = self.ctx.vertex_array(self.points, [(buf, "3f 3f f f f", "in_position", "in_color",
                                                      "in_size", "in_power", "in_phase")])
            self.particles.append((kind, buf, vao, len(data)))

    def draw_system(self, camera, vp, time):
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.BLEND)
        self.planet["u_vp"].write(vp)
        self.planet["u_camera"].value = tuple(camera.position)
        bodies = ((10, 0.9, (0.75,0.28,0.14),0,0.5),
                  (17, 1.5, (0.25,0.65,1.0),1,2.0),
                  (27, 3.1, (0.85,0.67,0.43),0,4.0),
                  (33, 2.0, (0.28,0.70,0.85),0,5.0))
        for radius, size, color, kind, offset in bodies:
            angle=time*0.04*(17/radius)**1.5+offset
            self.planet["u_center"].value=(math.cos(angle)*radius,0,math.sin(angle)*radius)
            self.planet["u_radius"].value=size
            self.planet["u_color"].value=color
            self.planet["u_kind"].value=kind
            self.planet["u_rotation"].value=time*0.1
            self.sphere_vao.render(moderngl.TRIANGLES)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func=moderngl.SRC_ALPHA, moderngl.ONE
        self.lines["u_vp"].write(vp)
        self.orbit_vao.render(moderngl.LINES)

    def render(self, camera, settings, time, ui=None):
        ctx=self.ctx
        vp=camera.matrix_bytes(self.width/self.height)
        self.scene_fbo.use()
        ctx.viewport=(0,0,self.width,self.height)
        self.scene_fbo.clear(0.0007, 0.0012, 0.0030, 1, depth=1.0)
        ctx.disable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        ctx.enable(moderngl.BLEND | moderngl.PROGRAM_POINT_SIZE)
        ctx.blend_func=moderngl.SRC_ALPHA, moderngl.ONE
        self.points["u_vp"].write(vp)
        self.points["u_camera"].value=tuple(camera.position)
        self.points["u_height"].value=float(self.height)
        self.points["u_time"].value=time
        self.points["u_size"].value=settings.size
        # Render atmosphere first, then sharp stars. Particle density trims a
        # randomly distributed prefix of the pre-generated buffer.
        for index in (0,2,1):
            kind, _, vao, count = self.particles[index]
            self.points["u_cloud"].value=kind
            vao.render(moderngl.POINTS, vertices=max(1,int(count*settings.density)))
        if settings.scene=="system":
            self.draw_system(camera,vp,time)
        ctx.disable(moderngl.BLEND | moderngl.DEPTH_TEST)
        self.blur["u_image"].value=0
        self.blur["u_extract"].value=1
        self.scene_texture.use(0)
        self.glow_a_fbo.use()
        ctx.viewport=(0,0,*self.glow_a.size)
        self.blur["u_direction"].value=(2.5/self.width,0)
        self.blur_vao.render(moderngl.TRIANGLES,vertices=3)
        self.blur["u_extract"].value=0
        for _ in range(3):
            self.glow_b_fbo.use()
            self.glow_a.use(0)
            self.blur["u_direction"].value=(0,2.0/self.glow_a.size[1])
            self.blur_vao.render(moderngl.TRIANGLES,vertices=3)
            self.glow_a_fbo.use()
            self.glow_b.use(0)
            self.blur["u_direction"].value=(2.0/self.glow_a.size[0],0)
            self.blur_vao.render(moderngl.TRIANGLES,vertices=3)
        self.output_fbo.use()
        ctx.viewport=(0,0,self.width,self.height)
        self.scene_texture.use(0)
        self.glow_a.use(1)
        self.composite["u_scene"].value=0
        self.composite["u_glow"].value=1
        self.composite["u_bloom"].value=settings.bloom
        self.composite["u_exposure"].value=settings.exposure
        self.composite_vao.render(moderngl.TRIANGLES,vertices=3)
        if ui is not None:
            self.draw_ui(ui)

    def draw_ui(self, ui):
        if self.ui_texture is None or self.ui_texture.size != ui.size:
            if self.ui_texture is not None:
                self.ui_texture.release()
            self.ui_texture = self.ctx.texture(ui.size, 4)
            self.ui_texture.filter=(moderngl.LINEAR,moderngl.LINEAR)
            self.ui_revision=None
        if self.ui_revision is not ui:
            self.ui_texture.write(ui.tobytes())
            self.ui_revision=ui
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func=moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA
        self.ui_texture.use(0)
        self.ui_program["u_ui"].value=0
        self.ui_vao.render(moderngl.TRIANGLES,vertices=3)
        self.ctx.disable(moderngl.BLEND)

    def image(self):
        return Image.frombytes("RGB",(self.width,self.height),self.output_fbo.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    def pick(self, camera, logical_position, logical_size, time=0.0):
        """Select named landmarks projected near the click, not invisible objects."""
        vp=perspective(self.width/self.height)@camera.view()
        candidates=[]
        for name, position in self.world.landmarks:
            point=vp@np.append(position,1)
            if point[3]<=0:
                continue
            p=point[:3]/point[3]
            if not -1 <= p[2] <= 1:
                continue
            screen=np.array([(p[0]+1)*logical_size[0]/2,(1-p[1])*logical_size[1]/2])
            distance=np.linalg.norm(screen-np.array(logical_position))
            if distance<50:
                candidates.append((distance,name,position))
        return min(candidates,key=lambda item:item[0])[1:] if candidates else None

    def release(self):
        for _, buf, vao, _ in self.particles:
            vao.release(); buf.release()
        if self.ui_texture:
            self.ui_texture.release()
        for item in reversed(self.targets):
            item.release()
        for item in (self.sphere_vao,self.sphere_buffer,self.orbit_vao,self.orbit_buffer,
                     self.blur_vao,self.composite_vao,self.ui_vao,self.points,self.blur,
                     self.composite,self.ui_program,self.planet,self.lines):
            item.release()
