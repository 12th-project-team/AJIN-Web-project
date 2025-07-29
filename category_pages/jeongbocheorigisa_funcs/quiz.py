# category_pages/template_funcs/quiz.py

import streamlit as st

def render(category_name: str):
    st.info(f"📝 퀴즈 탭 - {category_name}")
