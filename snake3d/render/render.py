import os
from datetime import datetime, timedelta, timezone

from . import charts
from . import grid as gridmod
from . import isometric
from . import solver
from . import stats as statsmod
from . import gif as gifmod

SHRINK_FRAMES = 5

BACKGROUND = (20, 19, 33)
SNAKE = (245, 215, 110)
OUTLINE = (10, 9, 18)
EMPTY = ((42, 33, 64), (32, 25, 49), (23, 18, 35))
RADAR_GRID = (90, 90, 110)
RADAR_LINE = (245, 210, 90)
TEXT = (230, 230, 235)

RADAR_SIZE = (210, 205)
DONUT_SIZE = (310, 150)
OVERLAY_MARGIN = 26

# Same three stops as the README's capsule-render footer (0:141321,50:A78BFA,100:F0568C),
# swept left-to-right across the weeks so the grid reads as one gradient instead of flat purple.
GRADIENT_STOPS = [(20, 19, 33), (167, 122, 250), (240, 86, 140)]
GRADIENT_STEPS = 16
TOP_FACTORS = [0.55, 0.7, 0.85, 1.0]
LEFT_SCALE = 0.78
RIGHT_SCALE = 0.58


def _lerp(a, b, t) -> tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient_hue(t: float) -> tuple[int, int, int]:
    if t <= 0.5:
        return _lerp(GRADIENT_STOPS[0], GRADIENT_STOPS[1], t / 0.5)
    return _lerp(GRADIENT_STOPS[1], GRADIENT_STOPS[2], (t - 0.5) / 0.5)


def _scale(color, factor) -> tuple[int, int, int]:
    return tuple(min(255, round(c * factor)) for c in color)


def build_colors():
    grid = []
    for step in range(GRADIENT_STEPS):
        hue = _gradient_hue(step / (GRADIENT_STEPS - 1))
        levels = []
        for factor in TOP_FACTORS:
            top = _lerp(BACKGROUND, hue, factor)
            levels.append((top, _scale(top, LEFT_SCALE), _scale(top, RIGHT_SCALE)))
        grid.append(levels)
    return {
        "background": BACKGROUND,
        "snake": SNAKE,
        "outline": OUTLINE,
        "empty": EMPTY,
        "grid": grid,
        "radar_grid": RADAR_GRID,
        "radar_line": RADAR_LINE,
        "text": TEXT,
    }


def _blend(fg, bg, alpha_frac) -> tuple[int, int, int]:
    return tuple(round(fg[i] * alpha_frac + bg[i] * (1 - alpha_frac)) for i in range(3))


def all_colors_flat(colors, language_colors: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    flat = [
        colors["background"],
        colors["snake"],
        colors["outline"],
        *colors["empty"],
        colors["radar_grid"],
        colors["radar_line"],
        colors["text"],
        _blend(colors["radar_line"], colors["background"], charts.RADAR_FILL_ALPHA / 255),
        _blend(colors["radar_line"], colors["radar_grid"], charts.RADAR_FILL_ALPHA / 255),
        *language_colors,
    ]
    for levels in colors["grid"]:
        for triple in levels:
            flat.extend(triple)
    return flat


def compose_overlays(frame, radar_img, donut_img):
    composed = frame.copy()
    width, height = composed.size
    composed.paste(radar_img, (width - radar_img.width - OVERLAY_MARGIN, OVERLAY_MARGIN))
    composed.paste(donut_img, (OVERLAY_MARGIN, height - donut_img.height - OVERLAY_MARGIN))
    return composed


def build_heights_px(raw_grid: list[list[int]]) -> list[list[float]]:
    return [[gridmod.bucket_height(count) * isometric.HEIGHT_SCALE for count in row] for row in raw_grid]


def render(username: str, token: str, output_path: str) -> None:
    raw_grid = gridmod.fetch_contribution_weeks(username, token)
    profile_stats = statsmod.fetch_profile_stats(username, token)
    walk = solver.solve(raw_grid)
    dims = (len(raw_grid), len(raw_grid[0]))
    size = isometric.canvas_size(dims)
    heights_px = build_heights_px(raw_grid)
    colors = build_colors()

    today = datetime.now(timezone.utc).date()
    date_range_label = f"{(today - timedelta(days=365)).isoformat()} / {today.isoformat()}"
    radar_img = charts.draw_radar_chart(profile_stats["radar"], RADAR_SIZE, date_range_label, colors)
    donut_img = charts.draw_donut_chart(profile_stats["languages"], DONUT_SIZE, colors)

    frames = []
    for index, cell in enumerate(walk):
        body = solver.snake_body(walk, index)
        week, day = cell
        target_height = heights_px[week][day]
        if target_height > 0:
            for step in range(1, SHRINK_FRAMES + 1):
                heights_px[week][day] = target_height * (1 - step / SHRINK_FRAMES)
                frames.append(isometric.draw_frame(heights_px, body, dims, colors, size))
            heights_px[week][day] = 0
        else:
            frames.append(isometric.draw_frame(heights_px, body, dims, colors, size))

    composed = [compose_overlays(frame, radar_img, donut_img) for frame in frames]
    language_colors = [color for _, _, color in profile_stats["languages"]]
    gifmod.encode_gif(composed, output_path, all_colors_flat(colors, language_colors))


if __name__ == "__main__":
    render(os.environ["USERNAME"], os.environ["GITHUB_TOKEN"], "output.gif")
