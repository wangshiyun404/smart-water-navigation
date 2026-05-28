"""Reusable UI helpers for the Streamlit product shell."""

from __future__ import annotations

from html import escape
from pathlib import Path
import sys

import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_DEPENDENCIES = PROJECT_DIR / ".vendor"
if LOCAL_DEPENDENCIES.exists():
    sys.path.insert(0, str(LOCAL_DEPENDENCIES))


def inject_global_css() -> None:
    """Apply a lightweight product-style design system on top of Streamlit."""
    st.markdown(
        """
        <style>
          :root {
            --brand: #155EEF;
            --brand-dark: #0B3D91;
            --water: #168AAD;
            --aqua: #EAFBFF;
            --page: #F6FAFC;
            --card: #FFFFFF;
            --ink: #0B2239;
            --muted: #52667A;
            --soft: #EFF6FB;
            --line: #D8E7EE;
            --warning: #F59E0B;
            --success: #1B998B;
            --shadow: 0 18px 45px rgba(15, 71, 97, .10);
          }

          .stApp {
            background:
              radial-gradient(circle at 5% 5%, rgba(21, 94, 239, .08), transparent 28rem),
              radial-gradient(circle at 95% 2%, rgba(22, 138, 173, .10), transparent 24rem),
              var(--page);
          }

          .block-container {
            max-width: 1280px;
            padding-top: 1.6rem;
            padding-bottom: 3rem;
          }

          section[data-testid="stSidebar"] {
            background: #EEF7FA;
            border-right: 1px solid var(--line);
          }

          h1, h2, h3 {
            color: var(--ink);
            letter-spacing: -.02em;
          }

          p, li, div {
            font-family: "Inter", "SF Pro Display", "Microsoft YaHei", "PingFang SC", sans-serif;
          }

          .hero {
            padding: 2.25rem 2.35rem;
            border-radius: 30px;
            background:
              radial-gradient(circle at top left, rgba(21, 94, 239, .18), transparent 34%),
              linear-gradient(135deg, #FFFFFF 0%, #F0FAFF 100%);
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
            margin-bottom: 1.4rem;
          }

          .hero h1 {
            font-size: clamp(2rem, 4vw, 3.15rem);
            line-height: 1.08;
            margin: .45rem 0 .7rem;
            font-weight: 850;
          }

          .hero p {
            color: var(--muted);
            font-size: 1.06rem;
            line-height: 1.75;
            max-width: 760px;
            margin: 0;
          }

          .hero-actions {
            display: flex;
            gap: .75rem;
            flex-wrap: wrap;
            margin-top: 1.25rem;
          }

          .badge {
            display: inline-flex;
            align-items: center;
            gap: .35rem;
            padding: .32rem .72rem;
            border-radius: 999px;
            background: #EAF3FF;
            color: var(--brand);
            font-size: .78rem;
            font-weight: 800;
          }

          .soft-card {
            min-height: 100%;
            padding: 1.12rem 1.16rem;
            border-radius: 24px;
            background: var(--card);
            border: 1px solid var(--line);
            box-shadow: 0 12px 28px rgba(15, 71, 97, .075);
          }

          .soft-card h3 {
            font-size: 1.04rem;
            margin: .25rem 0 .38rem;
          }

          .soft-card p {
            color: var(--muted);
            font-size: .91rem;
            line-height: 1.65;
            margin: 0;
          }

          .metric-card {
            padding: 1.05rem 1.15rem;
            border-radius: 24px;
            background: linear-gradient(180deg, #FFFFFF 0%, #F7FBFF 100%);
            border: 1px solid var(--line);
            box-shadow: 0 12px 26px rgba(15, 71, 97, .07);
          }

          .metric-label {
            color: var(--muted);
            font-size: .78rem;
            font-weight: 800;
            margin-bottom: .25rem;
          }

          .metric-value {
            color: var(--ink);
            font-size: 1.75rem;
            line-height: 1.15;
            font-weight: 900;
            font-variant-numeric: tabular-nums;
          }

          .metric-caption {
            color: #7A8A99;
            font-size: .78rem;
            margin-top: .28rem;
          }

          .section-title {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 1rem;
            margin: 1.6rem 0 .8rem;
          }

          .section-title h2 {
            margin: 0;
            font-size: 1.38rem;
          }

          .section-title p {
            margin: .22rem 0 0;
            color: var(--muted);
            line-height: 1.65;
          }

          .chain {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .9rem;
          }

          .chain-step {
            position: relative;
            padding: 1rem;
            border-radius: 22px;
            background: #FFFFFF;
            border: 1px solid var(--line);
            box-shadow: 0 10px 24px rgba(15, 71, 97, .06);
          }

          .chain-no {
            width: 2rem;
            height: 2rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: .75rem;
            background: #EAF3FF;
            color: var(--brand);
            font-weight: 900;
            margin-bottom: .55rem;
          }

          .chain-step h3 {
            font-size: 1rem;
            margin: 0 0 .32rem;
          }

          .chain-step p {
            margin: 0;
            color: var(--muted);
            line-height: 1.6;
            font-size: .88rem;
          }

          .callout {
            border-radius: 24px;
            padding: 1rem 1.12rem;
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            color: #7A4D00;
            line-height: 1.72;
            margin: .8rem 0;
          }

          .callout strong {
            color: #653D00;
          }

          .link-card {
            transition: transform .15s ease, box-shadow .15s ease;
          }

          .link-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 34px rgba(15, 71, 97, .12);
          }

          .small-note {
            color: var(--muted);
            font-size: .86rem;
            line-height: 1.7;
          }

          iframe {
            border-radius: 22px;
          }

          div[data-testid="stButton"] button[kind="primary"] {
            background: var(--brand);
            border-color: var(--brand);
            border-radius: 14px;
            font-weight: 800;
          }

          div[data-testid="stButton"] button[kind="secondary"] {
            border-radius: 14px;
          }

          @media (max-width: 900px) {
            .chain { grid-template-columns: 1fr; }
            .section-title { display: block; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, badge: str = "") -> None:
    badge_html = f'<div class="badge">{escape(badge)}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="hero">
          {badge_html}
          <h1>{escape(title)}</h1>
          <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{escape(label)}</div>
          <div class="metric-value">{escape(value)}</div>
          <div class="metric-caption">{escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_card(title: str, body: str, tag: str = "") -> None:
    tag_html = f'<div class="badge">{escape(tag)}</div>' if tag else ""
    st.markdown(
        f"""
        <div class="soft-card link-card">
          {tag_html}
          <h3>{escape(title)}</h3>
          <p>{escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, body: str = "") -> None:
    body_html = f"<p>{escape(body)}</p>" if body else ""
    st.markdown(
        f"""
        <div class="section-title">
          <div>
            <h2>{escape(title)}</h2>
            {body_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def callout(body: str) -> None:
    st.markdown(f'<div class="callout">{body}</div>', unsafe_allow_html=True)
