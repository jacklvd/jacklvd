def test_bucket_height():
    from grid import bucket_height
    assert bucket_height(0) == 0
    assert bucket_height(2) == 1
    assert bucket_height(5) == 2
    assert bucket_height(8) == 3
    assert bucket_height(12) == 4


def test_parse_weeks():
    from grid import parse_weeks

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


def main():
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("all tests passed")


if __name__ == "__main__":
    main()
