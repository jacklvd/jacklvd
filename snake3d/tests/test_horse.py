def test_level_for():
    from render.activity import level_for

    assert [level_for(n) for n in (0, 99, 100, 399, 400, 999, 1000, 5000)] == [1, 1, 2, 2, 3, 3, 4, 4]


def test_gait_for():
    from render.activity import gait_for

    assert [gait_for(n) for n in (0, 1, 3, 4, 6, 7, 10, 40)] == [
        "graze", "walk", "walk", "trot", "trot", "gallop", "gallop", "gallop",
    ]


def test_yesterday_count_by_date_not_position():
    from datetime import date
    from render.activity import yesterday_count

    days = [("2026-11-02", 5), ("2026-11-03", 2), ("2026-11-04", 9)]
    assert yesterday_count(days, date(2026, 11, 4)) == 2
    assert yesterday_count(days, date(2026, 11, 10)) == 0


def test_sprite_fits_and_is_deterministic():
    from render.horse_sprite import draw_horse, GAITS, SPRITE_SIZE

    for gait, g in GAITS.items():
        for level in (1, 2, 3, 4):
            for f in range(0, g.frames, max(1, g.frames // 4)):
                img = draw_horse(f, gait, level)
                assert img.size == SPRITE_SIZE
                left, top, right, bottom = img.getbbox()
                assert left > 0 and top > 0 and right < SPRITE_SIZE[0] and bottom < SPRITE_SIZE[1], (gait, level, f)
    assert draw_horse(5, "gallop", 3).tobytes() == draw_horse(5, "gallop", 3).tobytes()


def test_sprite_cycle_loops():
    from render.horse_sprite import draw_horse, GAITS

    for gait, g in GAITS.items():
        assert draw_horse(0, gait, 3).tobytes() == draw_horse(g.frames, gait, 3).tobytes()


def test_rim_light_only_from_level_3():
    from render.horse_sprite import draw_horse

    rim = (0xF0, 0x7A, 0x8C, 255)
    assert rim not in {c for _, c in draw_horse(0, "gallop", 2).getcolors(10000)}
    assert rim in {c for _, c in draw_horse(0, "gallop", 3).getcolors(10000)}


def test_backdrop_no_banding_and_static():
    from render.scene import build_backdrop, HORIZON

    a, b = build_backdrop(), build_backdrop()
    assert a.tobytes() == b.tobytes()
    row = [a.getpixel((x, HORIZON // 2)) for x in range(64)]
    assert len(set(row)) >= 2  # dithered: mid-sky rows mix two colors


def test_world_wraps_after_one_loop():
    from render.scene import build_backdrop, draw_world, draw_foreground, LOOP_SCROLL

    def frame_at(f, scroll):
        img = build_backdrop()
        draw_world(img, f, 64, scroll, 4)
        draw_foreground(img, f, 64, scroll, 4)
        return img.tobytes()

    assert frame_at(0, 0) == frame_at(64, LOOP_SCROLL)


def test_house_is_bigger_at_level_4():
    from render.scene import build_backdrop, draw_world, WALL, WALL_LIT

    def wall_pixels(level):
        img = build_backdrop()
        draw_world(img, 0, 64, 0, level)
        return sum(n for n, c in img.getcolors(10000) if c in (WALL, WALL_LIT))

    assert wall_pixels(4) >= 1.5 * wall_pixels(3)


def test_loop_frames_wrap_scroll():
    from render.horse import loop_frames
    from render.horse_sprite import GAITS
    from render.scene import LOOP_SCROLL

    assert [loop_frames(g) for g in ("graze", "walk", "trot", "gallop")] == [64, 160, 100, 64]
    for g in ("walk", "trot", "gallop"):
        gait = GAITS[g]
        assert loop_frames(g) * gait.stride_px / gait.frames == LOOP_SCROLL


def test_gif_deterministic_and_small():
    import os
    import tempfile
    from render.horse import render_frames, write_gif

    d = tempfile.mkdtemp()
    a, b = os.path.join(d, "a.gif"), os.path.join(d, "b.gif")
    write_gif(render_frames(4, "walk"), a)  # longest loop, most detail
    write_gif(render_frames(4, "walk"), b)
    assert open(a, "rb").read() == open(b, "rb").read()
    assert os.path.getsize(a) < 1_000_000, os.path.getsize(a)


def test_write_gif_rejects_palette_overflow():
    import os
    import tempfile
    from PIL import Image
    from render.horse import write_gif

    frames = [Image.new("RGB", (32, 16))]
    frames[0].putdata([(i % 256, (i // 256) * 100, 0) for i in range(512)])  # 512 distinct colors
    path = os.path.join(tempfile.mkdtemp(), "x.gif")
    try:
        write_gif(frames, path)
    except AssertionError:
        assert not os.path.exists(path)
    else:
        raise AssertionError("palette overflow was accepted")


def test_gif_pixels_match_rendered_frames():
    import os
    import tempfile
    from PIL import Image
    from render.horse import render_frames, write_gif, SCALE

    frames = render_frames(4, "gallop")[:4]  # level >= 2 has the near-identical sun/window yellows
    path = os.path.join(tempfile.mkdtemp(), "h.gif")
    write_gif(frames, path)
    gif = Image.open(path)
    for i, frame in enumerate(frames):
        gif.seek(i)
        expected = frame.resize((frame.width * SCALE, frame.height * SCALE), Image.NEAREST)
        assert gif.convert("RGB").tobytes() == expected.tobytes(), f"frame {i} colors were remapped"


def test_planted_hooves_stay_on_ground():
    from render.horse_sprite import GAITS, body_bob, body_scale, ground_units, leg_points, stance_sweep

    for gait in ("walk", "trot", "gallop"):
        g = GAITS[gait]
        for level in (1, 2):
            s = body_scale(level)
            sweep, gy = stance_sweep(g, s), ground_units(g, s)
            for f in range(g.frames):
                phase = f / g.frames
                hip_y = body_bob(g, phase) + 2
                for key, hx, front in (("hl", -7, False), ("hr", -7, False), ("fl", 7, True), ("fr", 7, True)):
                    p = (phase + g.offsets[key]) % 1
                    if p < g.stance:
                        _, (_, hoof_y) = leg_points(hx, hip_y, p, front, g, sweep, gy)
                        assert abs(hoof_y - gy) * s <= 0.5, (gait, level, f, key, hoof_y, gy)


def test_pacific_today_crosses_utc_midnight():
    from datetime import datetime, timezone
    from render.activity import pacific_today

    assert pacific_today(datetime(2026, 11, 4, 5, 0, tzinfo=timezone.utc)).isoformat() == "2026-11-03"
    assert pacific_today(datetime(2026, 11, 4, 9, 0, tzinfo=timezone.utc)).isoformat() == "2026-11-04"


def test_full_frame_loops_for_every_gait():
    from render.horse import loop_frames, render_frame

    for gait in ("graze", "walk", "trot", "gallop"):
        assert render_frame(4, gait, 0).tobytes() == render_frame(4, gait, loop_frames(gait)).tobytes(), gait


def main():
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("all tests passed")


if __name__ == "__main__":
    main()
