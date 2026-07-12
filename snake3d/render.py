import os

import grid as gridmod
import isometric
import solver
import gif as gifmod

SHRINK_FRAMES = 5

BACKGROUND = (20, 19, 33)
SNAKE = (245, 215, 110)
OUTLINE = (10, 9, 18)
EMPTY = ((42, 33, 64), (32, 25, 49), (23, 18, 35))

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
    }


def all_colors_flat(colors) -> list[tuple[int, int, int]]:
    flat = [colors["background"], colors["snake"], colors["outline"], *colors["empty"]]
    for levels in colors["grid"]:
        for triple in levels:
            flat.extend(triple)
    return flat


def build_heights_px(raw_grid: list[list[int]]) -> list[list[float]]:
    return [[gridmod.bucket_height(count) * isometric.HEIGHT_SCALE for count in row] for row in raw_grid]


def render(username: str, token: str, output_path: str) -> None:
    raw_grid = gridmod.fetch_contribution_weeks(username, token)
    walk = solver.solve(raw_grid)
    dims = (len(raw_grid), len(raw_grid[0]))
    size = isometric.canvas_size(dims)
    heights_px = build_heights_px(raw_grid)
    colors = build_colors()

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

    gifmod.encode_gif(frames, output_path, all_colors_flat(colors))


if __name__ == "__main__":
    render(os.environ["USERNAME"], os.environ["GITHUB_TOKEN"], "output.gif")
