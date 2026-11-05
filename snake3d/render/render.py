import os

from . import charts
from . import grid as gridmod
from . import isometric
from . import solver
from . import stats as statsmod
from . import gif as gifmod

SUBSTEPS = 4  # frames per grid cell; the head glides between cells instead of snapping
FRAME_MS = 40

BACKGROUND = (20, 19, 33)
SNAKE = (245, 215, 110)
SNAKE_STRIPE = (214, 168, 72)
OUTLINE = (10, 9, 18)
EMPTY = ((42, 33, 64), (32, 25, 49), (23, 18, 35))
RADAR_GRID = (118, 116, 150)
RADAR_LINE = (245, 210, 90)
TEXT = (230, 230, 235)

RADAR_SIZE = (230, 220)
LEGEND_SIZE = (200, 150)
OVERLAY_MARGIN = 26

# Weeks are split into one color band per language (sized by share), so more languages = more colors.
# dev-note: GitHub has no per-day language data, so a band shows overall share, not what that week was written in
GRADIENT_STEPS = 16
FALLBACK_HUE = (167, 122, 250)
TOP_FACTORS = [0.55, 0.7, 0.85, 1.0]
LEFT_SCALE = 0.78
RIGHT_SCALE = 0.58


def _lerp(a, b, t) -> tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def band_languages(languages):
    """Real languages by share, at most one per band ("other" is a bucket, not a language)."""
    named = sorted((lang for lang in languages if lang[0] != "other"), key=lambda lang: -lang[1])
    return named[:GRADIENT_STEPS]


def language_bands(languages, steps: int = GRADIENT_STEPS) -> list[tuple[int, int, int]]:
    named = band_languages(languages)[:steps]
    if not named:
        return [FALLBACK_HUE] * steps
    total = sum(share for _, share, _ in named)
    ideal = [share / total * (steps - len(named)) for _, share, _ in named]
    counts = [1 + int(x) for x in ideal]  # every language gets at least one band
    by_remainder = sorted(range(len(named)), key=lambda i: int(ideal[i]) - ideal[i])
    for i in by_remainder[: steps - sum(counts)]:
        counts[i] += 1
    return [color for (_, _, color), n in zip(named, counts) for _ in range(n)]


def _scale(color, factor) -> tuple[int, int, int]:
    return tuple(min(255, round(c * factor)) for c in color)


def build_colors(languages):
    grid = []
    for hue in language_bands(languages):
        levels = []
        for factor in TOP_FACTORS:
            top = _lerp(BACKGROUND, hue, factor)
            levels.append((top, _scale(top, LEFT_SCALE), _scale(top, RIGHT_SCALE)))
        grid.append(levels)
    return {
        "background": BACKGROUND,
        "snake": SNAKE,
        "snake_stripe": SNAKE_STRIPE,
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
        colors["snake_stripe"],
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


def compose_overlays(frame, radar_img, legend_img):
    composed = frame.copy()
    width, height = composed.size
    composed.paste(radar_img, (width - radar_img.width - OVERLAY_MARGIN, OVERLAY_MARGIN))
    composed.paste(legend_img, (OVERLAY_MARGIN, height - legend_img.height - OVERLAY_MARGIN))
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
    colors = build_colors(profile_stats["languages"])

    radar_img = charts.draw_radar_chart(profile_stats["radar"], RADAR_SIZE, colors)
    legend_img = charts.draw_legend(band_languages(profile_stats["languages"]), LEGEND_SIZE, colors)

    frames = []
    for index in range(len(walk) - 1):
        week, day = walk[index + 1]
        start_height = heights_px[week][day]
        for sub in range(SUBSTEPS):
            s = index + sub / SUBSTEPS
            heights_px[week][day] = start_height * (1 - sub / SUBSTEPS)  # block sinks as the head arrives
            frames.append(isometric.draw_frame(heights_px, isometric.snake_points(walk, s, dims), s, dims, colors, size))
        heights_px[week][day] = 0
    end = len(walk) - 1
    frames.append(isometric.draw_frame(heights_px, isometric.snake_points(walk, end, dims), end, dims, colors, size))

    composed = [compose_overlays(frame, radar_img, legend_img) for frame in frames]
    language_colors = [color for _, _, color in profile_stats["languages"]]
    gifmod.encode_gif(composed, output_path, all_colors_flat(colors, language_colors), FRAME_MS)


if __name__ == "__main__":
    render(os.environ["USERNAME"], os.environ["GITHUB_TOKEN"], "output.gif")
