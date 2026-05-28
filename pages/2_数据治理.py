"""Data-governance explainer page."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
LOCAL_DEPENDENCIES = PROJECT_DIR / ".vendor"
if LOCAL_DEPENDENCIES.exists():
    sys.path.insert(0, str(LOCAL_DEPENDENCIES))

import streamlit as st

from ui import feature_card, hero, inject_global_css, metric_card, section_title


st.set_page_config(page_title="数据治理 | 智能水上导航系统", page_icon="🧹", layout="wide")
inject_global_css()

hero(
    "数据治理：让轨迹数据变成可用航道",
    "这一页用于向评委或同学解释：系统不是直接把坐标点画在地图上，而是先经过清洗、平滑、抽取和统计，才进入路径规划。",
    "清洗 · 平滑 · 聚合 · 质控",
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("治理目标", "降噪", "减少异常点与轨迹漂移")
with c2:
    metric_card("网络产物", "节点 / 边", "为算法搜索提供结构")
with c3:
    metric_card("统计产物", "耗时 / 置信度", "为边权建模提供依据")
with c4:
    metric_card("展示定位", "可解释", "帮助用户理解推荐原因")

section_title("治理流程")
steps = [
    ("原始 AIS 轨迹接入", "统一时间、经纬度、航速、航向等字段口径，剔除明显缺失与越界记录。", "01"),
    ("轨迹清洗与平滑", "处理异常跳点、重复点和局部噪声，让航迹更接近真实通行路径。", "02"),
    ("航道节点与边抽取", "把连续轨迹转化为节点与有向边，保留通行方向和局部拓扑关系。", "03"),
    ("航段统计与质量标注", "统计航段距离、耗时、通行次数和置信度，为后续路线推荐提供依据。", "04"),
]
cols = st.columns(4)
for col, (title, body, tag) in zip(cols, steps):
    with col:
        feature_card(title, body, tag)

section_title("课堂展示建议")
st.markdown(
    """
    <div class="soft-card">
      <h3>讲解重点</h3>
      <p>
      不要只说“我们做了数据清洗”，而要说明数据治理对导航结果的影响：
      如果轨迹噪声没有处理，航道边会被错误连接；如果通行次数和置信度没有统计，
      系统就只能给出几何最短路线，无法解释哪条路线更稳健。
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

section_title("可以继续补充的材料")
st.info("如果后续补充清洗前后对比图、卡尔曼滤波效果图或异常点示意图，这一页会更有说服力。")
