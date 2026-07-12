from PIL import Image, ImageDraw

TILE_W = 20
TILE_H = 10
HEIGHT_SCALE = 8
MARGIN = 40


def project(week: int, day: int, dims: tuple[int, int]) -> tuple[int, int]:
    _, days = dims
    origin_x = days * (TILE_W // 2) + MARGIN
    origin_y = MARGIN
    x = origin_x + (week - day) * (TILE_W // 2)
    y = origin_y + (week + day) * (TILE_H // 2)
    return x, y


def canvas_size(dims: tuple[int, int]) -> tuple[int, int]:
    weeks, days = dims
    width = (weeks + days) * (TILE_W // 2) + MARGIN * 2
    height = (weeks + days) * (TILE_H // 2) + 4 * HEIGHT_SCALE + MARGIN * 2
    return width, height


def cube_polygons(x: int, y: int, height_px: float):
    hw = TILE_W // 2
    hh = TILE_H // 2
    top_y = y - height_px
    top = [(x, top_y - hh), (x + hw, top_y), (x, top_y + hh), (x - hw, top_y)]
    left = [(x - hw, top_y), (x, top_y + hh), (x, y + hh), (x - hw, y)]
    right = [(x, top_y + hh), (x + hw, top_y), (x + hw, y), (x, y + hh)]
    return top, left, right


def draw_frame(heights_px, snake_cells, dims, colors, size):
    weeks, days = dims
    image = Image.new("RGB", size, colors["background"])
    draw = ImageDraw.Draw(image)
    cells = sorted(
        ((w, d) for w in range(weeks) for d in range(days)),
        key=lambda c: c[0] + c[1],
    )
    snake_set = set(snake_cells)
    for week, day in cells:
        x, y = project(week, day, dims)
        height_px = heights_px[week][day]
        top, left, right = cube_polygons(x, y, height_px)
        bucket = max(0, min(4, int(height_px // HEIGHT_SCALE)))
        top_color, left_color, right_color = colors["buckets"][bucket]
        draw.polygon(left, fill=left_color)
        draw.polygon(right, fill=right_color)
        draw.polygon(top, fill=top_color)
        if (week, day) in snake_set:
            draw.polygon(top, fill=colors["snake"])
    return image
