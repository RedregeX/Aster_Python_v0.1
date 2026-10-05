import sys
import numpy as np
import pytest
import moderngl
from aster.camera import Camera
from aster.config import Settings
from aster.renderer import Renderer
from aster.world import make_world


@pytest.fixture
def renderer():
    try:
        ctx=moderngl.create_standalone_context(require=330,**({"backend":"egl"} if sys.platform.startswith("linux") else {}))
    except Exception as exc:
        pytest.skip(f"No offscreen OpenGL context: {exc}")
    render=Renderer(ctx,640,400)
    yield render
    render.release()
    ctx.release()


@pytest.mark.parametrize("scene",("galaxy","nebula","system"))
def test_real_gpu_scene_renders_and_resizes(renderer,scene):
    settings=Settings(scene=scene,quality="low")
    renderer.set_world(make_world(scene,42,"low"))
    camera=Camera()
    camera.reset(scene)
    renderer.render(camera,settings,0)
    pixels=np.array(renderer.image())
    assert pixels.shape==(400,640,3)
    assert pixels.std()>6
    assert (pixels.max(axis=2)>80).sum()>500
    renderer.resize(480,320)
    renderer.render(camera,settings,5)
    assert renderer.image().size==(480,320)
    assert renderer.ctx.error=="GL_NO_ERROR"


def test_bloom_and_density_change_actual_pixels(renderer):
    settings=Settings(scene="nebula",quality="low",bloom=0)
    renderer.set_world(make_world("nebula",42,"low"))
    camera=Camera()
    camera.reset("nebula")
    renderer.render(camera,settings,0)
    baseline=np.array(renderer.image(),dtype=float)
    settings.bloom=1.5
    renderer.render(camera,settings,0)
    glowy=np.array(renderer.image(),dtype=float)
    assert glowy.mean()>baseline.mean()
    settings.density=0.15
    renderer.render(camera,settings,0)
    sparse=np.array(renderer.image(),dtype=float)
    assert sparse.mean()<glowy.mean()


def test_landmark_selection(renderer):
    renderer.set_world(make_world("galaxy",42,"low"))
    camera=Camera()
    assert renderer.pick(camera,(640,400),(1280,800))[0]=="GALACTIC CORE"
    assert renderer.pick(camera,(10,10),(1280,800)) is None


def test_scene_replacement_releases_previous_buffers(renderer):
    for scene in ("galaxy","system","nebula","galaxy"):
        renderer.set_world(make_world(scene,42,"low"))
        camera=Camera()
        camera.reset(scene)
        renderer.render(camera,Settings(scene=scene),0)
        assert renderer.ctx.error=="GL_NO_ERROR"


def test_consecutive_frames_keep_the_same_viewport(renderer):
    settings=Settings(scene="nebula",quality="low")
    renderer.set_world(make_world("nebula",42,"low"))
    camera=Camera()
    camera.reset("nebula")
    renderer.render(camera,settings,0)
    first=np.array(renderer.image())
    renderer.render(camera,settings,0)
    second=np.array(renderer.image())
    assert np.array_equal(first,second)
    assert renderer.ctx.error=="GL_NO_ERROR"
