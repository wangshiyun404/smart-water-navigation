"""Data loading and path planning services for the waterway navigation demo."""

from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
EARTH_RADIUS_M = 6_371_000.0
# Generous ceiling for inland-waterway travel; faster edges indicate corrupt data.
MAX_NAV_SPEED_MS = 25.0

STRATEGIES = {
    "距离最短线路": {"key": "distance", "color": "#2563eb"},
    "时间最短线路": {"key": "time", "color": "#16a34a"},
    "综合最优线路": {"key": "balanced", "color": "#dc2626"},
}

CASES = {
    "西江内河": {
        "prefix": "region1",
        "caption": "肇庆 -> 广州",
        "focus": "综合路线更可靠，低置信路段明显减少",
    },
    "珠三角核心": {
        "prefix": "region2",
        "caption": "广州 -> 东莞",
        "focus": "三条路径差异化明显，耗时优势直观",
    },
    "珠江出海": {
        "prefix": "region3",
        "caption": "东莞 -> 外海",
        "focus": "复杂水域中可靠性权重体现稳健选择",
    },
}


@dataclass
class RouteResult:
    strategy: str
    start_node: int
    end_node: int
    details: pd.DataFrame
    metrics: dict[str, float | int]
    explored_nodes: int
    filtered_edges: int
    runtime_ms: float
    algorithm: str


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in meters."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    value = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(value))


@lru_cache(maxsize=1)
def load_nodes() -> pd.DataFrame:
    nodes = pd.read_csv(BASE_DIR / "nodes.csv")
    nodes = nodes.rename(
        columns={"node_id": "node_id", "lat": "lat", "lon": "lon", "point_count": "point_count"}
    )
    nodes["node_id"] = nodes["node_id"].astype(int)
    return nodes


@lru_cache(maxsize=1)
def load_base_edges() -> pd.DataFrame:
    edges = pd.read_csv(BASE_DIR / "edges.csv")
    edges[["start_node", "end_node"]] = edges[["start_node", "end_node"]].astype(int)
    return edges


@lru_cache(maxsize=1)
def load_weight_edges() -> pd.DataFrame:
    """Read the weighted network and expose stable English field names."""
    raw = pd.read_excel(BASE_DIR / "edge_time_stats.xlsx")
    expected = [
        "start_node",
        "end_node",
        "distance_m",
        "base_time_s",
        "base_pass_count",
        "refined_time_s",
        "median_time_s",
        "time_std_s",
        "min_time_s",
        "max_time_s",
        "day_time_s",
        "night_time_s",
        "valid_pass_count",
        "speed_avg_ms",
        "confidence",
        "has_stats",
        "max_draft_m",
        "max_air_draft_m",
    ]
    if len(raw.columns) != len(expected):
        raise ValueError("edge_time_stats.xlsx 字段数量变化，无法按既定接口读取。")
    raw.columns = expected
    raw[["start_node", "end_node"]] = raw[["start_node", "end_node"]].astype(int)
    numeric = [column for column in expected if column not in {"start_node", "end_node", "has_stats"}]
    raw[numeric] = raw[numeric].apply(pd.to_numeric, errors="coerce")
    raw["has_stats"] = raw["has_stats"].fillna(False).astype(bool)
    raw["confidence"] = raw["confidence"].fillna(0.0)
    raw["valid_pass_count"] = raw["valid_pass_count"].fillna(0)
    raw["planning_time_s"] = raw["refined_time_s"].where(
        raw["has_stats"] & raw["refined_time_s"].notna(), raw["base_time_s"]
    )
    raw["planning_pass_count"] = raw["valid_pass_count"].where(
        raw["has_stats"], raw["base_pass_count"]
    ).fillna(0)
    return raw


def _matching_path(prefix: str, suffix: str) -> Path:
    """Find a case file while tolerating small filename variants.

    Earlier code only accepted names such as ``region1_xxx_path_summary.csv``.
    The shared coursework repository may instead contain files like
    ``region1_path_summary.csv``.  This helper tries several compatible
    patterns and returns the first stable match.
    """
    patterns = [
        f"{prefix}_*{suffix}",
        f"{prefix}{suffix}",
        f"{prefix}*{suffix}",
    ]
    seen: set[Path] = set()
    matches: list[Path] = []
    for pattern in patterns:
        for path in sorted(BASE_DIR.glob(pattern)):
            if path not in seen:
                seen.add(path)
                matches.append(path)
    if not matches:
        pattern_text = " 或 ".join(patterns)
        raise FileNotFoundError(f"无法定位案例文件：{pattern_text}")
    if len(matches) > 1:
        # Prefer the most explicit / shortest filename; this avoids crashing the
        # interface when duplicate export variants exist in the repository.
        matches = sorted(matches, key=lambda path: (len(path.name), path.name))
    return matches[0]


@lru_cache(maxsize=None)
def load_case_routes(case_name: str) -> dict[str, pd.DataFrame]:
    prefix = CASES[case_name]["prefix"]
    routes: dict[str, pd.DataFrame] = {}
    for index, strategy in enumerate(STRATEGIES, start=1):
        file_path = _matching_path(prefix, f"_path_{index}_*.csv")
        route = pd.read_csv(file_path)
        route.columns = [
            "sequence",
            "node_id",
            "lat",
            "lon",
            "distance_m",
            "time_s",
            "pass_count",
            "confidence",
        ]
        route["strategy"] = strategy
        route["node_id"] = route["node_id"].astype(int)
        routes[strategy] = route
    return routes


@lru_cache(maxsize=None)
def load_case_summary(case_name: str) -> pd.DataFrame:
    file_path = _matching_path(CASES[case_name]["prefix"], "_path_summary.csv")
    summary = pd.read_csv(file_path)
    summary.columns = ["strategy", "nodes", "edges", "distance_km", "time_min", "total_pass_count"]
    details = []
    for strategy, route in load_case_routes(case_name).items():
        segments = route.dropna(subset=["distance_m"])
        details.append(
            {
                "strategy": strategy,
                "avg_confidence": segments["confidence"].mean(),
                "low_confidence_pct": (segments["confidence"] < 0.4).mean() * 100,
            }
        )
    return summary.merge(pd.DataFrame(details), on="strategy", how="left")


def case_bounds(case_name: str, padding: float = 0.035) -> tuple[float, float, float, float]:
    points = pd.concat(load_case_routes(case_name).values(), ignore_index=True)
    return (
        float(points["lat"].min() - padding),
        float(points["lat"].max() + padding),
        float(points["lon"].min() - padding),
        float(points["lon"].max() + padding),
    )


def case_center(case_name: str) -> tuple[float, float]:
    points = pd.concat(load_case_routes(case_name).values(), ignore_index=True)
    return float(points["lat"].mean()), float(points["lon"].mean())


def case_interpretation(case_name: str) -> str:
    summary = load_case_summary(case_name).set_index("strategy")
    shortest = summary.loc["距离最短线路"]
    balanced = summary.loc["综合最优线路"]
    fastest = summary.loc["时间最短线路"]
    if case_name == "珠三角核心":
        saved = shortest["time_min"] - fastest["time_min"]
        return (
            f"时间最短线路较距离最短线路节省 {saved:.1f} 分钟，"
            "体现真实通航耗时权重能够识别几何距离无法表达的高效航道。"
        )
    extra_distance = balanced["distance_km"] - shortest["distance_km"]
    return (
        f"综合最优线路比距离最短线路多行驶 {extra_distance:.2f} km，"
        f"平均置信度由 {shortest['avg_confidence']:.3f} 提升至 {balanced['avg_confidence']:.3f}，"
        f"低置信路段占比由 {shortest['low_confidence_pct']:.1f}% "
        f"降至 {balanced['low_confidence_pct']:.1f}%。"
    )


@lru_cache(maxsize=1)
def build_adjacency() -> tuple[dict[int, list[dict]], dict[int, tuple[float, float]], float]:
    edges = load_weight_edges()
    nodes = load_nodes()
    positions = {
        int(row.node_id): (float(row.lat), float(row.lon))
        for row in nodes.itertuples(index=False)
    }
    adjacency: dict[int, list[dict]] = {}
    max_speed = 0.1
    for row in edges.itertuples(index=False):
        edge = row._asdict()
        adjacency.setdefault(int(row.start_node), []).append(edge)
        if row.planning_time_s and row.planning_time_s > 0:
            max_speed = max(max_speed, float(row.distance_m / row.planning_time_s))
    return adjacency, positions, max_speed


def nearest_node(lat: float, lon: float) -> tuple[int, float]:
    nodes = load_nodes()
    approx = (nodes["lat"] - lat) ** 2 + (nodes["lon"] - lon) ** 2
    nearest_candidates = nodes.loc[approx.nsmallest(8).index]
    distances = nearest_candidates.apply(
        lambda row: haversine_m(lat, lon, row["lat"], row["lon"]), axis=1
    )
    best_index = distances.idxmin()
    return int(nodes.loc[best_index, "node_id"]), float(distances.loc[best_index])


def _edge_cost(edge: dict, strategy: str) -> float:
    if strategy == "距离最短线路":
        return float(edge["distance_m"])
    base = float(edge["planning_time_s"])
    if strategy == "时间最短线路":
        return base
    return base * (1 + 3 * (1 - float(edge["confidence"])))


def _heuristic(
    node_id: int,
    end_node: int,
    strategy: str,
    positions: dict[int, tuple[float, float]],
    max_speed: float,
) -> float:
    lat1, lon1 = positions[node_id]
    lat2, lon2 = positions[end_node]
    direct_distance = haversine_m(lat1, lon1, lat2, lon2)
    if strategy == "距离最短线路":
        return direct_distance
    return direct_distance / max_speed


def plan_route(
    start_node: int,
    end_node: int,
    strategy: str,
    algorithm: str = "A*",
    ship_draft_m: float = 5.8,
    ship_air_draft_m: float = 22.0,
) -> RouteResult | None:
    """Plan one route while applying draft and air-draft constraints."""
    if start_node == end_node:
        return None
    if strategy not in STRATEGIES:
        raise ValueError(f"未知路线策略：{strategy}")
    adjacency, positions, max_speed = build_adjacency()
    if start_node not in positions or end_node not in positions:
        return None
    started = time.perf_counter()
    queue: list[tuple[float, float, int]] = [(0.0, 0.0, start_node)]
    best = {start_node: 0.0}
    previous: dict[int, tuple[int, dict]] = {}
    explored = 0
    filtered = 0
    use_astar = algorithm == "A*"
    while queue:
        _, current_cost, node_id = heapq.heappop(queue)
        if current_cost != best.get(node_id):
            continue
        explored += 1
        if node_id == end_node:
            break
        for edge in adjacency.get(node_id, []):
            travel_time = float(edge["planning_time_s"])
            if (
                ship_draft_m > float(edge["max_draft_m"])
                or ship_air_draft_m > float(edge["max_air_draft_m"])
                or travel_time <= 0
                or float(edge["distance_m"]) / travel_time > MAX_NAV_SPEED_MS
            ):
                filtered += 1
                continue
            target = int(edge["end_node"])
            new_cost = current_cost + _edge_cost(edge, strategy)
            if new_cost >= best.get(target, math.inf):
                continue
            best[target] = new_cost
            previous[target] = (node_id, edge)
            estimate = (
                _heuristic(target, end_node, strategy, positions, max_speed) if use_astar else 0.0
            )
            heapq.heappush(queue, (new_cost + estimate, new_cost, target))
    if end_node not in previous:
        return None
    route_edges: list[dict] = []
    cursor = end_node
    while cursor != start_node:
        parent, edge = previous[cursor]
        route_edges.append(edge)
        cursor = parent
    route_edges.reverse()
    rows = []
    for sequence, edge in enumerate(route_edges):
        start = int(edge["start_node"])
        end = int(edge["end_node"])
        rows.append(
            {
                "sequence": sequence,
                "start_node": start,
                "end_node": end,
                "start_lat": positions[start][0],
                "start_lon": positions[start][1],
                "end_lat": positions[end][0],
                "end_lon": positions[end][1],
                "distance_m": edge["distance_m"],
                "time_s": edge["planning_time_s"],
                "pass_count": edge["planning_pass_count"],
                "confidence": edge["confidence"],
                "has_stats": edge["has_stats"],
                "max_draft_m": edge["max_draft_m"],
                "max_air_draft_m": edge["max_air_draft_m"],
            }
        )
    details = pd.DataFrame(rows)
    metrics = summarize_details(details)
    return RouteResult(
        strategy=strategy,
        start_node=start_node,
        end_node=end_node,
        details=details,
        metrics=metrics,
        explored_nodes=explored,
        filtered_edges=filtered,
        runtime_ms=(time.perf_counter() - started) * 1000,
        algorithm=algorithm,
    )


def summarize_details(details: pd.DataFrame) -> dict[str, float | int]:
    if details.empty:
        return {}
    return {
        "segments": int(len(details)),
        "distance_km": float(details["distance_m"].sum() / 1000),
        "time_min": float(details["time_s"].sum() / 60),
        "total_pass_count": int(details["pass_count"].sum()),
        "avg_confidence": float(details["confidence"].mean()),
        "low_confidence_pct": float((details["confidence"] < 0.4).mean() * 100),
        "fallback_segments": int((~details["has_stats"]).sum()) if "has_stats" in details else 0,
    }


def routes_summary_frame(results: Iterable[RouteResult]) -> pd.DataFrame:
    records = []
    for result in results:
        metrics = result.metrics
        records.append(
            {
                "路线": result.strategy,
                "距离_km": round(float(metrics["distance_km"]), 2),
                "预计时间_min": round(float(metrics["time_min"]), 1),
                "总通行次数": int(metrics["total_pass_count"]),
                "平均置信度": round(float(metrics["avg_confidence"]), 3),
                "低置信路段占比_%": round(float(metrics["low_confidence_pct"]), 1),
                "回退边数": int(metrics["fallback_segments"]),
                "搜索节点数": result.explored_nodes,
                "计算耗时_ms": round(result.runtime_ms, 1),
            }
        )
    return pd.DataFrame(records)
