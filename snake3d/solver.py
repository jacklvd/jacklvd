from collections import deque

Cell = tuple[int, int]


def neighbors(cell: Cell, dims: tuple[int, int]) -> list[Cell]:
    week, day = cell
    weeks, days = dims
    candidates = [(week - 1, day), (week + 1, day), (week, day - 1), (week, day + 1)]
    return [c for c in candidates if 0 <= c[0] < weeks and 0 <= c[1] < days]


def bfs_from(start: Cell, dims: tuple[int, int]) -> tuple[dict[Cell, int], dict[Cell, Cell]]:
    dist = {start: 0}
    parent: dict[Cell, Cell] = {}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for nxt in neighbors(current, dims):
            if nxt not in dist:
                dist[nxt] = dist[current] + 1
                parent[nxt] = current
                queue.append(nxt)
    return dist, parent


def reconstruct_path(parent: dict[Cell, Cell], start: Cell, goal: Cell) -> list[Cell]:
    if goal == start:
        return [start]
    path = [goal]
    current = goal
    while current != start:
        current = parent[current]
        path.append(current)
    path.reverse()
    return path


def solve(grid: list[list[int]]) -> list[Cell]:
    weeks, days = len(grid), len(grid[0])
    dims = (weeks, days)
    targets = {(w, d) for w in range(weeks) for d in range(days) if grid[w][d] > 0}

    start: Cell = (0, 0)
    walk = [start]
    targets.discard(start)
    current = start

    while targets:
        dist, parent = bfs_from(current, dims)
        nearest = min(targets, key=lambda c: dist[c])
        path = reconstruct_path(parent, current, nearest)
        for cell in path[1:]:
            walk.append(cell)
            targets.discard(cell)
        current = nearest

    return walk


def snake_body(walk: list[Cell], index: int, max_len: int = 8) -> list[Cell]:
    start_idx = max(0, index - max_len + 1)
    return walk[start_idx:index + 1]
