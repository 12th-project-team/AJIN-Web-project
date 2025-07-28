# main_app.py
import streamlit as st
from category_pages import computer, info, word, itq, office

CATEGORIES = {
    "컴퓨터활용능력": computer.render,
    "정보처리": info.render,
    "워드프로세서": word.render,
    "ITQ/GTQ": itq.render,
    "사무자동화": office.render,
}

if "selected_category" not in st.session_state:
    st.session_state.selected_category = list(CATEGORIES.keys())[0]

st.title("📚 자격증 문서 기반 AI 학습 플랫폼")

st.markdown("### 📂 카테고리를 선택하세요")
cols = st.columns(len(CATEGORIES), gap="small")

for i, (cat_name, _) in enumerate(CATEGORIES.items()):
    with cols[i]:
        color = "red" if st.session_state.selected_category == cat_name else "gray"
        if st.button(f"**:{color}[{cat_name}]**"):
            st.session_state.selected_category = cat_name

st.markdown("---")
CATEGORIES[st.session_state.selected_category]()