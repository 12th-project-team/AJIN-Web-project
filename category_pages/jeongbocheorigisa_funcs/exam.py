# category_pages/template_funcs/exam.py

import streamlit as st

def render(category_name: str):
    st.info(f"📄 기출문제 탭 - {category_name}")
