"""Waterway network overview page."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
LOCAL_DEPENDENCIES = PROJECT_DIR / ".vendor"
if LOCAL_DEPENDENCIES.exists():
    sys.path.insert(0, str(LOCAL_DEPENDENCIES))

import streamlit as st

from nav_core import CASES, case_interpretation, load_case_summary, load_nodes, load_weight_edges
from ui import hero, inject_global_css, metric_card, section_title


st.set_page_config(page_title="航道网络 | 智能水上导航系统", page_icon="🕸️", layout="wide")
inject_global_css()

hero(
    "航道网络：把轨迹组织成可搜索的水上路网",
    "这一页把节点、边、案例区域和路线差异集中展示出来，帮助观众理解 Folium 地图背后的网络结构。",
    "节点 · 有向边 · 区域案例",
)

nodes = load_nodes()
# The fork does not currently include edges.csv.  The weighted edge workbook is
# the authoritative edge table used by the planner, so this page uses it as the
# network source instead of load_base_edges().
edges = load_weight_edges()
stat_edges = edges[edges["has_stats"]].copy()

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("节点数量", f"{len(nodes):,}", "航道位置骨架")
with c2:
    metric_card("规划边数量", f"{len(edges):,}", "来自动态边权表")
with c3:
    metric_card("平均出边", f"{len(edges) / len(nodes):.2f}", "粗略反映网络连通度")
with c4:
    metric_card("统计边数量", f"{len(stat_edges):,}", "具有历史通行统计")

section_title("节点热度样例", "按轨迹点聚合数量查看高频位置，适合解释“哪些地方更像航道枢纽”。")
hot_nodes = nodes.sort_values("point_count", ascending=False).head(12)
st.dataframe(
    hot_nodes[["node_id", "lat", "lon", "point_count"]],
    hide_index=True,
    use_container_width=True,
)

section_title("高置信航段样例", "从动态边权表中抽取置信度较高、通行次数较多的航段，说明系统如何形成“经验航道”。")
edge_sample = edges.sort_values(["confidence", "planning_pass_count"], ascending=False).head(12)
st.dataframe(
    edge_sample[["start_node", "end_node", "distance_m", "planning_time_s", "planning_pass_count", "confidence"]],
    hide_index=True,
    use_container_width=True,
)

section_title("典型区域路线对比")
case_name = st.selectbox("选择案例区域", list(CASES), format_func=lambda item: f"{item} · {CASES[item]['caption']}")
summary = load_case_summary(case_name)
left, right = st.columns([0.42, 0.58])
with left:
    st.markdown(
        f"""
        <div class="soft-card">
          <div class="badge">案例解读</div>
          <h3>{case_name}</h3>
          <p>{case_interpretation(case_name)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with right:
    display = summary[["strategy", "nodes", "edges", "distance_km", "time_min", "avg_confidence", "low_confidence_pct"]]
    st.dataframe(display, hide_index=True, use_container_width=True)

section_title("页面设计意图")
st.markdown(
    """
    <div class="soft-card">
      <p>
      这类页面不要急着放满复杂控件。先用指标卡和案例解释建立“路网真实存在”的感觉，
      再让用户进入智能规划页查看算法如何沿着这张网络搜索。
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
