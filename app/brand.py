"""Brand theme matching the Job Scout AI logo."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from i18n import get_lang, get_theme, set_lang, set_theme, t

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_PATH = ASSETS / "logo.png"

GREEN = "#39B54A"
GREEN_DARK = "#1B5E20"
GREEN_BRIGHT = "#7CFF3A"
CHARCOAL = "#1A1A1A"
SOFT_GRAY = "#F4F6F5"
MUTED = "#5C6670"

# Default Streamlit sidebar ~21rem → 30% thinner ≈ 14.7rem
SIDEBAR_WIDTH = "14.7rem"

PAGE_LINKS = [
    ("Home.py", "home_nav"),
    ("pages/1_דשבורד.py", "dashboard"),
    ("pages/2_קורות_חיים.py", "cv"),
    ("pages/3_חיפוש.py", "search"),
    ("pages/4_משרות.py", "jobs"),
    ("pages/5_מועמדויות.py", "applications"),
    ("pages/6_הגדרות.py", "settings"),
    ("pages/7_סטטיסטיקות.py", "statistics"),
]


def apply_brand_theme() -> None:
    rtl = get_lang() == "he"
    dark = get_theme() == "dark"
    direction = "rtl" if rtl else "ltr"
    text_align = "right" if rtl else "left"

    if dark:
        app_bg = (
            "radial-gradient(1200px 500px at 10% -10%, rgba(124,255,58,0.08), transparent 55%),"
            "radial-gradient(900px 400px at 100% 0%, rgba(57,181,74,0.08), transparent 50%),"
            "#0B1220"
        )
        text = "#E8EDF2"
        muted = "#9AA7B5"
        card_bg = "#141C2B"
        card_border = "rgba(124,255,58,0.16)"
        btn_border = "rgba(232,237,242,0.22)"
        btn_color = "#E8EDF2"
        metric_label = "#9AA7B5"
        top_btn_hover_bg = "rgba(239, 68, 68, 0.18)"
    else:
        app_bg = (
            "radial-gradient(1200px 500px at 10% -10%, rgba(124,255,58,0.12), transparent 55%),"
            "radial-gradient(900px 400px at 100% 0%, rgba(57,181,74,0.10), transparent 50%),"
            f"{SOFT_GRAY}"
        )
        text = CHARCOAL
        muted = MUTED
        card_bg = "#ffffff"
        card_border = "rgba(27,94,32,0.12)"
        btn_border = "rgba(26,26,26,0.2)"
        btn_color = CHARCOAL
        metric_label = MUTED
        top_btn_hover_bg = "rgba(239, 68, 68, 0.10)"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

        html, body, [class*="css"]  {{
          font-family: Manrope, "Segoe UI", sans-serif;
        }}

        .stApp {{
          background: {app_bg};
        }}

        .block-container {{
          padding-top: 0.85rem;
          max-width: 1100px;
        }}

        h1, h2, h3 {{
          color: {text} !important;
          letter-spacing: -0.03em;
          font-weight: 800 !important;
        }}

        p, label, .stMarkdown, .stCaption, .stText, span {{
          color: {text};
        }}

        /* Sidebar 30% thinner — custom bilingual nav */
        section[data-testid="stSidebar"] {{
          background: linear-gradient(180deg, {CHARCOAL} 0%, #111827 55%, #0b1220 100%);
          border-right: 1px solid rgba(124,255,58,0.18);
          width: {SIDEBAR_WIDTH} !important;
          min-width: {SIDEBAR_WIDTH} !important;
          max-width: {SIDEBAR_WIDTH} !important;
        }}
        section[data-testid="stSidebar"] > div {{
          width: {SIDEBAR_WIDTH} !important;
          min-width: {SIDEBAR_WIDTH} !important;
          max-width: {SIDEBAR_WIDTH} !important;
        }}
        [data-testid="stSidebar"] * {{
          color: #F3F4F6 !important;
        }}
        [data-testid="stSidebar"] a:hover {{
          color: {GREEN_BRIGHT} !important;
        }}
        /* Hide Streamlit auto page names (always Hebrew filenames) */
        [data-testid="stSidebarNav"] {{
          display: none !important;
        }}
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
          border-radius: 8px;
          padding: 0.35rem 0.55rem;
          margin-bottom: 0.15rem;
        }}
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{
          background: rgba(124,255,58,0.12);
        }}

        /* Top bar — no white panel */
        div[data-testid="stHorizontalBlock"]:has(.top-controls-marker) {{
          background: transparent !important;
          border: 0 !important;
          border-radius: 0 !important;
          padding: 0.15rem 0 0.55rem 0;
          margin-bottom: 0.55rem;
          align-items: center;
        }}
        .top-controls-marker {{ display: none; }}
        .top-user-line {{
          margin: 0.35rem 0 !important;
          font-size: 0.95rem;
          color: {text} !important;
          font-weight: 600;
        }}

        /* Transparent logo, no green frame */
        [data-testid="stImage"],
        [data-testid="stImage"] img {{
          background: transparent !important;
          border: 0 !important;
          padding: 0 !important;
          box-shadow: none !important;
        }}

        /* Compact top-bar controls */
        div[data-testid="stHorizontalBlock"]:has(.top-controls-marker) div.stButton > button {{
          background: transparent !important;
          border: 1px solid {btn_border} !important;
          color: {btn_color} !important;
          font-weight: 700 !important;
          border-radius: 999px !important;
          padding: 0.35rem 0.55rem !important;
          box-shadow: none !important;
          font-size: 0.8rem !important;
          min-height: 2.1rem !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(.top-controls-marker)
          div[data-testid="column"]:last-child div.stButton > button.logout-ish:hover,
        div[data-testid="stHorizontalBlock"]:has(.top-user-line)
          div[data-testid="column"]:last-child div.stButton > button:hover {{
          background: {top_btn_hover_bg} !important;
          border-color: rgba(220, 38, 38, 0.45) !important;
          color: #FCA5A5 !important;
        }}

        div.stButton > button[kind="primary"],
        div.stButton > button[data-testid="baseButton-primary"] {{
          background: {GREEN};
          color: #ffffff;
          border: 0;
          font-weight: 700;
          border-radius: 10px;
        }}
        div.stButton > button[kind="primary"]:hover {{
          background: {GREEN_DARK};
          color: #ffffff;
        }}
        div.stButton > button {{
          border-radius: 10px;
          border: 1px solid rgba(57,181,74,0.35);
          color: {btn_color};
          font-weight: 600;
        }}

        [data-testid="stMetric"] {{
          background: {card_bg};
          border: 1px solid {card_border};
          border-radius: 14px;
          padding: 0.75rem 1rem;
        }}
        [data-testid="stMetricLabel"] {{ color: {metric_label} !important; }}
        [data-testid="stMetricValue"] {{ color: {text} !important; }}

        div[data-baseweb="tab-list"] {{ gap: 0.35rem; background: transparent; }}
        button[data-baseweb="tab"] {{
          border-radius: 999px !important;
          font-weight: 700;
          color: {text} !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
          background: rgba(57,181,74,0.15) !important;
          color: {GREEN_BRIGHT if dark else GREEN_DARK} !important;
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
          color: {muted};
          font-weight: 600;
        }}
        .brand-caption {{
          margin: 0.15rem 0 0 0;
          color: {muted};
          font-size: 0.95rem;
        }}
        .brand-divider {{
          height: 3px;
          width: 84px;
          border-radius: 999px;
          background: linear-gradient(90deg, {GREEN_DARK}, {GREEN_BRIGHT});
          margin: 0.55rem 0 0.9rem 0;
        }}

        [data-testid="InputInstructions"] {{ display: none !important; }}

        .block-container, [data-testid="stMarkdownContainer"], label, p, h1, h2, h3 {{
          direction: {direction};
          text-align: {text_align};
        }}

        /* Dark-mode form controls */
        {"div[data-baseweb='input'] > div, div[data-baseweb='select'] > div, textarea, .stTextInput input, .stTextArea textarea { background: #141C2B !important; color: #E8EDF2 !important; border-color: rgba(124,255,58,0.22) !important; }" if dark else ""}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_logo(width: int = 320) -> None:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=width)
    else:
        st.markdown(f"**{t('app_title')}**")


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


def render_sidebar_nav() -> None:
    """Custom sidebar labels that follow EN/HE (default Streamlit nav uses Hebrew filenames)."""
    with st.sidebar:
        for path, key in PAGE_LINKS:
            st.page_link(path, label=t(key))


def render_guest_controls(*, key_prefix: str = "guest") -> None:
    """Lang + dark mode for the login screen."""
    apply_brand_theme()
    _, lang_col, theme_col = st.columns([6.5, 0.8, 1.0])
    with lang_col:
        st.markdown('<span class="top-controls-marker"></span>', unsafe_allow_html=True)
        _lang_toggle(f"{key_prefix}_lang")
    with theme_col:
        _theme_toggle(f"{key_prefix}_theme")


def render_top_bar(*, user_label: str, logout_key: str = "top_logout") -> bool:
    """Top menu: logo | signed-in | EN/HE | dark | logout."""
    apply_brand_theme()
    render_sidebar_nav()
    left, mid, lang_col, theme_col, out = st.columns([2.0, 3.0, 0.7, 0.95, 1.25])
    with left:
        render_logo(width=170)
    with mid:
        st.markdown(
            f'<span class="top-controls-marker"></span>'
            f'<p class="top-user-line">{t("signed_in_as")} <strong>{user_label}</strong></p>',
            unsafe_allow_html=True,
        )
    with lang_col:
        _lang_toggle(f"{logout_key}_lang")
    with theme_col:
        _theme_toggle(f"{logout_key}_theme")
    with out:
        return st.button(t("log_out"), key=logout_key, use_container_width=True)
    return False


def _lang_toggle(key: str) -> None:
    label = "EN" if get_lang() == "he" else "HE"
    if st.button(label, key=key, use_container_width=True, help=t("ui_language")):
        set_lang("en" if get_lang() == "he" else "he")
        st.rerun()


def _theme_toggle(key: str) -> None:
    dark = get_theme() == "dark"
    label = t("theme_light") if dark else t("theme_dark")
    if st.button(label, key=key, use_container_width=True, help=t("theme_toggle")):
        set_theme("light" if dark else "dark")
        st.rerun()
