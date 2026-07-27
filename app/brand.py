"""Brand theme matching the Job Scout AI logo."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from i18n import get_lang, t

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_PATH = ASSETS / "logo.png"

# Logo palette
GREEN = "#39B54A"
GREEN_DARK = "#1B5E20"
GREEN_BRIGHT = "#7CFF3A"
CHARCOAL = "#1A1A1A"
SOFT_GRAY = "#F4F6F5"
MUTED = "#5C6670"


def apply_brand_theme() -> None:
    rtl = get_lang() == "he"
    direction = "rtl" if rtl else "ltr"
    text_align = "right" if rtl else "left"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

        html, body, [class*="css"]  {{
          font-family: Manrope, "Segoe UI", sans-serif;
        }}

        .stApp {{
          background:
            radial-gradient(1200px 500px at 10% -10%, rgba(124,255,58,0.12), transparent 55%),
            radial-gradient(900px 400px at 100% 0%, rgba(57,181,74,0.10), transparent 50%),
            {SOFT_GRAY};
        }}

        .block-container {{
          padding-top: 1.4rem;
          max-width: 1100px;
        }}

        h1, h2, h3 {{
          color: {CHARCOAL} !important;
          letter-spacing: -0.03em;
          font-weight: 800 !important;
        }}

        p, label, .stMarkdown, .stCaption {{
          color: {CHARCOAL};
        }}

        [data-testid="stSidebar"] {{
          background: linear-gradient(180deg, {CHARCOAL} 0%, #111827 55%, #0b1220 100%);
          border-right: 1px solid rgba(124,255,58,0.18);
        }}
        [data-testid="stSidebar"] * {{
          color: #F3F4F6 !important;
        }}
        [data-testid="stSidebar"] a:hover {{
          color: {GREEN_BRIGHT} !important;
        }}

        div.stButton > button[kind="primary"],
        div.stButton > button[data-testid="baseButton-primary"] {{
          background: linear-gradient(90deg, {GREEN_DARK}, {GREEN}, {GREEN_BRIGHT});
          color: {CHARCOAL};
          border: 0;
          font-weight: 700;
          border-radius: 10px;
        }}
        div.stButton > button[kind="primary"]:hover {{
          filter: brightness(1.05);
          color: {CHARCOAL};
        }}
        div.stButton > button {{
          border-radius: 10px;
          border: 1px solid rgba(57,181,74,0.35);
          color: {CHARCOAL};
          font-weight: 600;
        }}

        [data-testid="stMetric"] {{
          background: white;
          border: 1px solid rgba(27,94,32,0.12);
          border-radius: 14px;
          padding: 0.75rem 1rem;
          box-shadow: none;
        }}
        [data-testid="stMetricLabel"] {{
          color: {MUTED} !important;
        }}
        [data-testid="stMetricValue"] {{
          color: {CHARCOAL} !important;
        }}

        div[data-baseweb="tab-list"] {{
          gap: 0.35rem;
          background: transparent;
        }}
        button[data-baseweb="tab"] {{
          border-radius: 999px !important;
          font-weight: 700;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
          background: rgba(57,181,74,0.15) !important;
          color: {GREEN_DARK} !important;
        }}

        .brand-hero {{
          display: flex;
          flex-direction: column;
          align-items: {"flex-end" if rtl else "flex-start"};
          gap: 0.35rem;
          margin-bottom: 1.25rem;
          direction: {direction};
          text-align: {text_align};
        }}
        .brand-tagline {{
          margin: 0;
          font-size: 0.78rem;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: {MUTED};
          font-weight: 600;
        }}
        .brand-caption {{
          margin: 0.15rem 0 0 0;
          color: {MUTED};
          font-size: 0.95rem;
        }}
        .brand-card {{
          background: #ffffff;
          border: 1px solid rgba(27,94,32,0.12);
          border-radius: 18px;
          padding: 1.25rem 1.35rem 1.4rem;
        }}
        .brand-divider {{
          height: 3px;
          width: 84px;
          border-radius: 999px;
          background: linear-gradient(90deg, {GREEN_DARK}, {GREEN_BRIGHT});
          margin: 0.55rem 0 0.9rem 0;
        }}

        /* Force readable content direction for HE */
        .block-container, [data-testid="stMarkdownContainer"], label, p, h1, h2, h3 {{
          direction: {direction};
          text-align: {text_align};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_logo(width: int = 320) -> None:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=width)


def render_brand_header(*, show_caption: bool = True, width: int = 340) -> None:
    apply_brand_theme()
    st.markdown('<div class="brand-hero">', unsafe_allow_html=True)
    render_logo(width=width)
    st.markdown(
        f'<p class="brand-tagline">{t("brand_tagline")}</p>',
        unsafe_allow_html=True,
    )
    if show_caption:
        st.markdown(
            f'<p class="brand-caption">{t("app_caption")}</p>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="brand-divider"></div></div>', unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.markdown(f"**{t('app_title')}**")
        st.caption(t("brand_tagline"))
