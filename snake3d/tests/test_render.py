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


def test_snake_glides_between_cells():
    from render.isometric import TILE_W, snake_points

    walk = [(0, 0), (1, 0), (1, 1), (2, 1)]
    dims = (3, 2)
    heads = [snake_points(walk, i / 4, dims)[0] for i in range(13)]
    for a, b in zip(heads, heads[1:]):
        step = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        assert 0 < step <= TILE_W / 4, step  # moves every frame, never jumps a whole cell
    body = snake_points(walk, 3.0, dims)
    assert len(body) > 4 and body[-1] == snake_points(walk, 0.0, dims)[0]  # tail clamps at the start


def test_radar_labels_show_counts():
    from render.charts import axis_label

    assert axis_label("Commit", 630) == ("Commit", "630")
    assert axis_label("Commit", 1234) == ("Commit", "1.2K")


def test_language_bands_scale_with_languages():
    from render.render import language_bands

    py, ts, c = (1, 1, 1), (2, 2, 2), (3, 3, 3)
    bands = language_bands([("Python", 0.5, py), ("TypeScript", 0.4, ts), ("C", 0.01, c)], 10)
    assert len(bands) == 10 and bands[0] == py and bands[-1] == c  # ordered by share, every language visible
    assert bands.count(py) > bands.count(ts) > bands.count(c) == 1
    assert language_bands([("Python", 1.0, py)], 10) == [py] * 10
    assert language_bands([("other", 1.0, c)], 4) == [language_bands([], 4)[0]] * 4  # "other" is not a language


def main():
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("all tests passed")


if __name__ == "__main__":
    main()
