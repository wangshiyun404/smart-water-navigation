"""Dynamic edge weights overview page."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
LOCAL_DEPENDENCIES = PROJECT_DIR / ".vendor"
if LOCAL_DEPENDENCIES.exists():
    sys.path.insert(0, str(LOCAL_DEPENDENCIES))

import pandas as pd
import streamlit as st

from nav_core import load_weight_edges
from ui import hero, inject_global_css, metric_card, section_title


st.set_page_config(page_title="动态边权 | 智能水上导航系统", page_icon="📈", layout="wide")
inject_global_css()

hero(
    "动态边权：解释系统为什么推荐这条路",
    "路径规划不只是“连线最短”。系统会把距离、历史耗时、通行次数与置信度转化为航段权重，用于比较不同路线策略。",
    "距离 · 时间 · 通行次数 · 置信度",
)

edges = load_weight_edges()
stat_edges = edges[edges["has_stats"]].copy()

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("精细化统计边", f"{len(stat_edges):,}", "具有历史通行统计")
with c2:
    metric_card("有效通行次数", f"{int(edges['planning_pass_count'].sum()):,}", "交付权重文件汇总口径")
with c3:
    metric_card("平均置信度", f"{edges['confidence'].mean():.3f}", "越高表示历史证据越稳定")
with c4:
    metric_card("低置信航段", f"{(edges['confidence'].lt(0.4).mean() * 100):.1f}%", "低于 0.4 的边占比")

section_title("置信度分布", "把连续置信度转为分档，更适合课堂讲解和页面阅读。")
bins = pd.cut(
    edges["confidence"],
    bins=[-0.001, 0.4, 0.7, 1.001],
    labels=["低置信（<0.4）", "中等置信（0.4-0.7）", "较高置信（≥0.7）"],
)
confidence_frame = bins.value_counts().rename_axis("置信度分级").reset_index(name="航段数量")
st.bar_chart(confidence_frame.set_index("置信度分级"))

section_title("昼夜耗时样例", "筛选具有昼夜统计值的航段，观察同一航段在不同时段的耗时差异。")
day_night = stat_edges.dropna(subset=["day_time_s", "night_time_s"]).copy()
if day_night.empty:
    st.info("当前权重文件中没有可展示的昼夜耗时差异字段。")
else:
    day_night["昼夜耗时差_min"] = (day_night["night_time_s"] - day_night["day_time_s"]) / 60
    sample = day_night.reindex(day_night["昼夜耗时差_min"].abs().sort_values(ascending=False).index).head(12)
    st.dataframe(
        sample[["start_node", "end_node", "distance_m", "day_time_s", "night_time_s", "confidence", "昼夜耗时差_min"]],
        hide_index=True,
        use_container_width=True,
    )

section_title("如何讲给非技术同学")
st.markdown(
    """
    <div class="soft-card">
      <p>
      可以把每一条航段理解为一段“有经验记录的水上道路”：
      距离告诉我们走多远，时间告诉我们通常要多久，通行次数告诉我们证据多少，
      置信度告诉我们这段经验是否稳定。综合最优线路正是在这些因素之间做权衡。
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
