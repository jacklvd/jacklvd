import requests

STATS_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
"""

TOP_LANGUAGE_COUNT = 5
OTHER_COLOR = (110, 110, 110)


def fetch_profile_stats(username: str, token: str) -> dict:
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": STATS_QUERY, "variables": {"username": username}},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    user = response.json()["data"]["user"]
    return {
        "radar": radar_metrics(user["contributionsCollection"]),
        "languages": language_breakdown(user["repositories"]["nodes"]),
    }


def radar_metrics(contributions: dict) -> dict[str, int]:
    return {
        "Commit": contributions["totalCommitContributions"],
        "Issue": contributions["totalIssueContributions"],
        "PullReq": contributions["totalPullRequestContributions"],
        "Review": contributions["totalPullRequestReviewContributions"],
        "Repo": contributions["totalRepositoryContributions"],
    }


def language_breakdown(repo_nodes: list[dict]) -> list[tuple[str, float, tuple[int, int, int]]]:
    totals: dict[str, int] = {}
    colors: dict[str, tuple[int, int, int]] = {}
    for repo in repo_nodes:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            totals[name] = totals.get(name, 0) + edge["size"]
            colors[name] = hex_to_rgb(edge["node"]["color"])

    grand_total = sum(totals.values())
    if grand_total == 0:
        return []

    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    top = ranked[:TOP_LANGUAGE_COUNT]
    rest_size = sum(size for _, size in ranked[TOP_LANGUAGE_COUNT:])

    breakdown = [(name, size / grand_total, colors[name]) for name, size in top]
    if rest_size > 0:
        breakdown.append(("other", rest_size / grand_total, OTHER_COLOR))
    return breakdown


def hex_to_rgb(value: str | None) -> tuple[int, int, int]:
    if not value:
        return OTHER_COLOR
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
