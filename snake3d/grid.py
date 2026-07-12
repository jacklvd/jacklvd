import requests

GRAPHQL_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            contributionCount
          }
        }
      }
    }
  }
}
"""

BUCKET_THRESHOLDS = [1, 4, 7, 10]


def bucket_height(count: int) -> int:
    bucket = 0
    for threshold in BUCKET_THRESHOLDS:
        if count >= threshold:
            bucket += 1
    return bucket


def parse_weeks(weeks: list[dict]) -> list[list[int]]:
    grid = []
    for week in weeks:
        days = [day["contributionCount"] for day in week["contributionDays"]]
        while len(days) < 7:
            days.append(0)
        grid.append(days)
    return grid


def fetch_contribution_weeks(username: str, token: str) -> list[list[int]]:
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": GRAPHQL_QUERY, "variables": {"username": username}},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return parse_weeks(data["weeks"])
