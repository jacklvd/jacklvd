import argparse
import math
import os

from PIL import Image

from . import activity
from . import gif as gifmod
from . import scene
from .horse_sprite import GAITS, SPRITE_ANCHOR, draw_horse

HX = 150
SCALE = 2
FRAME_MS = 40
LEVELS = (1, 2, 3, 4)


def loop_frames(gait: str) -> int:
    g = GAITS[gait]
    if g.stride_px == 0:
        return g.frames
    assert scene.LOOP_SCROLL % g.stride_px == 0, gait
    return g.frames * (scene.LOOP_SCROLL // g.stride_px)


def render_frame(level: int, gait: str, frame: int) -> Image.Image:
    """One native-resolution (320x120) frame."""
    g, total = GAITS[gait], loop_frames(gait)
    phase = (frame % g.frames) / g.frames
    scroll = frame * g.stride_px / g.frames
    img = scene.build_backdrop()
    scene.draw_world(img, frame, total, scroll, level)
    lift = max(0.0, math.sin(2 * math.pi * (phase - 0.55))) if gait == "gallop" else 0.0
    scene.draw_shadow(img, HX, round((32 if level >= 2 else 24) - lift * 8))
    if level >= 4 and g.stride_px:
        scene.draw_dust(img, HX - 14, frame, total, g.stride_px / g.frames)
    sprite = draw_horse(frame, gait, level)
    img.paste(sprite, (HX - SPRITE_ANCHOR[0], scene.GROUND - SPRITE_ANCHOR[1]), sprite)
    scene.draw_foreground(img, frame, total, scroll, level)
    return img


def render_frames(level: int, gait: str) -> list[Image.Image]:
    return [render_frame(level, gait, frame) for frame in range(loop_frames(gait))]


def write_gif(frames: list[Image.Image], path: str) -> None:
    """Encodes native frames upscaled SCALEx, mapping every color to its exact palette slot."""
    colors: set[tuple[int, int, int]] = set()
    for frame in frames:
        found = frame.getcolors(maxcolors=256)
        if found is None:
            raise ValueError("frame has more than 256 colors")
        colors.update(color for _, color in found)
    if len(colors) > 256:
        raise ValueError(f"{len(colors)} colors exceed the GIF palette")
    palette = sorted(colors)
    # Pillow's quantize() matches colors at reduced precision and merged near-twins (sun #ffd77e -> window #ffd27a),
    # so index pixels ourselves.
    slot = {bytes(color): i for i, color in enumerate(palette)}
    ref = gifmod.build_palette_image(palette)
    indexed = []
    for frame in frames:
        data = frame.tobytes()
        p = Image.frombytes("P", frame.size, bytes(slot[data[i : i + 3]] for i in range(0, len(data), 3)))
        p.putpalette(ref.getpalette())
        indexed.append(p.resize((frame.width * SCALE, frame.height * SCALE), Image.NEAREST))
    tmp = f"{path}.tmp.gif"
    try:
        indexed[0].save(tmp, save_all=True, append_images=indexed[1:], loop=0, duration=FRAME_MS, optimize=True)
        os.replace(tmp, path)  # never leave a half-written GIF at the published path
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def write_preview(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for level in LEVELS:
        cells = []
        for gait in GAITS:
            name = f"level{level}-{gait}.gif"
            write_gif(render_frames(level, gait), os.path.join(out_dir, name))
            kb = os.path.getsize(os.path.join(out_dir, name)) // 1024
            cells.append(f'<td><img src="{name}" width="640"><br>level {level} · {gait} · {kb} KB</td>')
        rows.append(f"<tr>{''.join(cells)}</tr>")
    with open(os.path.join(out_dir, "index.html"), "w") as fh:
        fh.write(
            "<!doctype html><meta charset=utf-8><title>Horse preview</title>"
            "<style>body{background:#0d1117;color:#c9d1d9;font:14px system-ui}td{padding:8px;text-align:center}"
            "img{image-rendering:pixelated}</style>"
            f"<table>{''.join(rows)}</table>"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the pixel horse GIF")
    parser.add_argument("--level", type=int, choices=LEVELS)
    parser.add_argument("--gait", choices=list(GAITS))
    parser.add_argument("--out", default="horse.gif")
    parser.add_argument("--preview", metavar="DIR", help="render every level x gait into DIR with an index.html")
    args = parser.parse_args(argv)
    if (args.level is None) != (args.gait is None):
        parser.error("--level and --gait go together")
    return args


def main() -> None:
    args = parse_args()
    if args.preview:
        write_preview(args.preview)
        return
    if args.level and args.gait:
        level, gait = args.level, args.gait
    else:
        total, yesterday = activity.fetch_activity(os.environ["USERNAME"], os.environ["GITHUB_TOKEN"])
        level, gait = activity.level_for(total), activity.gait_for(yesterday)
        print(f"past year: {total} -> level {level}; yesterday: {yesterday} -> {gait}")
    write_gif(render_frames(level, gait), args.out)


if __name__ == "__main__":
    main()
