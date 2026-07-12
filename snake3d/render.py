import os

import grid as gridmod
import isometric
import solver
import gif as gifmod

SHRINK_FRAMES = 5


def build_colors():
    return {
        "background": (13, 17, 23),
        "snake": (255, 165, 0),
        "buckets": [
            ((22, 39, 55), (17, 30, 43), (12, 21, 30)),
            ((30, 70, 99), (23, 54, 77), (16, 38, 54)),
            ((25, 92, 133), (19, 71, 103), (13, 50, 73)),
            ((18, 114, 168), (14, 88, 130), (10, 62, 91)),
            ((14, 137, 202), (11, 106, 157), (7, 76, 112)),
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
