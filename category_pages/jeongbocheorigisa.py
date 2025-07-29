import streamlit as st
from category_pages import jeongbocheorigisa_funcs as funcs

def render():
    st.header("📘 정보처리기사")

    # 업로드 탭
    funcs.upload("정보처리기사")
    st.markdown("---")

    # 미리보기 탭
    funcs.preview("정보처리기사")
    st.markdown("---")

    # AI 탭
    tab1, tab2, tab3, tab4 = st.tabs(["요약","기출문제","퀴즈","챗봇"])
    with tab1: funcs.summary("정보처리기사")
    with tab2: funcs.exam("정보처리기사")
    with tab3: funcs.quiz("정보처리기사")
    with tab4: funcs.chatbot("정보처리기사")
