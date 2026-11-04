from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from .grid import bucket_height

ACTIVITY_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

LEVEL_THRESHOLDS = (100, 400, 1000)
GAITS_BY_BUCKET = ("graze", "walk", "trot", "gallop", "gallop")
TIMEZONE = ZoneInfo("America/Los_Angeles")


def level_for(total: int) -> int:
    return 1 + sum(total >= threshold for threshold in LEVEL_THRESHOLDS)


def gait_for(count: int) -> str:
    return GAITS_BY_BUCKET[bucket_height(count)]


def yesterday_count(days: list[tuple[str, int]], today: date) -> int:
    target = (today - timedelta(days=1)).isoformat()
    return next((count for day, count in days if day == target), 0)


def fetch_activity(username: str, token: str) -> tuple[int, int]:
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": ACTIVITY_QUERY, "variables": {"username": username}},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    calendar = response.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [
        (day["date"], day["contributionCount"])
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]
    return calendar["totalContributions"], yesterday_count(days, datetime.now(TIMEZONE).date())
