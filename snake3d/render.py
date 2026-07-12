import os

import grid as gridmod
import isometric
import solver
import gif as gifmod

SHRINK_FRAMES = 5


def build_colors():
    return {
        "background": (20, 19, 33),
        "snake": (245, 215, 110),
        "buckets": [
            ((42, 33, 64), (32, 25, 49), (23, 18, 35)),
            ((74, 55, 130), (57, 42, 100), (41, 30, 72)),
            ((110, 80, 190), (85, 62, 146), (61, 44, 105)),
            ((150, 110, 220), (116, 85, 169), (83, 61, 121)),
            ((170, 139, 250), (131, 107, 193), (94, 76, 138)),
        ],
    }


def all_colors_flat(colors) -> list[tuple[int, int, int]]:
    flat = [colors["background"], colors["snake"]]
    for triple in colors["buckets"]:
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
