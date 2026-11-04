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


def main():
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("all tests passed")


if __name__ == "__main__":
    main()
