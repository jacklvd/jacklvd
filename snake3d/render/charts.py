import math

from PIL import Image, ImageDraw, ImageFont

RADAR_LABELS = ["Commit", "Issue", "PullReq", "Review", "Repo"]
RADAR_RINGS = [0.25, 0.5, 0.75, 1.0]  # log rings at 10 / 100 / 1K / 10K
RADAR_MAX_VALUE = 10000
RADAR_FILL_ALPHA = 150


def _axis_point(center, radius, index, count=5):
    angle = -math.pi / 2 + index * (2 * math.pi / count)
    return (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))


def _dashed_line(draw, p1, p2, color, dash=4, gap=4):
    x1, y1 = p1
    x2, y2 = p2
    dist = math.hypot(x2 - x1, y2 - y1)
    if dist == 0:
        return
    dx, dy = (x2 - x1) / dist, (y2 - y1) / dist
    pos = 0.0
    on = True
    while pos < dist:
        seg = dash if on else gap
        end = min(pos + seg, dist)
        if on:
            draw.line([(x1 + dx * pos, y1 + dy * pos), (x1 + dx * end, y1 + dy * end)], fill=color)
        pos = end
        on = not on


def _value_ratio(value: int) -> float:
    return max(0.0, min(1.0, math.log10(max(value, 1)) / math.log10(RADAR_MAX_VALUE)))


def axis_label(name: str, value: int) -> tuple[str, str]:
    if value < 1000:
        return name, str(value)
    return name, f"{value / 1000:.1f}".removesuffix(".0") + "K"


def draw_radar_chart(metrics: dict[str, int], size: tuple[int, int], colors: dict) -> Image.Image:
    width, height = size
    background = Image.new("RGBA", size, (*colors["background"], 255))
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default(size=14)

    # exact counts sit under each axis name, so the old 1/10/100/1K/10K ring numbers (crowded at the center) are gone
    cx, cy = width // 2, height // 2 + 4
    max_radius = min(width, height) // 2 - 38

    for frac in RADAR_RINGS:
        points = [_axis_point((cx, cy), max_radius * frac, i) for i in range(5)]
        for a, b in zip(points, points[1:] + points[:1]):
            _dashed_line(draw, a, b, (*colors["radar_grid"], 255))

    data_points = [
        _axis_point((cx, cy), max_radius * _value_ratio(metrics[name]), i)
        for i, name in enumerate(RADAR_LABELS)
    ]
    draw.polygon(data_points, fill=(*colors["radar_line"], RADAR_FILL_ALPHA), outline=(*colors["radar_line"], 255), width=2)

    for i, name in enumerate(RADAR_LABELS):
        x, y = _axis_point((cx, cy), max_radius + 22, i)
        title, count = axis_label(name, metrics[name])
        draw.text((x, y), title, fill=(*colors["text"], 255), font=font, anchor="md")
        draw.text((x, y + 1), count, fill=(*colors["radar_line"], 255), font=font, anchor="ma")

    return Image.alpha_composite(background, overlay).convert("RGB")


def draw_legend(languages: list[tuple[str, float, tuple[int, int, int]]], size: tuple[int, int], colors: dict) -> Image.Image:
    """Which language each block color band stands for, in band order (oldest weeks first)."""
    image = Image.new("RGB", size, colors["background"])
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=13)
    swatch, row = 12, 20
    y = size[1] - len(languages) * row
    for name, share, color in languages:
        draw.rectangle([0, y + 2, swatch, y + 2 + swatch], fill=color, outline=colors["outline"])
        draw.text((swatch + 8, y), f"{name} {round(share * 100)}%", fill=colors["text"], font=font)
        y += row
    return image
