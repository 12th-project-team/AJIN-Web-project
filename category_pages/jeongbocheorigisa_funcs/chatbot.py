# category_pages/template_funcs/chatbot.py

import streamlit as st

def render(category_name: str):
    st.info(f"🤖 챗봇 탭 - {category_name}")
