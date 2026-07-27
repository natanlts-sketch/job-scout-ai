from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_APP = Path(__file__).resolve().parents[1]
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from pathlib import Path

import streamlit as st

from auth_gate import require_user
from src.cv.upload import (
    add_user_skill,
    delete_active_cv,
    get_active_cv,
    get_user_skills,
    remove_user_skill,
    store_cv_upload,
)

user = require_user()
st.title("CV")

cv = get_active_cv(user["id"])
if cv:
    st.success(f"Active CV: {cv['filename']} · parse status: **{cv['parse_status']}**")
    if cv.get("parse_error"):
        st.error(cv["parse_error"])
    with st.expander("Extracted text preview"):
        st.text((cv.get("extracted_text") or "")[:3000])
else:
    st.info("No CV uploaded yet.")

uploaded = st.file_uploader("Upload CV (DOCX or PDF)", type=["docx", "pdf"])
if uploaded and st.button("Save CV", type="primary"):
    try:
        result = store_cv_upload(user["id"], uploaded.name, uploaded.getvalue())
        if result["parse_status"] == "success":
            st.success(f"Parsed OK — {len(result['skills'])} skills extracted.")
        else:
            st.error(f"Parse failed: {result['parse_error']}")
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))

skills = get_user_skills(user["id"])
st.subheader("Skills")
st.write(", ".join(skills) if skills else "No skills yet.")

col_a, col_b = st.columns(2)
with col_a:
    new_skill = st.text_input("Add skill")
    if st.button("Add") and new_skill:
        add_user_skill(user["id"], new_skill)
        st.rerun()
with col_b:
    if skills:
        to_remove = st.selectbox("Remove skill", skills)
        if st.button("Remove"):
            remove_user_skill(user["id"], to_remove)
            st.rerun()

if cv and st.button("Delete CV", type="secondary"):
    delete_active_cv(user["id"])
    st.rerun()

if cv and Path(cv["stored_path"]).exists():
    st.download_button(
        "Download current CV",
        data=Path(cv["stored_path"]).read_bytes(),
        file_name=cv["filename"],
    )
