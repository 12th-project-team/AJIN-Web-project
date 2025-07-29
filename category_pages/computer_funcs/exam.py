import streamlit as st

def render(category_name: str):
    st.header(f"📄 {category_name} - 기출문제 모의 연습")

    st.markdown("""
    ### 기출문제 예시 목록
    - 2022년 1회: 함수와 셀 참조
    - 2023년 2회: 조건부 서식, 데이터 필터
    - 2024년 1회: 피벗테이블, 정렬 및 필터
    """)
