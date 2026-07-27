from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_APP = Path(__file__).resolve().parents[1]
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

import streamlit as st

from src.streamlit_ui.auth_gate import require_user
from src.streamlit_ui.i18n import t
from src.cv.upload import (
    add_user_skill,
    delete_active_cv,
    get_active_cv,
    get_user_skills,
    remove_user_skill,
    store_cv_upload,
)

user = require_user()
st.title(t("cv"))

cv = get_active_cv(user["id"])
if cv:
    st.success(
        f"{t('active_cv')}: {cv['filename']} · {t('parse_status')}: **{cv['parse_status']}**"
    )
    if cv.get("parse_error"):
        st.error(cv["parse_error"])
    with st.expander(t("extracted_preview")):
        st.text((cv.get("extracted_text") or "")[:3000])
else:
    st.info(t("no_cv"))

uploaded = st.file_uploader(t("upload_cv"), type=["docx", "pdf"])
if uploaded and st.button(t("save_cv"), type="primary"):
    try:
        result = store_cv_upload(user["id"], uploaded.name, uploaded.getvalue())
        if result["parse_status"] == "success":
            st.success(t("parsed_ok", n=len(result["skills"])))
        else:
            st.error(f"{t('parse_failed')}: {result['parse_error']}")
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))

skills = get_user_skills(user["id"])
st.subheader(t("skills"))
st.write(", ".join(skills) if skills else t("no_skills"))

col_a, col_b = st.columns(2)
with col_a:
    new_skill = st.text_input(t("add_skill"))
    if st.button(t("add")) and new_skill:
        add_user_skill(user["id"], new_skill)
        st.rerun()
with col_b:
    if skills:
        to_remove = st.selectbox(t("remove_skill"), skills)
        if st.button(t("remove")):
            remove_user_skill(user["id"], to_remove)
            st.rerun()

if cv and st.button(t("delete_cv"), type="secondary"):
    delete_active_cv(user["id"])
    st.rerun()

if cv and Path(cv["stored_path"]).exists():
    st.download_button(
        t("download_cv"),
        data=Path(cv["stored_path"]).read_bytes(),
        file_name=cv["filename"],
    )
