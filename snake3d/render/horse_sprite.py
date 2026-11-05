import math
from dataclasses import dataclass

from PIL import Image

COAT = (0x1D, 0x1B, 0x26)
FAR = (0x0C, 0x0B, 0x12)
RIM_TOP = (0xF0, 0x7A, 0x8C)
RIM_SIDE = (0x8A, 0x4A, 0x6E)
SOCK = (0xD9, 0xD4, 0xCC)
SOCK_FAR = (0x9A, 0x94, 0x8C)
FEATHER = (0xC4, 0xBC, 0xB0)

SPRITE_SIZE = (72, 56)
SPRITE_ANCHOR = (36, 48)  # hoof line, pasted onto scene.GROUND
LEG_SEGMENT = 6


@dataclass(frozen=True)
class Gait:
    frames: int
    stride_px: int
    offsets: dict[str, float]
    stance: float
    bob: float = 0.0
    bob_freq: int = 1  # bobs per stride: gallop 1, trot/walk 2 (one per diagonal/pair)
    nod: float = 0.0
    bend: tuple[float, float] = (0.0, 0.0)  # swing knee fold, (front, hind)


GAITS = {
    "graze": Gait(64, 0, {"hl": 0.0, "hr": 0.0, "fl": 0.0, "fr": 0.0}, 1.0),
    "walk": Gait(20, 20, {"hl": 0.0, "fl": 0.25, "hr": 0.5, "fr": 0.75}, 0.62, 0.4, 2, 0.8, (0.9, 0.7)),
    "trot": Gait(20, 32, {"hl": 0.0, "fr": 0.0, "hr": 0.5, "fl": 0.5}, 0.45, 1.0, 2, 0.6, (1.3, 1.0)),
    "gallop": Gait(16, 40, {"hl": 0.0, "hr": 0.10, "fl": 0.32, "fr": 0.42}, 0.38, 1.4, 1, 1.6, (1.5, 1.1)),
}


def _ease(s: float) -> float:
    return s * s * (3 - 2 * s)


class _Pen:
    """Rasterizes round-capped shapes in horse units (scaled by S) into a pixel dict."""

    def __init__(self, scale: float, origin: tuple[float, float]):
        self.s, (self.ox, self.oy) = scale, origin
        self.px: dict[tuple[int, int], tuple[int, int, int]] = {}
        self.color = COAT

    def blob(self, x: float, y: float, r: float) -> None:
        cx, cy, rr = self.ox + x * self.s, self.oy + y * self.s, r * self.s
        n = math.ceil(rr)
        for dy in range(-n, n + 1):
            for dx in range(-n, n + 1):
                if dx * dx + dy * dy <= rr * rr + 0.3:
                    self.px[(round(cx) + dx, round(cy) + dy)] = self.color

    def limb(self, x1: float, y1: float, x2: float, y2: float, r1: float, r2: float) -> None:
        n = max(2, math.ceil(math.hypot(x2 - x1, y2 - y1) * 3))
        for i in range(n + 1):
            t = i / n
            self.blob(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, r1 + (r2 - r1) * t)


def body_scale(level: int) -> float:
    return 1.5 if level >= 2 else 1.1


def stance_sweep(gait: Gait, s: float) -> float:
    # dev-note: sweep sized so the stance hoof moves exactly at ground speed (no skating):
    # hoof travel 2*L*S*sin(sweep) == stance * stride_px
    if not gait.stride_px:
        return 0.0
    return math.asin(min(0.95, gait.stance * gait.stride_px / (4 * LEG_SEGMENT * s)))


def ground_units(gait: Gait, s: float) -> float:
    """Hoof line below the body centre, low enough that a stance hoof is reachable at any bob."""
    return 2 + 2 * LEG_SEGMENT * math.cos(stance_sweep(gait, s)) - gait.bob


def body_bob(gait: Gait, phase: float) -> float:
    return -gait.bob * math.sin(gait.bob_freq * 2 * math.pi * phase - 0.55 * 2 * math.pi)


def _reach(hx, hy, tx, ty, front):
    """Two-segment IK: thigh/shin angles putting the hoof at (tx, ty). Knee folds back on fore legs, forward on hind."""
    dx, dy = tx - hx, ty - hy
    d = math.hypot(dx, dy)
    theta = math.atan2(dx, dy)
    alpha = math.acos(min(1.0, d / (2 * LEG_SEGMENT)))
    return (theta - alpha, theta + alpha) if front else (theta + alpha, theta - alpha)


def leg_points(hx, hy, p, front, gait, sweep, ground):
    """Knee and hoof positions for one leg at gait phase p; hooves never go below the ground line."""
    if gait.stride_px == 0:
        a, b = (0.06, 0.06) if front else (-0.08, -0.02)
    elif p < gait.stance:
        reach = sweep - (p / gait.stance) * 2 * sweep
        a, b = _reach(hx, hy, hx + 2 * LEG_SEGMENT * math.sin(reach), ground, front)
    else:
        s = (p - gait.stance) / (1 - gait.stance)
        a = -sweep + _ease(s) * 2 * sweep
        bend = math.sin(math.pi * s) * gait.bend[0 if front else 1]
        b = a - bend if front else a + bend * 0.2 - 0.9 * math.sin(math.pi * s)
    kx, ky = hx + math.sin(a) * LEG_SEGMENT, hy + math.cos(a) * LEG_SEGMENT
    fx, fy = kx + math.sin(b) * LEG_SEGMENT, ky + math.cos(b) * LEG_SEGMENT
    if fy > ground:  # swing hoof brushing the grass at lift-off/touch-down: keep it on top
        a, b = _reach(hx, hy, fx, ground, front)
        kx, ky = hx + math.sin(a) * LEG_SEGMENT, hy + math.cos(a) * LEG_SEGMENT
        fx, fy = kx + math.sin(b) * LEG_SEGMENT, ky + math.cos(b) * LEG_SEGMENT
    return (kx, ky), (fx, fy)


def _leg(pen, hx, hy, p, front, gait, sweep, ground, level, far):
    (kx, ky), (fx, fy) = leg_points(hx, hy, p, front, gait, sweep, ground)
    pen.limb(hx, hy, kx, ky, 1.6 if front else 2.2, 1.0)
    pen.limb(kx, ky, fx, fy, 0.9, 0.8)
    if level >= 3:
        coat = pen.color
        pen.color = SOCK_FAR if far else SOCK
        pen.limb(kx + (fx - kx) * 0.6, ky + (fy - ky) * 0.6, fx, fy, 0.8, 0.8)
        if level >= 4:
            pen.color = FEATHER
            pen.blob(fx - 0.5, fy, 1.0)
        pen.color = coat


def draw_horse(frame: int, gait: str, level: int) -> Image.Image:
    g = GAITS[gait]
    phase = (frame % g.frames) / g.frames
    wave = 2 * math.pi * phase  # every secondary motion completes whole cycles per stride, so the sprite loops
    s = body_scale(level)
    sweep, ground = stance_sweep(g, s), ground_units(g, s)
    pen = _Pen(s, (SPRITE_ANCHOR[0] - 2, SPRITE_ANCHOR[1] - ground * s))

    cy = body_bob(g, phase)
    nod = g.nod * math.sin(g.bob_freq * wave + 0.15 * 2 * math.pi)
    grazing = g.stride_px == 0

    pen.color = FAR
    _leg(pen, -7, cy + 2, (phase + g.offsets["hl"]) % 1, False, g, sweep, ground, level, True)
    _leg(pen, 7, cy + 2, (phase + g.offsets["fl"]) % 1, True, g, sweep, ground, level, True)

    pen.color = COAT
    segments = 4 if level == 1 else 9
    swish = 1.6 * math.sin(2 * wave) if grazing else 0.0
    for i in range(segments):
        k = i / 8
        sway = math.sin(wave - i * 0.7) * i * (0.12 if grazing else 0.25) + swish * k
        drop = 0.7 if not grazing else 1.3
        pen.blob(-11 - i * 1.1 * (0.6 if grazing else 1), cy - 2 + i * drop + sway, max(0.6, 1.6 - i * 0.12))

    pen.blob(-7, cy - 1, 4.2)
    pen.blob(7, cy - 0.5, 4.2)
    for x in range(-7, 8):
        pen.blob(x, cy, 3.9)

    if grazing:
        nibble = 0.6 * max(0.0, math.sin(4 * wave))
        nx, ny = 14.0, cy + 3 + nibble
        pen.limb(8, cy - 2, nx, ny, 3.2, 2.0)
        pen.limb(nx, ny, nx + 2.5, ny + 6, 1.9, 1.2)       # head hanging to the grass
        pen.blob(nx + 1.0, ny + 2, 1.6)
        ear_flick = 0.8 if 40 <= frame % g.frames < 44 else 0.0
        pen.blob(nx - 1.2, ny - 1.6 - ear_flick, 0.6)
        star_at = (nx + 1.6, ny + 2.6)
    else:
        nx, ny = 13.0, cy - 9 + nod * 0.5
        pen.limb(8, cy - 2, nx, ny, 3.2, 2.0)
        pen.blob(nx + 1.2, ny + 1.0, 1.8)                    # jaw
        pen.limb(nx, ny - 0.8, nx + 5.5, ny + 3.2 + nod * 0.4, 1.9, 1.2)  # skull tapering to muzzle
        pen.blob(nx, ny - 3.6, 0.6)
        pen.blob(nx - 0.8, ny - 3.0, 0.5)
        star_at = (nx + 1.4, ny - 1.4)

    mane = 3 if level == 1 else 6
    for i in range(mane):
        flutter = math.sin(wave * (1 if not grazing else 2) - i * 0.9) * (0.8 if not grazing else 0.3)
        braid = (0.5 if i % 2 else -0.3) if level >= 4 else 0.0
        if grazing:
            pen.blob(nx - 1.5 - i * 0.9, ny - 1 - i * 0.5 + flutter + braid, 0.9)
        else:
            pen.blob(nx - 2 - i * 0.9, ny - 1 + i * 1.2 + flutter + braid, 0.9 if level < 4 else 1.0)

    _leg(pen, -7, cy + 2, (phase + g.offsets["hr"]) % 1, False, g, sweep, ground, level, False)
    _leg(pen, 7, cy + 2, (phase + g.offsets["fr"]) % 1, True, g, sweep, ground, level, False)

    px = pen.px
    if level >= 3:
        lit = {}
        for (x, y), col in px.items():
            if col not in (COAT, FAR):
                continue
            if (x, y - 1) not in px:
                lit[(x, y)] = RIM_TOP
            elif (x + 1, y - 1) not in px or (x + 1, y) not in px:
                lit[(x, y)] = RIM_SIDE
        px.update(lit)
        sx, sy = round(pen.ox + star_at[0] * s), round(pen.oy + star_at[1] * s)
        px[(sx, sy)] = SOCK

    img = Image.new("RGBA", SPRITE_SIZE, (0, 0, 0, 0))
    for (x, y), col in px.items():
        if 0 <= x < SPRITE_SIZE[0] and 0 <= y < SPRITE_SIZE[1]:
            img.putpixel((x, y), (*col, 255))
    return img
