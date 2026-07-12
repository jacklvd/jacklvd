from PIL import Image


def build_palette_image(colors: list[tuple[int, int, int]]) -> Image.Image:
    ref = Image.new("P", (1, 1))
    palette_data: list[int] = []
    for color in colors:
        palette_data.extend(color)
    palette_data.extend([0, 0, 0] * (256 - len(colors)))
    ref.putpalette(palette_data)
    return ref


def encode_gif(frames: list[Image.Image], path: str, colors: list[tuple[int, int, int]], duration: int = 50) -> None:
    ref = build_palette_image(colors)
    indexed = [frame.quantize(palette=ref, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(
        path,
        save_all=True,
        append_images=indexed[1:],
        loop=0,
        duration=duration,
        optimize=False,
    )
