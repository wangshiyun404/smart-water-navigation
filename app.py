"""Product-style landing page for the smart water navigation demo."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_DEPENDENCIES = PROJECT_DIR / ".vendor"
if LOCAL_DEPENDENCIES.exists():
    sys.path.insert(0, str(LOCAL_DEPENDENCIES))

import streamlit as st

from nav_core import CASES, case_interpretation, load_case_summary
from ui import feature_card, hero, inject_global_css, metric_card, section_title


st.set_page_config(
    page_title="项目总览 | 智能水上导航系统",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()

hero(
    "智能水上导航与路径规划系统",
    "把 AIS 轨迹清洗、航道拓扑、动态边权和多目标路径规划组织成一个可讲解、可演示、可导出的产品型原型，而不是单纯的数据分析页面。",
    "AIS 轨迹 · 航道网络 · 动态边权 · 多目标规划",
)

cta_col, note_col = st.columns([0.36, 0.64])
with cta_col:
    if st.button("进入智能规划工作台", type="primary", use_container_width=True):
        st.switch_page("pages/1_智能规划.py")
with note_col:
    st.markdown(
        '<div class="small-note">建议演示顺序：先在本页讲清楚“数据如何变成可解释航线”，再进入智能规划页进行起终点选取、路线比较和结果导出。</div>',
        unsafe_allow_html=True,
    )

m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_card("航道节点", "12,305", "由清洗后的轨迹点聚合得到")
with m2:
    metric_card("有向航道边", "47,826", "表达可通行方向与拓扑连接")
with m3:
    metric_card("精细化统计边", "30,106", "支撑航段耗时与置信度建模")
with m4:
    metric_card("权重建模事件", "241,224", "报告口径下的有效建模事件")

section_title(
    "核心功能入口",
    "把原来堆在一个页面里的内容拆成“看懂项目—检查数据—理解网络—解释权重—运行规划”的自然路径。",
)
f1, f2, f3 = st.columns(3)
with f1:
    feature_card("智能规划", "选择起点与终点，设置船舶约束，对比距离最短、时间最短和综合最优三类航线。", "主任务")
    st.page_link("pages/1_智能规划.py", label="打开智能规划", icon="🧭")
with f2:
    feature_card("航道网络", "从节点、边、区域案例和高频航段理解 AIS 轨迹如何转化为可搜索的航道网络。", "网络结构")
    st.page_link("pages/3_航道网络.py", label="查看航道网络", icon="🕸️")
with f3:
    feature_card("动态边权", "围绕时间、距离、通行次数与置信度解释系统为什么会推荐某一条路线。", "可解释性")
    st.page_link("pages/4_动态边权.py", label="查看动态边权", icon="📈")

section_title("从数据到决策的四步链路")
st.markdown(
    """
    <div class="chain">
      <div class="chain-step">
        <div class="chain-no">01</div>
        <h3>AIS 数据治理</h3>
        <p>对原始船舶轨迹进行清洗、平滑与异常处理，降低噪声点对航道抽取的干扰。</p>
      </div>
      <div class="chain-step">
        <div class="chain-no">02</div>
        <h3>航道拓扑构建</h3>
        <p>把连续轨迹转化为节点与有向边，保留通行方向和局部拓扑关系。</p>
      </div>
      <div class="chain-step">
        <div class="chain-no">03</div>
        <h3>动态边权建模</h3>
        <p>根据航段历史耗时、通行次数与置信度，为不同路线策略提供权重基础。</p>
      </div>
      <div class="chain-step">
        <div class="chain-no">04</div>
        <h3>多目标路径规划</h3>
        <p>在距离、时间和可靠性之间进行权衡，并输出可解释、可导出的路线结果。</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

section_title("典型案例如何讲解")
for case_name in CASES:
    case_meta = CASES[case_name]
    with st.container(border=True):
        left, right = st.columns([0.28, 0.72])
        with left:
            st.markdown(f"### {case_name}")
            st.caption(case_meta["caption"])
            st.markdown(f"**展示重点：**{case_meta['focus']}")
        with right:
            try:
                summary = load_case_summary(case_name)
                st.markdown(case_interpretation(case_name))
                st.dataframe(
                    summary[["strategy", "distance_km", "time_min", "avg_confidence", "low_confidence_pct"]],
                    hide_index=True,
                    use_container_width=True,
                )
            except FileNotFoundError as exc:
                st.info(
                    f"当前仓库没有找到 {case_name} 的案例路线 CSV 文件，已跳过案例表格。"
                    f"缺失信息：{exc}。这不影响数据治理、航道网络、动态边权等页面的展示。"
                )

section_title("演示边界")
st.markdown(
    """
    <div class="callout">
      <strong>重要说明：</strong>当前系统是课程作业与比赛展示原型，读取既有成果文件，不提供实时船舶在线导航。
      边表中的吃水和限高字段用于演示约束过滤机制，不能替代真实电子海图、桥梁净空、海事通告或现场调度决策。
    </div>
    """,
    unsafe_allow_html=True,
)
