"""Single-page smart waterway route planning workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_DEPENDENCIES = PROJECT_DIR / ".vendor"
if LOCAL_DEPENDENCIES.exists():
    sys.path.insert(0, str(LOCAL_DEPENDENCIES))

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from nav_core import CASES, STRATEGIES, load_case_routes, nearest_node, plan_route


st.set_page_config(
    page_title="智能规划 | 交互式水上导航系统",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root {
        --navy: #071e35; --ocean: #086788; --cyan: #18a3be; --ice: #f4f8fb;
        --ink: #14273d; --muted: #5e7084; --line: #dae4ed; --safe: #13755b;
      }
      .stApp {background: var(--ice);}
      .block-container {max-width: 1510px; padding: 1.05rem 1.45rem 1.4rem;}
      section[data-testid="stSidebar"] {background: #ffffff; border-right: 1px solid var(--line);}
      section[data-testid="stSidebar"] .block-container {padding-top: 1.25rem;}
      .topbar {
        background: linear-gradient(112deg, #071e35, #0b5168 63%, #128ca5);
        border-radius: 18px; color: #fff; padding: 1rem 1.25rem;
        display: flex; justify-content: space-between; align-items: center; margin-bottom: .8rem;
      }
      .topbar h1 {font-size: 1.42rem; margin: 0 0 .18rem; font-weight: 680;}
      .topbar p {font-size: .86rem; opacity: .78; margin: 0;}
      .system-state {
        padding: .38rem .72rem; border: 1px solid rgba(255,255,255,.28);
        border-radius: 999px; font-size: .82rem; background: rgba(255,255,255,.1);
      }
      .side-brand {font-size: 1.15rem; font-weight: 700; color: var(--ink); margin-bottom: .15rem;}
      .side-subtitle {font-size: .84rem; color: var(--muted); margin-bottom: .82rem;}
      .step-title {
        display: flex; align-items: center; gap: .52rem; color: var(--ink);
        font-weight: 650; font-size: .92rem; margin: .86rem 0 .45rem;
      }
      .step-no {
        display: inline-flex; align-items: center; justify-content: center; height: 1.34rem;
        width: 1.34rem; border-radius: 50%; background: #e4f5f8; color: #08758e;
        font-size: .72rem; font-weight: 750;
      }
      .hint {
        color: var(--muted); font-size: .8rem; background: #f4f8fb; border-radius: 10px;
        padding: .52rem .62rem; margin: .35rem 0;
      }
      .metric-note {font-size: .78rem; color: var(--muted); margin-top: .26rem;}
      div[data-testid="stMetric"] {
        border: 1px solid var(--line); background: #fff; border-radius: 14px;
        padding: .56rem .72rem .62rem;
      }
      .panel {
        border: 1px solid var(--line); background: #fff; border-radius: 16px;
        padding: .88rem .92rem; margin-bottom: .65rem;
      }
      .panel-label {
        color: #5e7084; font-size: .73rem; text-transform: uppercase;
        letter-spacing: .06em; margin-bottom: .3rem;
      }
      .route-title {font-weight: 710; color: var(--ink); font-size: 1.08rem;}
      .route-copy {font-size: .86rem; color: var(--muted); line-height: 1.55; margin-top: .4rem;}
      .tag {
        display: inline-block; border-radius: 999px; font-size: .74rem;
        padding: .17rem .47rem; color: #08758e; background: #e5f6f8; margin-left: .4rem;
      }
      .alert {
        border-left: 3px solid #f59e0b; background: #fff8eb; color: #79551b;
        border-radius: 8px; padding: .55rem .64rem; font-size: .84rem; margin-top: .62rem;
      }
      .ready {
        border-left: 3px solid var(--safe); background: #eefaf5; color: #185d49;
        border-radius: 8px; padding: .55rem .64rem; font-size: .84rem; margin-top: .62rem;
      }
      .algo-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: .48rem; margin: .2rem 0 .72rem;
      }
      .algo-item {
        border: 1px solid var(--line); border-radius: 10px; background: #f8fbfd;
        padding: .46rem .52rem;
      }
      .algo-key {font-size: .74rem; color: var(--muted); margin-bottom: .12rem;}
      .algo-value {font-size: .94rem; color: var(--ink); font-weight: 650;}
      /* Keep the algorithm token in English even when browser translation is active. */
      .st-key-planning_algorithm div[role="radiogroup"] label:nth-child(2) p {
        font-size: 0;
      }
      .st-key-planning_algorithm div[role="radiogroup"] label:nth-child(2) p::after {
        content: "Dijkstra";
        font-size: .95rem;
      }
      .empty {
        background: #fff; border: 1px dashed #c6d6e3; border-radius: 16px;
        padding: 1rem .95rem; color: var(--muted); line-height: 1.64;
      }
      iframe {border-radius: 16px;}
      div[data-testid="stButton"] button[kind="primary"] {
        background: #087c97; border-color: #087c97; border-radius: 10px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


TILE_OPTIONS = {
    "普通地图": "CartoDB positron",
    "深色底图": "CartoDB dark_matter",
    "卫星底图": (
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}"
    ),
}
ROUTE_COLORS = {
    "距离最短线路": "#168aad",
    "时间最短线路": "#1b998b",
    "综合最优线路": "#155eef",
}
ROUTE_LABELS = {
    "距离最短线路": "里程最短",
    "时间最短线路": "时间最短",
    "综合最优线路": "稳健推荐",
}
SHIP_PRESETS = {
    "内河货船": {"draft": 5.8, "air_draft": 22.0},
    "客运游船": {"draft": 3.2, "air_draft": 12.0},
    "小型公务艇": {"draft": 2.0, "air_draft": 8.0},
}


@dataclass
class DisplayRoute:
    name: str
    coordinates: list[list[float]]
    metrics: dict[str, float | int]
    details: pd.DataFrame
    explored_nodes: int
    filtered_edges: int
    runtime_ms: float
    algorithm: str


@st.cache_data(show_spinner=False)
def shortcut_locations() -> dict[str, tuple[float, float]]:
    labels = {
        "西江内河": ("肇庆港区", "广州西航道"),
        "珠三角核心": ("广州航道", "东莞港区"),
        "珠江出海": ("东莞出海口", "外海航段"),
    }
    locations: dict[str, tuple[float, float]] = {}
    for case_name in CASES:
        route = load_case_routes(case_name)["综合最优线路"]
        start_label, end_label = labels[case_name]
        locations[start_label] = (float(route.iloc[0]["lat"]), float(route.iloc[0]["lon"]))
        locations[end_label] = (float(route.iloc[-1]["lat"]), float(route.iloc[-1]["lon"]))
    return locations


def create_map(center: tuple[float, float], tile_name: str, zoom: int = 10) -> folium.Map:
    tile = TILE_OPTIONS[tile_name]
    if tile_name == "卫星底图":
        map_obj = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=True)
        folium.TileLayer(tile, attr="Esri World Imagery", name=tile_name).add_to(map_obj)
        return map_obj
    return folium.Map(location=center, zoom_start=zoom, tiles=tile, control_scale=True)


def point_marker(map_obj: folium.Map, point: tuple[float, float], label: str, color: str) -> None:
    folium.Marker(
        point,
        tooltip=label,
        popup=f"<b>{label}</b><br>{point[0]:.6f}, {point[1]:.6f}",
        icon=folium.Icon(color=color, icon="flag" if color == "red" else "play"),
    ).add_to(map_obj)


def input_map(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    tile_name: str,
) -> folium.Map:
    center = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2)
    map_obj = create_map(center, tile_name)
    point_marker(map_obj, start_point, "当前起点", "green")
    point_marker(map_obj, end_point, "当前终点", "red")
    map_obj.fit_bounds([start_point, end_point])
    return map_obj


def reliability_text(confidence: float) -> str:
    if confidence >= 0.7:
        return "较高"
    if confidence >= 0.4:
        return "中等"
    return "较低"


def add_risk_segments(map_obj: folium.Map, route: DisplayRoute) -> None:
    low_confidence = route.details[route.details["confidence"] < 0.4].head(18)
    for segment in low_confidence.itertuples(index=False):
        point = [(segment.start_lat + segment.end_lat) / 2, (segment.start_lon + segment.end_lon) / 2]
        folium.CircleMarker(
            point,
            radius=5,
            color="#d97706",
            fill=True,
            fill_color="#f59e0b",
            fill_opacity=0.86,
            tooltip=f"低置信航段 · 置信度 {segment.confidence:.3f}",
        ).add_to(map_obj)


def result_map(
    routes: dict[str, DisplayRoute],
    active_route: str,
    tile_name: str,
    show_alternatives: bool,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
) -> folium.Map:
    highlighted = routes[active_route]
    center = (
        sum(point[0] for point in highlighted.coordinates) / len(highlighted.coordinates),
        sum(point[1] for point in highlighted.coordinates) / len(highlighted.coordinates),
    )
    map_obj = create_map(center, tile_name)
    visible_routes = routes if show_alternatives else {active_route: highlighted}
    for name, route in visible_routes.items():
        selected = name == active_route
        layer = folium.FeatureGroup(name=name, show=True)
        folium.PolyLine(
            route.coordinates,
            color=ROUTE_COLORS[name],
            weight=7 if selected else 4,
            opacity=0.96 if selected else 0.5,
            dash_array=None if selected else "8 7",
            tooltip=(
                f"{name} | {route.metrics['distance_km']:.1f} km | "
                f"{route.metrics['time_min']:.0f} min"
            ),
        ).add_to(layer)
        layer.add_to(map_obj)
    point_marker(map_obj, start_point, "规划起点", "green")
    point_marker(map_obj, end_point, "规划终点", "red")
    add_risk_segments(map_obj, highlighted)
    if show_alternatives and len(routes) > 1:
        folium.LayerControl(collapsed=True).add_to(map_obj)
    map_obj.fit_bounds(highlighted.coordinates)
    return map_obj


def plan_custom_routes(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    route_names: list[str],
    algorithm: str,
    ship_draft: float,
    ship_air_draft: float,
) -> tuple[dict[str, DisplayRoute], dict[str, float | int], str | None]:
    start_node, start_gap = nearest_node(*start_point)
    end_node, end_gap = nearest_node(*end_point)
    match = {
        "start_node": start_node,
        "end_node": end_node,
        "start_gap": start_gap,
        "end_gap": end_gap,
    }
    if max(start_gap, end_gap) > 5000:
        return {}, match, "起点或终点距离航道路网超过 5 km，请重新选点。"
    if start_node == end_node:
        return {}, match, "起点与终点匹配到同一航道节点，请拉开规划距离。"
    routes: dict[str, DisplayRoute] = {}
    for name in route_names:
        result = plan_route(
            start_node,
            end_node,
            name,
            algorithm=algorithm,
            ship_draft_m=ship_draft,
            ship_air_draft_m=ship_air_draft,
        )
        if result is None:
            continue
        detail = result.details
        coordinates = [[float(detail.iloc[0]["start_lat"]), float(detail.iloc[0]["start_lon"])]]
        coordinates.extend(detail[["end_lat", "end_lon"]].values.tolist())
        routes[name] = DisplayRoute(
            name=name,
            coordinates=coordinates,
            metrics=result.metrics,
            details=detail,
            explored_nodes=result.explored_nodes,
            filtered_edges=result.filtered_edges,
            runtime_ms=result.runtime_ms,
            algorithm=result.algorithm,
        )
    if not routes:
        return {}, match, "当前起终点与船舶约束下未找到可通行路线，请调整后重试。"
    return routes, match, None


def comparison_frame(routes: dict[str, DisplayRoute]) -> pd.DataFrame:
    records = []
    for route in routes.values():
        metrics = route.metrics
        records.append(
            {
                "方案": route_label(route.name),
                "距离 (km)": round(float(metrics["distance_km"]), 1),
                "预计时间 (min)": round(float(metrics["time_min"])),
                "可靠性": reliability_text(float(metrics["avg_confidence"])),
                "低置信航段 (%)": round(float(metrics["low_confidence_pct"]), 1),
            }
        )
    return pd.DataFrame(records)


def detailed_frame(routes: dict[str, DisplayRoute]) -> pd.DataFrame:
    frames = [route.details.assign(strategy=route.name) for route in routes.values()]
    return pd.concat(frames, ignore_index=True)


def downloadable_map(map_obj: folium.Map) -> bytes:
    return map_obj.get_root().render().encode("utf-8")


def route_label(route_name: str) -> str:
    return ROUTE_LABELS.get(route_name, route_name.replace("线路", ""))


locations = shortcut_locations()
default_start_name = "肇庆港区"
default_end_name = "广州西航道"
default_start = locations[default_start_name]
default_end = locations[default_end_name]

defaults = {
    "planner_start": default_start,
    "planner_end": default_end,
    "planner_start_name": default_start_name,
    "planner_end_name": default_end_name,
    "planned_routes": {},
    "planned_meta": {},
    "planned_source": "",
    "planned_requested": ["综合最优线路"],
    "planner_feedback": None,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

with st.sidebar:
    st.markdown('<div class="side-brand">航程规划控制台</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-subtitle">按步骤设置条件并生成可解释路线</div>', unsafe_allow_html=True)

    st.markdown('<div class="step-title"><span class="step-no">01</span>选择起点与终点</div>', unsafe_allow_html=True)
    input_mode = st.radio("定位方式", ["地图选点", "快捷港区", "精确坐标"], horizontal=True, label_visibility="collapsed")
    start_point = st.session_state.planner_start
    end_point = st.session_state.planner_end
    start_name = st.session_state.planner_start_name
    end_name = st.session_state.planner_end_name
    if input_mode == "快捷港区":
        start_name = st.selectbox("起点", list(locations), index=list(locations).index(default_start_name))
        end_name = st.selectbox("终点", list(locations), index=list(locations).index(default_end_name))
        start_point, end_point = locations[start_name], locations[end_name]
    elif input_mode == "精确坐标":
        start_lat = st.number_input("起点纬度", value=float(start_point[0]), format="%.6f")
        start_lon = st.number_input("起点经度", value=float(start_point[1]), format="%.6f")
        end_lat = st.number_input("终点纬度", value=float(end_point[0]), format="%.6f")
        end_lon = st.number_input("终点经度", value=float(end_point[1]), format="%.6f")
        start_point, end_point = (start_lat, start_lon), (end_lat, end_lon)
        start_name, end_name = "坐标起点", "坐标终点"
    else:
        st.markdown(
            f'<div class="hint">在地图上点击后设为起点或终点。<br>'
            f'起点：{start_point[0]:.5f}, {start_point[1]:.5f}<br>'
            f'终点：{end_point[0]:.5f}, {end_point[1]:.5f}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="step-title"><span class="step-no">02</span>设置船舶约束</div>', unsafe_allow_html=True)
    ship_type = st.selectbox("船舶模板", list(SHIP_PRESETS), index=0)
    preset = SHIP_PRESETS[ship_type]
    with st.expander("吃水与净空参数", expanded=False):
        ship_draft = st.number_input("吃水深度 (m)", min_value=0.1, value=preset["draft"], step=0.1)
        ship_air_draft = st.number_input("净空高度 (m)", min_value=1.0, value=preset["air_draft"], step=0.5)

    st.markdown('<div class="step-title"><span class="step-no">03</span>选择规划方式</div>', unsafe_allow_html=True)
    requested_routes = st.multiselect(
        "规划目标（可选一种或多种）",
        list(STRATEGIES),
        default=["综合最优线路"],
        format_func=route_label,
    )
    algorithm = st.radio("规划算法", ["A*", "Dijkstra"], horizontal=True, key="planning_algorithm")
    tile_name = st.selectbox("地图底图", list(TILE_OPTIONS), index=0)

    st.markdown('<div class="step-title"><span class="step-no">04</span>生成航线</div>', unsafe_allow_html=True)
    submitted = st.button("开始规划", type="primary", width="stretch")
    st.markdown(
        '<div class="hint">约束字段当前用于验证规划机制，不能替代真实水深、桥梁净空或海事通告。</div>',
        unsafe_allow_html=True,
    )

if submitted:
    st.session_state.planned_routes = {}
    st.session_state.planned_meta = {}
    st.session_state.planner_feedback = None
    if not requested_routes:
        st.session_state.planner_feedback = ("error", "请至少选择一种规划目标。")
    elif start_point == end_point:
        st.session_state.planner_feedback = ("error", "起点与终点不能相同，请重新选择位置。")
    elif not (
        -90 <= start_point[0] <= 90
        and -180 <= start_point[1] <= 180
        and -90 <= end_point[0] <= 90
        and -180 <= end_point[1] <= 180
    ):
        st.session_state.planner_feedback = ("error", "经纬度超出有效范围，请检查输入。")
    else:
        with st.spinner("正在匹配航道并计算路线..."):
            planned_routes, matched, error_message = plan_custom_routes(
                start_point,
                end_point,
                requested_routes,
                algorithm,
                ship_draft,
                ship_air_draft,
            )
        if error_message:
            st.session_state.planner_feedback = ("error", error_message)
        else:
            st.session_state.planned_routes = planned_routes
            st.session_state.planned_meta = matched
            st.session_state.planned_source = algorithm
            st.session_state.planned_requested = requested_routes
            st.session_state.planner_start = start_point
            st.session_state.planner_end = end_point
            st.session_state.planner_start_name = start_name
            st.session_state.planner_end_name = end_name
            st.session_state.planner_feedback = ("success", "规划完成，已生成所选路线方案。")

routes: dict[str, DisplayRoute] = st.session_state.planned_routes
state_text = "规划完成" if routes else "待规划"
st.markdown(
    f"""
    <div class="topbar">
      <div><h1>智能水上导航与路径规划系统</h1>
      <p>自定义选点 · 多目标规划 · 结果可解释与导出</p></div>
      <div class="system-state">{state_text}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
feedback = st.session_state.planner_feedback
if feedback:
    feedback_type, feedback_message = feedback
    if feedback_type == "success":
        st.success(feedback_message)
    else:
        st.error(feedback_message)

if routes:
    requested_at_plan = st.session_state.planned_requested
    recommended = "综合最优线路" if "综合最优线路" in requested_at_plan else requested_at_plan[0]
    if "active_route" not in st.session_state or st.session_state.active_route not in routes:
        st.session_state.active_route = recommended
    active_route = st.session_state.active_route
    selected = routes[active_route]
    metrics = selected.metrics
    meta = st.session_state.planned_meta

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("预计航行时间", f"{float(metrics['time_min']):.0f} min")
    metric_1.markdown('<div class="metric-note">基于历史航段耗时</div>', unsafe_allow_html=True)
    metric_2.metric("总航程", f"{float(metrics['distance_km']):.1f} km")
    metric_2.markdown('<div class="metric-note">路线累计长度</div>', unsafe_allow_html=True)
    metric_3.metric("路线可靠性", reliability_text(float(metrics["avg_confidence"])))
    metric_3.markdown('<div class="metric-note">依据航段历史数据置信度</div>', unsafe_allow_html=True)
    metric_4.metric("低置信航段", f"{float(metrics['low_confidence_pct']):.1f}%")
    metric_4.markdown('<div class="metric-note">地图以橙色节点提示</div>', unsafe_allow_html=True)

    control_left, control_right = st.columns([1.3, 1])
    with control_left:
        show_alternatives = st.toggle("显示备选路线", value=len(routes) > 1, disabled=len(routes) <= 1)
    with control_right:
        if len(routes) > 1:
            active_route = st.selectbox("查看路线", list(routes), key="active_route")
            selected = routes[active_route]
        else:
            st.caption(f"当前输出：{route_label(selected.name)}")

    map_column, result_column = st.columns([1.7, 0.9], gap="large")
    with map_column:
        rendered_map = result_map(
            routes,
            active_route,
            tile_name,
            show_alternatives,
            st.session_state.planner_start,
            st.session_state.planner_end,
        )
        click_result = st_folium(
            rendered_map,
            height=625,
            use_container_width=True,
            key=f"result_map_{input_mode}_{tile_name}_{active_route}_{show_alternatives}",
            returned_objects=["last_clicked"] if input_mode == "地图选点" else [],
        )
        if input_mode == "地图选点" and click_result and click_result.get("last_clicked"):
            click = click_result["last_clicked"]
            pick_1, pick_2, pick_3 = st.columns([2, 1, 1])
            pick_1.caption(f"选中位置：{click['lat']:.6f}, {click['lng']:.6f}")
            if pick_2.button("设为起点", key="result_start"):
                st.session_state.planner_start = (float(click["lat"]), float(click["lng"]))
                st.session_state.planner_start_name = "地图选定起点"
                st.session_state.planned_routes = {}
                st.session_state.planner_feedback = None
                st.rerun()
            if pick_3.button("设为终点", key="result_end"):
                st.session_state.planner_end = (float(click["lat"]), float(click["lng"]))
                st.session_state.planner_end_name = "地图选定终点"
                st.session_state.planned_routes = {}
                st.session_state.planner_feedback = None
                st.rerun()
    with result_column:
        selected = routes[active_route]
        metrics = selected.metrics
        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-label">推荐结果</div>
              <div class="route-title">{route_label(selected.name)}<span class="tag notranslate" translate="no">{selected.algorithm}</span></div>
              <div class="route-copy">{st.session_state.planner_start_name} → {st.session_state.planner_end_name}<br>
              起终点已匹配航道路网，偏差分别为 {meta["start_gap"]:.0f} m 与 {meta["end_gap"]:.0f} m。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if float(metrics["low_confidence_pct"]) >= 30:
            st.markdown(
                '<div class="alert">该路线低置信航段占比较高，请结合稳健路线与人工规则复核。</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="ready">当前路线未出现明显的大比例低置信航段。</div>',
                unsafe_allow_html=True,
            )
        with st.expander("路线对比", expanded=len(routes) > 1):
            st.dataframe(comparison_frame(routes), hide_index=True, width="stretch")
        with st.expander("规划依据与算法信息"):
            st.markdown(
                f"""
                <div class="algo-grid">
                  <div class="algo-item"><div class="algo-key">规划算法</div><div class="algo-value notranslate" translate="no">{selected.algorithm}</div></div>
                  <div class="algo-item"><div class="algo-key">搜索节点数</div><div class="algo-value">{selected.explored_nodes:,}</div></div>
                  <div class="algo-item"><div class="algo-key">约束过滤边次数</div><div class="algo-value">{selected.filtered_edges:,}</div></div>
                  <div class="algo-item"><div class="algo-key">计算耗时</div><div class="algo-value"><span class="notranslate" translate="no">{selected.runtime_ms:.1f} ms</span></div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("可靠性由航段历史数据置信度汇总；低置信比例表示置信度低于 0.4 的航段占比。")
        with st.expander("导出结果"):
            summary = comparison_frame(routes)
            st.download_button(
                "下载规划摘要 CSV",
                summary.to_csv(index=False).encode("utf-8-sig"),
                "智能导航_规划摘要.csv",
                "text/csv",
                width="stretch",
            )
            st.download_button(
                "下载路段明细 CSV",
                detailed_frame(routes).to_csv(index=False).encode("utf-8-sig"),
                "智能导航_路段明细.csv",
                "text/csv",
                width="stretch",
            )
            st.download_button(
                "导出交互地图 HTML",
                downloadable_map(rendered_map),
                "智能导航_路线地图.html",
                "text/html",
                width="stretch",
            )
else:
    map_column, result_column = st.columns([1.7, 0.9], gap="large")
    with map_column:
        picker_map = input_map(start_point, end_point, tile_name)
        click_result = st_folium(
            picker_map,
            height=650,
            use_container_width=True,
            key=f"picker_map_{input_mode}_{tile_name}",
            returned_objects=["last_clicked"] if input_mode == "地图选点" else [],
        )
        if input_mode == "地图选点" and click_result and click_result.get("last_clicked"):
            click = click_result["last_clicked"]
            pick_1, pick_2, pick_3 = st.columns([2, 1, 1])
            pick_1.caption(f"选中位置：{click['lat']:.6f}, {click['lng']:.6f}")
            if pick_2.button("设为起点", key="picker_start"):
                st.session_state.planner_start = (float(click["lat"]), float(click["lng"]))
                st.session_state.planner_start_name = "地图选定起点"
                st.session_state.planner_feedback = None
                st.rerun()
            if pick_3.button("设为终点", key="picker_end"):
                st.session_state.planner_end = (float(click["lat"]), float(click["lng"]))
                st.session_state.planner_end_name = "地图选定终点"
                st.session_state.planner_feedback = None
                st.rerun()
    with result_column:
        st.markdown(
            """
            <div class="empty">
              <b>开始一次自定义规划</b><br>
              1. 选择港区、点击地图或输入坐标确定航程。<br>
              2. 设置船舶吃水与净空限制。<br>
              3. 选择规划目标及算法。<br>
              4. 点击“开始规划”查看推荐路线与可导出结果。<br><br>
              地图点击选点为默认入口；橙色提示仅在结果中表示真实低置信航段。
            </div>
            """,
            unsafe_allow_html=True,
        )
