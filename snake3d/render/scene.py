import math
from functools import lru_cache

from PIL import Image

W, H, HORIZON, GROUND = 320, 120, 70, 106
# Ground scroll per full loop. Every scrolling layer's pattern repeats every LOOP_SCROLL * speed px,
# so whatever the gait, the last frame lines up with the first.
LOOP_SCROLL = 160

BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
SUN = (230, HORIZON - 2, 13)


def _hex(value: str) -> tuple[int, int, int]:
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


SKY = [_hex(c) for c in ("141321", "231a3f", "3a2861", "5a3d8a", "8462b8", "b07cc9", "d97bb0", "f0688f", "ff8a6b", "ffb06a")]
FIELD = [_hex(c) for c in ("8a8a3c", "6f8a38", "557a33", "41692e", "33592a", "284a24", "1f3d1e")]
GLOW_OUTER, GLOW_INNER, FIELD_GLOW = _hex("ffb877"), _hex("ffd08a"), _hex("a39a45")
SUN_DISK, SUN_CORE = _hex("ffd77e"), _hex("ffe9a8")
HILL_FAR, HILL_MID, TREES = _hex("6a4f94"), _hex("4a3570"), _hex("2a2140")
CLOUD, CLOUD_LIT = _hex("c788c9"), _hex("ff9f86")
WALL, WALL_LIT, ROOF, CHIMNEY = _hex("5c3f52"), _hex("8a5a5a"), _hex("3b2335"), _hex("2b1d2a")
WINDOW_LIT, WINDOW_DARK, LANTERN = _hex("ffd27a"), _hex("3b2335"), _hex("ffcf6a")
SMOKE = (_hex("cdbad6"), _hex("ab98ba"), _hex("8c7a9e"))
BIRD, STAR, STAR_DIM = _hex("2a1e3f"), _hex("fff4d6"), _hex("b9a6d6")
TUFT_FAR, TUFT_NEAR, BLADE, BLADE_TIP = _hex("7d8f3e"), _hex("4f7f35"), _hex("16301a"), _hex("8fae4c")
FLOWERS = (_hex("f0a0c0"), _hex("ffe08a"), _hex("e8e4f0"))
FIREFLY, SHADOW, DUST = _hex("fff27a"), _hex("1f3d1e"), _hex("b8a87a")


def _px(img, x, y, col) -> None:
    x, y = round(x), round(y)
    if 0 <= x < W and 0 <= y < H:
        img.putpixel((x, y), col)


def _rect(img, x, y, w, h, col) -> None:
    for yy in range(round(y), round(y) + h):
        for xx in range(round(x), round(x) + w):
            _px(img, xx, yy, col)


def _ridge(x: float, base: float, amp: float, detail: float, scale: float) -> int:
    return round(base + amp * math.sin(x / scale) + detail * math.sin(x / (scale * 0.37) + 1.7))


@lru_cache(maxsize=1)
def _backdrop() -> Image.Image:
    img = Image.new("RGB", (W, H))
    sx, sy, sr = SUN
    data = []
    for y in range(H):
        sky = y < HORIZON
        pal = SKY if sky else FIELD
        t = (y / HORIZON) * (len(pal) - 1) if sky else ((y - HORIZON) / (H - HORIZON)) ** 0.8 * (len(pal) - 1)
        i, f = int(t), t - int(t)
        for x in range(W):
            thr = (BAYER[y % 4][x % 4] + 0.5) / 16
            col = pal[min(len(pal) - 1, i + 1 if f > thr else i)]
            dist = math.hypot((x - sx) * 0.8, (y - sy) * 1.3)
            if sky:
                # two dithered glow rings soften the halo instead of one hard speckle field
                if 1 - (dist - sr) / 40 > thr:
                    col = GLOW_OUTER
                if 1 - (dist - sr) / 22 > thr:
                    col = GLOW_INNER
            elif 1 - (dist - sr) / 20 - (y - HORIZON) / 8 > thr:
                col = FIELD_GLOW
            data.append(col)
    img.putdata(data)
    for dy in range(-sr, 1):
        hw = int(math.sqrt(sr * sr - dy * dy))
        _rect(img, sx - hw, sy + dy, hw * 2, 1, SUN_CORE if dy > -4 else SUN_DISK)
    for x0, y0, w in ((40, 14, 22), (130, 22, 30), (205, 10, 18), (290, 26, 24)):
        _rect(img, x0, y0, w, 2, CLOUD)
        _rect(img, x0 + 4, y0 - 1, w - 10, 1, CLOUD)
        _rect(img, x0 + 2, y0 + 2, w - 3, 1, CLOUD_LIT)
    for x in range(W):
        h = _ridge(x, 9, 4, 2, 40)
        _rect(img, x, HORIZON - h, 1, h + 1, HILL_FAR)
    for x in range(W):
        h = _ridge(x, 5, 2.5, 1.5, 22)
        _rect(img, x, HORIZON - h, 1, h + 1, HILL_MID)
    return img


def build_backdrop() -> Image.Image:
    return _backdrop().copy()


def _tiles(scroll: float, speed: float):
    """Yields the left x of each repeat of a pattern whose period is LOOP_SCROLL * speed."""
    period = round(LOOP_SCROLL * speed)
    start = -round(scroll * speed) % period - period
    for k in range(W // period + 3):
        yield start + k * period, period


TREE_LINE = ((3, 5, 2.6), (11, 3, 2.0), (18, 6, 3.0), (31, 4, 2.2), (39, 5, 2.6), (52, 3, 1.8), (58, 4, 2.4))
TUFTS = [((i * 53) % 160, HORIZON + 4 + (i * 13) % (H - HORIZON - 6)) for i in range(70)]
FLOWER_SPOTS = [((i * 37 + 11) % 160, HORIZON + 10 + (i * 17) % (H - HORIZON - 14)) for i in range(18)]
STARS = [((i * 71 + 9) % W, 3 + (i * 29) % 22) for i in range(16)]
FIREFLIES = [((i * 43 + 20) % W, GROUND - 14 + (i * 11) % 16) for i in range(10)]
HOUSE_X = 262


def _blob(img, cx, cy, r, col) -> None:
    n = math.ceil(r)
    for dy in range(-n, n + 1):
        for dx in range(-n, n + 1):
            if dx * dx + dy * dy <= r * r:
                _px(img, cx + dx, cy + dy, col)


def _house(img, frac: float, loop_frames: int, level: int) -> None:
    x, y = HOUSE_X, HORIZON - 9
    _rect(img, x, y + 4, 8, 5, WALL)
    _rect(img, x + 6, y + 4, 2, 5, WALL_LIT)
    for i in range(4):
        _rect(img, x - 1 + i, y + 4 - i, 10 - 2 * i, 1, ROOF)
    _rect(img, x + 6, y, 1, 3, CHIMNEY)
    _rect(img, x + 2, y + 5, 2, 2, WINDOW_LIT if level >= 2 else WINDOW_DARK)
    if level >= 4:
        _px(img, x + 9, y + 6, LANTERN)
        _px(img, x + 9, y + 5, CHIMNEY)
    if level >= 2:
        cycles = max(1, loop_frames // 32)
        for i in range(6):
            age = (frac * cycles + i / 6) % 1
            _px(img, x + 6 - age * 6, y - 1 - age * 9, SMOKE[min(2, int(age * 3))])


def draw_world(img: Image.Image, frame: int, loop_frames: int, scroll: float, level: int) -> None:
    frac = (frame % loop_frames) / loop_frames
    if level >= 4:
        twinkle_cycles = max(1, loop_frames // 16)
        for i, (sx, sy) in enumerate(STARS):
            _px(img, sx, sy, STAR if math.sin(2 * math.pi * (frac * twinkle_cycles + i * 0.37)) > -0.2 else STAR_DIM)
        if 0.3 <= frac < 0.42:
            k = (frac - 0.3) / 0.12
            for tail in range(5):
                _px(img, 60 + k * 50 - tail, 6 + k * 12 - tail * 0.25, STAR if tail < 2 else STAR_DIM)
    if level >= 2:
        flaps = max(1, loop_frames // 8)
        for bx, by, ph in ((0, 20, 0.0), (12, 24, 0.3), (22, 18, 0.6)):
            x = frac * (W + 40) - 20 + bx
            y = by + round(math.sin(2 * math.pi * (frac + ph)))
            up = 1 if math.sin(2 * math.pi * (frac * flaps + ph)) > 0 else 0
            _px(img, x, y, BIRD)
            _px(img, x - 1, y - up, BIRD)
            _px(img, x + 1, y - up, BIRD)
    for left, _ in _tiles(scroll, 0.4):
        for tx, h, r in TREE_LINE:
            _rect(img, left + tx, HORIZON - h + 1, 1, h, TREES)
            _blob(img, left + tx, HORIZON - h - r * 0.4, r, TREES)
    _house(img, frac, loop_frames, level)
    for speed, near in ((0.5, False), (1.0, True)):
        for left, period in _tiles(scroll, speed):
            for tx, ty in TUFTS:
                if (ty - HORIZON > 14) != near:
                    continue
                x = left + tx * period / LOOP_SCROLL
                _px(img, x, ty, TUFT_NEAR if near else TUFT_FAR)
                if near:
                    _px(img, x + 1, ty - 1, TUFT_NEAR)
    if level >= 3:
        for left, _ in _tiles(scroll, 1.0):
            for i, (fx, fy) in enumerate(FLOWER_SPOTS):
                _px(img, left + fx, fy, FLOWERS[i % 3])


def draw_shadow(img: Image.Image, x: int, width: int) -> None:
    _rect(img, x - width // 2, GROUND, width, 1, SHADOW)
    _rect(img, x - width // 2 + 2, GROUND + 1, max(1, width - 4), 1, SHADOW)


def draw_dust(img: Image.Image, x: int, frame: int, loop_frames: int) -> None:
    frac = (frame % loop_frames) / loop_frames
    cycles = max(1, loop_frames // 16)
    for i in range(5):
        age = (frac * cycles + i / 5) % 1
        _px(img, x - age * 18, GROUND - 1 - age * 4 + (i % 2), DUST)


def draw_foreground(img: Image.Image, frame: int, loop_frames: int, scroll: float, level: int) -> None:
    frac = (frame % loop_frames) / loop_frames
    sways = max(1, loop_frames // 32)
    if level >= 3:
        blinks = max(1, loop_frames // 24)
        for i, (fx, fy) in enumerate(FIREFLIES):
            if math.sin(2 * math.pi * (frac * blinks + i * 0.37)) > 0.2:
                x = fx + 6 * math.sin(2 * math.pi * (frac + i / 10))
                y = fy + 3 * math.sin(2 * math.pi * (frac * 2 + i / 5))
                _px(img, x, y, FIREFLY)
    for left, _ in _tiles(scroll, 1.5):
        for i in range(48):
            gx, h = left + i * 5, 5 + (i * 7) % 6
            sway = math.sin(2 * math.pi * frac * sways + i * 0.6) * 1.2
            for r in range(h):
                _px(img, gx + sway * (r / h), H - 1 - r, BLADE_TIP if r > h - 2 else BLADE)
