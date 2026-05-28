"""Project boundary and presentation notes page."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
LOCAL_DEPENDENCIES = PROJECT_DIR / ".vendor"
if LOCAL_DEPENDENCIES.exists():
    sys.path.insert(0, str(LOCAL_DEPENDENCIES))

import streamlit as st

from ui import feature_card, hero, inject_global_css, section_title


st.set_page_config(page_title="说明与边界 | 智能水上导航系统", page_icon="ℹ️", layout="wide")
inject_global_css()

hero(
    "说明与边界：让展示更可信",
    "一个好的课程项目页面，不仅要展示功能，也要清楚说明数据口径、适用场景和不能替代的真实决策环节。",
    "数据口径 · 约束说明 · 展示建议",
)

section_title("需要主动说明的边界")
c1, c2, c3 = st.columns(3)
with c1:
    feature_card("非实时导航", "本应用读取既有成果文件，不接入实时船舶 AIS 数据，也不提供在线航行指挥。", "边界 01")
with c2:
    feature_card("约束字段为机制演示", "吃水和限高字段用于展示约束过滤逻辑，不能替代真实水深、桥梁净空或海图信息。", "边界 02")
with c3:
    feature_card("路线需要人工复核", "低置信航段、异常耗时和实际航行条件仍需结合海事通告与专业判断。", "边界 03")

section_title("比赛或课堂讲解话术")
st.markdown(
    """
    <div class="soft-card">
      <h3>建议表述</h3>
      <p>
      “本系统的目标不是替代真实船舶导航，而是展示如何把 AIS 轨迹数据转化为可解释的航道网络和路径规划原型。
      因此，我们特别标注了低置信航段、约束字段口径和数据边界，让用户知道结果从哪里来，也知道结果不能被怎样使用。”
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

section_title("后续优化清单")
st.markdown(
    """
    <div class="soft-card">
      <p>
      1. 为数据治理页补充清洗前后对比图。<br>
      2. 为航道网络页增加区域地图快照或高频边可视化。<br>
      3. 为动态边权页增加鼠标悬停解释卡。<br>
      4. 在智能规划页增加“为什么推荐该路线”的自然语言解释模板。<br>
      5. 部署后在 README 中加入 Streamlit Cloud 或 GitHub Pages 的访问说明。
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
