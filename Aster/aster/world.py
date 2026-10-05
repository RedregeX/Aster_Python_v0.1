"""Vectorized, reproducible particle distributions, uploaded once per scene.

Packed particles: position.xyz, color.rgb, world size, intensity, random phase.
The GPU handles individual point movement and all pixel shading.
"""
from dataclasses import dataclass
import numpy as np
from .config import QUALITY

PALETTES = (
    ((0.12, 0.42, 1.0), (0.8, 0.12, 0.45), (1.0, 0.65, 0.25)),
    ((0.08, 0.72, 0.70), (0.20, 0.40, 1.0), (0.95, 0.85, 0.45)),
    ((0.48, 0.22, 1.0), (1.0, 0.24, 0.30), (1.0, 0.70, 0.48)),
)


@dataclass
class World:
    stars: np.ndarray
    clouds: np.ndarray
    background: np.ndarray
    landmarks: list

    @property
    def count(self):
        return len(self.stars) + len(self.clouds) + len(self.background)


def pack(rng, pos, color, size, intensity):
    n = len(pos)
    result = np.empty((n, 9), dtype="f4")
    result[:, :3] = pos
    result[:, 3:6] = color
    result[:, 6] = size
    result[:, 7] = intensity
    result[:, 8] = rng.uniform(0, 1, n)
    return result


def background(rng, n):
    directions = rng.normal(size=(n, 3))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    pos = directions * rng.uniform(600, 1100, n)[:, None]
    colors = np.tile([0.70, 0.80, 1.0], (n, 1))
    warm = rng.random(n) < 0.18
    colors[warm] = [1.0, 0.76, 0.49]
    return pack(rng, pos, colors, rng.uniform(0.45, 1.4, n), rng.uniform(0.15, 1.0, n))


def galaxy_points(rng, n, clouds=False, palette=0):
    radius = np.clip(rng.gamma(2.1, 9.0, n), 0.1, 55.0)
    branch = rng.integers(0, 4, n)
    angle = branch * np.pi/2 + radius*0.105 + rng.normal(0, 0.14 if clouds else 0.22, n)
    scatter = (0.35 + radius*0.035) if clouds else (0.25 + radius*0.04)
    pos = np.column_stack((np.cos(angle)*radius + rng.normal(0, scatter),
                           rng.normal(0, 0.6 + np.exp(-radius/7)*2.0, n),
                           np.sin(angle)*radius + rng.normal(0, scatter)))
    inner = np.exp(-radius/15)[:, None]
    cool, pink, warm = map(np.array, PALETTES[palette])
    if clouds:
        colors = cool*(1-inner) + warm*inner
        colors += pink[None, :] * rng.uniform(0.0, 0.3, n)[:, None]
        size = rng.uniform(2.0, 5.5, n)
        power = rng.uniform(0.008, 0.035, n)
    else:
        colors = (np.array([0.46, 0.68, 1.0])*(1-inner) + np.array([1, 0.83, 0.59])*inner)
        colors += rng.uniform(0, 0.15, (n, 1))
        size = rng.uniform(0.055, 0.13, n)
        power = rng.uniform(0.15, 0.85, n)
        # More luminous foreground stars interrupt the fine star dust.
        bright = rng.random(n) < 0.006
        size[bright] *= 3.0
        power[bright] *= 4.0
        if n > 1:
            pos[0] = 0
            colors[0] = [1, 0.9, 0.65]
            size[0], power[0] = 1.8, 8.0
    return pack(rng, pos, colors, size, power)


def nebula_points(rng, n, clouds=False, palette=0):
    t = rng.uniform(-np.pi, np.pi, n)
    strand = rng.integers(0, 3, n)
    radius = 17 + 4*np.sin(t*3 + strand*1.8)
    width = 1.8 + 2.1*(np.sin(t*2+strand)**2)
    pos = np.column_stack((np.cos(t)*radius*1.6,
                           np.sin(t*2+strand)*5.0,
                           np.sin(t)*radius*0.65))
    pos += rng.normal(size=(n, 3)) * width[:, None]
    # Tangled arcs, long filaments and a cavity around the central stars.
    pos[:, 1] += 3*np.sin(pos[:, 0]*0.24)
    cool, pink, warm = map(np.array, PALETTES[palette])
    mix = (np.sin(t+0.8)*0.5+0.5)[:, None]
    colors = cool*(1-mix) + pink*mix
    hot = np.exp(-np.linalg.norm(pos-[15, 0, 2], axis=1)/10)[:, None]
    colors = colors*(1-hot*0.8) + warm*hot*0.8
    if clouds:
        return pack(rng, pos, colors, rng.uniform(3.0, 7.0, n), rng.uniform(0.012, 0.045, n))
    points = pack(rng, pos, colors*0.8 + 0.2, rng.uniform(0.035, 0.11, n), rng.uniform(0.08, 0.5, n))
    # Embedded blue-white stars.
    for index, xyz in enumerate(([0, 0, 0], [15, 0, 2], [-18, 3, -2], [6, -2, 10])):
        if index < n:
            points[index, :3] = xyz
            points[index, 3:6] = [0.60, 0.82, 1.0]
            points[index, 6:8] = [0.9, 9]
    return points


def make_world(scene="galaxy", seed=42, quality="high", palette=0):
    rng = np.random.default_rng(seed)
    factor = QUALITY[quality]
    sky = background(rng, int(9000*factor))
    if scene == "galaxy":
        stars = galaxy_points(rng, int(170000*factor), palette=palette)
        clouds = galaxy_points(rng, int(9500*factor), True, palette)
        landmarks = [("GALACTIC CORE", np.array([0, 0, 0], dtype="f4")),
                     ("OUTER ARM", np.array([32, 0, -12], dtype="f4"))]
    elif scene == "nebula":
        stars = nebula_points(rng, int(110000*factor), palette=palette)
        clouds = nebula_points(rng, int(11000*factor), True, palette)
        landmarks = [("STELLAR NURSERY", np.array([0, 0, 0], dtype="f4")),
                     ("AMBER KNOT", np.array([15, 0, 2], dtype="f4"))]
    elif scene == "system":
        radius = rng.uniform(37, 46, int(24000*factor))
        t = rng.uniform(0, np.pi*2, len(radius))
        pos = np.column_stack((np.cos(t)*radius, rng.normal(0, 0.22, len(t)), np.sin(t)*radius))
        stars = pack(rng, pos, [0.52, 0.58, 0.66], rng.uniform(0.04, 0.11, len(t)), 0.24)
        stars = np.vstack((pack(rng, [[0, 0, 0]], [1, 0.63, 0.22], 8.0, 9.0), stars))
        clouds = pack(rng, rng.normal(0, 1.9, (400, 3)), [1, 0.30, 0.07], 6.0, 0.04)
        landmarks = [("HELIOS", np.array([0, 0, 0], dtype="f4"))]
    else:
        raise ValueError(f"Unknown scene: {scene}")
    return World(stars, clouds, sky, landmarks)
