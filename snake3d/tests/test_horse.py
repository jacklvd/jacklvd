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


def main():
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("all tests passed")


if __name__ == "__main__":
    main()
