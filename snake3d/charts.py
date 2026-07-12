import math

from PIL import Image, ImageDraw, ImageFont

RADAR_LABELS = ["Commit", "Issue", "PullReq", "Review", "Repo"]
RADAR_RINGS = [(0.0, "1"), (0.25, "10"), (0.5, "100"), (0.75, "1K"), (1.0, "10K")]
RADAR_MAX_VALUE = 10000
RADAR_FILL_ALPHA = 110


def _axis_point(center, radius, index, count=5):
    angle = -math.pi / 2 + index * (2 * math.pi / count)
    return (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))


def _angle_point(center, radius, angle_deg):
    angle = math.radians(angle_deg)
    return (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))


# Midpoint between the "Repo" and "Commit" spokes -- a gap with no axis label,
# so the 1/10/100/1K/10K ring markers never overlap a metric name.
RING_LABEL_ANGLE = -90 - 36


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


def draw_radar_chart(metrics: dict[str, int], size: tuple[int, int], date_range_label: str, colors: dict) -> Image.Image:
    width, height = size
    background = Image.new("RGBA", size, (*colors["background"], 255))
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default(size=13)
    small_font = ImageFont.load_default(size=11)

    header_h = 18
    draw.text((width - 4, 2), date_range_label, fill=(*colors["radar_grid"], 255), font=small_font, anchor="ra")

    cx = width // 2
    cy = header_h + (height - header_h) // 2
    max_radius = min(width, height - header_h) // 2 - 26

    for frac, label in RADAR_RINGS:
        radius = max_radius * frac
        if radius > 0:
            points = [_axis_point((cx, cy), radius, i) for i in range(5)]
            for a, b in zip(points, points[1:] + points[:1]):
                _dashed_line(draw, a, b, (*colors["radar_grid"], 255))
        label_point = _angle_point((cx, cy), radius, RING_LABEL_ANGLE)
        draw.text(label_point, label, fill=(*colors["radar_grid"], 255), font=small_font, anchor="mm")

    data_points = [
        _axis_point((cx, cy), max_radius * _value_ratio(metrics[name]), i)
        for i, name in enumerate(RADAR_LABELS)
    ]
    draw.polygon(data_points, fill=(*colors["radar_line"], RADAR_FILL_ALPHA), outline=(*colors["radar_line"], 255))

    for i, name in enumerate(RADAR_LABELS):
        label_point = _axis_point((cx, cy), max_radius + 16, i)
        draw.text(label_point, name, fill=(*colors["text"], 255), font=font, anchor="mm")

    return Image.alpha_composite(background, overlay).convert("RGB")


def draw_donut_chart(languages: list[tuple[str, float, tuple[int, int, int]]], size: tuple[int, int], colors: dict) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, colors["background"])
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=13)

    if not languages:
        return image

    outer_r = min(height, width // 2) // 2 - 6
    cx = outer_r + 8
    cy = height // 2
    inner_r = int(outer_r * 0.55)

    bbox = [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r]
    start = -90.0
    for _, fraction, color in languages:
        extent = fraction * 360
        draw.pieslice(bbox, start, start + extent, fill=color)
        start += extent
    draw.ellipse(
        [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
        fill=colors["background"],
    )

    legend_x = cx + outer_r + 20
    legend_y = cy - (len(languages) * 20) // 2
    swatch = 14
    for name, _, color in languages:
        draw.rectangle([legend_x, legend_y, legend_x + swatch, legend_y + swatch], fill=color)
        draw.text((legend_x + swatch + 8, legend_y - 1), name, fill=colors["text"], font=font)
        legend_y += 20

    return image
