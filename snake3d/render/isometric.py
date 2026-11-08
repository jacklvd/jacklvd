import math

from PIL import Image, ImageDraw

TILE_W = 20
TILE_H = 10
HEIGHT_SCALE = 8
MARGIN = 70
TOP_PAD = 60  # extra headroom so the top-right radar sits above the board, not on it

SNAKE_CELLS = 5  # body length in grid cells
SNAKE_SPACING = 0.25  # one body disc every quarter cell
HEAD_R, TAIL_R = 6.0, 2.5


def project(week: int, day: int, dims: tuple[int, int]) -> tuple[int, int]:
    _, days = dims
    origin_x = days * (TILE_W // 2) + MARGIN
    origin_y = MARGIN + TOP_PAD
    x = origin_x + (week - day) * (TILE_W // 2)
    y = origin_y + (week + day) * (TILE_H // 2)
    return x, y


def canvas_size(dims: tuple[int, int]) -> tuple[int, int]:
    weeks, days = dims
    width = (weeks + days) * (TILE_W // 2) + MARGIN * 2
    height = (weeks + days) * (TILE_H // 2) + 4 * HEIGHT_SCALE + MARGIN * 2 + TOP_PAD
    return width, height


def cube_polygons(x: int, y: int, height_px: float):
    hw = TILE_W // 2
    hh = TILE_H // 2
    top_y = y - height_px
    top = [(x, top_y - hh), (x + hw, top_y), (x, top_y + hh), (x - hw, top_y)]
    left = [(x - hw, top_y), (x, top_y + hh), (x, y + hh), (x - hw, y)]
    right = [(x, top_y + hh), (x + hw, top_y), (x + hw, y), (x, y + hh)]
    return top, left, right


def _point_at(walk, s, dims) -> tuple[float, float]:
    s = max(0.0, min(s, len(walk) - 1))
    i = int(s)
    if i == len(walk) - 1:
        return project(*walk[i], dims)
    (ax, ay), (bx, by), t = project(*walk[i], dims), project(*walk[i + 1], dims), s - i
    return ax + (bx - ax) * t, ay + (by - ay) * t


def snake_points(walk, s: float, dims) -> list[tuple[float, float]]:
    """Body disc centers, head first, with the head s cells along the walk (fractional = between cells)."""
    count = round(SNAKE_CELLS / SNAKE_SPACING) + 1
    return [_point_at(walk, s - k * SNAKE_SPACING, dims) for k in range(count)]


def draw_snake(draw, points, s: float, colors) -> None:
    last = len(points) - 1
    discs = []
    for k, (x, y) in enumerate(points):
        r = HEAD_R - (HEAD_R - TAIL_R) * k / last
        # stripes are pinned to walk distance, so they travel with the body instead of sliding along it
        stripe = math.floor(s - k * SNAKE_SPACING) % 2
        discs.append((x, y - r * 0.6, r, colors["snake_stripe"] if stripe else colors["snake"]))
    for x, y, r, _ in reversed(discs):
        draw.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1], fill=colors["outline"])
    for x, y, r, fill in reversed(discs):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    hx, hy, _, _ = discs[0]
    dx, dy = hx - discs[2][0], hy - discs[2][1]
    norm = math.hypot(dx, dy)
    dx, dy = (dx / norm, dy / norm) if norm > 1e-6 else (1.0, 0.0)
    for side in (-1, 1):
        ex, ey = hx + dx * 2 - dy * 2.6 * side, hy + dy * 2 + dx * 2.6 * side
        draw.ellipse([ex - 1.6, ey - 1.6, ex + 1.6, ey + 1.6], fill=colors["text"])
        draw.point((round(ex + dx * 0.6), round(ey + dy * 0.6)), fill=colors["outline"])


def draw_frame(heights_px, snake_pts, s, dims, colors, size):
    weeks, days = dims
    image = Image.new("RGB", size, colors["background"])
    draw = ImageDraw.Draw(image)
    cells = sorted(
        ((w, d) for w in range(weeks) for d in range(days)),
        key=lambda c: c[0] + c[1],
    )
    outline = colors["outline"]
    steps = len(colors["grid"])
    for week, day in cells:
        x, y = project(week, day, dims)
        height_px = heights_px[week][day]
        top, left, right = cube_polygons(x, y, height_px)
        bucket = 0 if height_px <= 0 else max(1, min(4, math.ceil(height_px / HEIGHT_SCALE)))  # sinking blocks keep their color
        if bucket == 0:
            top_color, left_color, right_color = colors["empty"]
        else:
            step = round((week / (weeks - 1)) * (steps - 1)) if weeks > 1 else 0
            top_color, left_color, right_color = colors["grid"][step][bucket - 1]
        draw.polygon(left, fill=left_color, outline=outline)
        draw.polygon(right, fill=right_color, outline=outline)
        draw.polygon(top, fill=top_color, outline=outline)
    # dev-note: snake is drawn over the whole grid, so a tall block in front never hides it; per-cell depth
    # interleaving if that ever looks wrong (it only crosses already-eaten, flat cells, so it rarely shows)
    draw_snake(draw, snake_pts, s, colors)
    return image
