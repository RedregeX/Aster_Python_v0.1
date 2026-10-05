import json
import numpy as np
import pytest
from aster.camera import Camera, perspective
from aster.config import Settings, load_settings, save_settings
from aster.world import make_world


@pytest.mark.parametrize("scene",("galaxy","nebula","system"))
def test_generation_reproducible_and_finite(scene):
    a=make_world(scene,123,"low")
    b=make_world(scene,123,"low")
    c=make_world(scene,124,"low")
    assert np.array_equal(a.stars,b.stars)
    assert not np.array_equal(a.stars,c.stars)
    for data in (a.stars,a.clouds,a.background):
        assert data.dtype==np.float32 and data.shape[1]==9
        assert np.isfinite(data).all()
        assert (data[:,6]>0).all() and (data[:,7]>=0).all()


def test_quality_and_palette():
    low=make_world("nebula",42,"low")
    high=make_world("nebula",42,"high")
    tinted=make_world("nebula",42,"low",1)
    assert high.count>low.count*2
    assert np.array_equal(low.clouds[:,:3],tinted.clouds[:,:3])
    assert not np.array_equal(low.clouds[:,3:6],tinted.clouds[:,3:6])


@pytest.mark.parametrize("scene",("galaxy","nebula","system"))
def test_camera_centers_scene_and_moves_consistently(scene):
    camera=Camera()
    camera.reset(scene)
    origin=(perspective(1.6)@camera.view())@np.array([0,0,0,1])
    assert np.allclose(origin[:2]/origin[3],0,atol=1e-6)
    initial=camera.position.copy()
    camera.move((1,0,1),0.1,10)
    assert np.isclose(np.linalg.norm(camera.position-initial),1,atol=1e-5)
    camera.look(100000,100000)
    assert np.isfinite(camera.view()).all()
    assert abs(camera.pitch)<=1.54


def test_settings_roundtrip_and_corruption(tmp_path):
    path=tmp_path/"prefs.json"
    original=Settings(scene="nebula",seed=953,speed=60,palette=2)
    save_settings(original,path)
    assert load_settings(path)==original
    path.write_text("bad json")
    assert load_settings(path)==Settings()
    path.write_text(json.dumps({"scene":"oops","quality":"oops","seed":-50,"exposure":99,"density":-1}))
    loaded=load_settings(path)
    assert loaded.scene=="galaxy" and loaded.quality=="high"
    assert loaded.seed==0 and loaded.exposure==1.1 and loaded.density==1
    path.write_text(json.dumps({"seed":None}))
    assert load_settings(path)==Settings()
