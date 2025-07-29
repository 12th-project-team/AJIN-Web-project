# category_pages/template_funcs/summary.py

import streamlit as st

def render(category_name: str):
    st.info(f"📌 요약 탭 - {category_name}")
