from unittest.mock import Mock
import glfw
import numpy as np
from aster.app import Application
from aster.camera import Camera
from aster.config import Settings
from aster.ui import HUD


def shell_app(monkeypatch):
    # Exercise the real control code without requiring an OS desktop session.
    app=Application.__new__(Application)
    app.window=object()
    app.settings=Settings()
    app.camera=Camera()
    app.hud=HUD()
    app.cursor=None
    app.selected=""
    app.time=0
    app.dirty=False
    app.rebuild=Mock()
    app.renderer=Mock()
    app.screenshot_pending=False
    monkeypatch.setattr(glfw,"set_input_mode",lambda *args:None)
    monkeypatch.setattr(glfw,"get_window_size",lambda *args:(1280,800))
    return app


def test_control_routes_and_focus_loss(monkeypatch):
    app=shell_app(monkeypatch)
    app.on_key(None,glfw.KEY_F,0,glfw.PRESS,0)
    assert app.camera.flying
    app.on_cursor(None,100,100)
    initial=app.camera.forward.copy()
    app.on_cursor(None,160,120)
    assert not np.allclose(initial,app.camera.forward)
    app.on_focus(None,False)
    assert not app.camera.flying
    app.on_key(None,glfw.KEY_2,0,glfw.PRESS,0)
    assert app.settings.scene=="nebula"
    app.rebuild.assert_called_with(reset_camera=True)
    app.on_key(None,glfw.KEY_SPACE,0,glfw.PRESS,0)
    assert not app.settings.motion
    app.on_key(None,glfw.KEY_P,0,glfw.PRESS,0)
    assert app.screenshot_pending


def test_movement_and_scroll_bounds(monkeypatch):
    app=shell_app(monkeypatch)
    app.set_flying(True)
    monkeypatch.setattr(glfw,"get_key",lambda window,key:glfw.PRESS if key==glfw.KEY_W else glfw.RELEASE)
    start=app.camera.position.copy()
    app.update(0.1)
    assert np.linalg.norm(app.camera.position-start)>1
    app.on_scroll(None,0,100)
    assert app.settings.speed==250
    app.on_scroll(None,0,-100)
    assert app.settings.speed==0.2


def test_hud_panels_and_slider_hit_regions(monkeypatch):
    app=shell_app(monkeypatch)
    app.hud.settings_open=True
    image=app.hud.render(1280,800,app.settings,app.camera,188500)
    assert image.size==(1280,800)
    action,rect=app.hud.action_at(1020,235)
    assert action[:2]==("slider","exposure")
    app.set_slider(action,rect,rect[2])
    assert app.settings.exposure==2.5
    app.set_slider(action,rect,rect[0]-100)
    assert app.settings.exposure==0.3
    assert app.hud.action_at(1000,180)[0]==("consume",)
    app.hud.settings_open=False
    app.hud.help_open=True
    app.hud.render(1280,800,app.settings,app.camera,188500)
    assert app.hud.action_at(600,300)[0]==("consume",)
    assert app.hud.action_at(620,550)[0]==("help",)
    app.hud.visible=False
    assert app.hud.render(1280,800,app.settings,app.camera,0).getbbox() is None
    assert app.hud.regions==[]
