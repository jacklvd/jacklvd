def test_bucket_height():
    from render.grid import bucket_height
    assert bucket_height(0) == 0
    assert bucket_height(2) == 1
    assert bucket_height(5) == 2
    assert bucket_height(8) == 3
    assert bucket_height(12) == 4


def test_parse_weeks():
    from render.grid import parse_weeks

    raw_weeks = [
        {"contributionDays": [{"contributionCount": 1}, {"contributionCount": 0}]},
        {"contributionDays": [{"contributionCount": 3}]},
    ]
    result = parse_weeks(raw_weeks)
    assert len(result) == 2
    assert len(result[0]) == 7
    assert len(result[1]) == 7
    assert result[0][0] == 1
    assert result[0][1] == 0
    assert result[1][0] == 3
    assert result[1][1] == 0


def test_solver_walk_contiguous_and_covers_targets():
    from render.solver import solve

    grid = [
        [1, 0],
        [0, 0],
        [0, 2],
    ]
    walk = solve(grid)

    assert walk[0] == (0, 0)
    for (w1, d1), (w2, d2) in zip(walk, walk[1:]):
        assert abs(w1 - w2) + abs(d1 - d2) == 1

    targets = {(0, 0), (2, 1)}
    assert targets.issubset(set(walk))


def test_project_known_point():
    from render.isometric import project

    assert project(0, 0, (3, 2)) == (90, 70)
    assert project(2, 1, (3, 2)) == (100, 85)


def test_hex_to_rgb():
    from render.stats import hex_to_rgb

    assert hex_to_rgb("#3572A5") == (0x35, 0x72, 0xA5)
    assert hex_to_rgb(None) == (110, 110, 110)


def test_language_breakdown_ranks_and_buckets_other():
    from render.stats import language_breakdown

    repo_nodes = [
        {"languages": {"edges": [{"size": 100, "node": {"name": "Python", "color": "#3572A5"}}]}},
        {"languages": {"edges": [{"size": 50, "node": {"name": "HTML", "color": "#e34c26"}}]}},
        {"languages": {"edges": [{"size": 10, "node": {"name": "CSS", "color": "#663399"}}]}},
        {"languages": {"edges": [{"size": 5, "node": {"name": "Shell", "color": "#89e051"}}]}},
        {"languages": {"edges": [{"size": 3, "node": {"name": "Lua", "color": "#000080"}}]}},
        {"languages": {"edges": [{"size": 2, "node": {"name": "Makefile", "color": "#427819"}}]}},
    ]
    result = language_breakdown(repo_nodes)
    names = [name for name, _, _ in result]
    assert names == ["Python", "HTML", "CSS", "Shell", "Lua", "other"]
    assert abs(sum(fraction for _, fraction, _ in result) - 1.0) < 1e-9
    assert result[-1][1] == 2 / 170


def test_radar_value_ratio_log_scale():
    from render.charts import _value_ratio

    assert _value_ratio(1) == 0.0
    assert abs(_value_ratio(100) - 0.5) < 1e-9
    assert _value_ratio(10000) == 1.0
    assert _value_ratio(50000) == 1.0


def main():
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("all tests passed")


if __name__ == "__main__":
    main()
