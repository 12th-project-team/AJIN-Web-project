import os
import json
import streamlit as st
from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from vectorstore_utils import save_exam_questions, load_exam_questions

# ————————————
# 1) PDF 업로드 → 문제 추출 → 벡터스토어 저장
# ————————————

def ingest_exam_pdf(category_name: str):
    st.subheader("📤 기출문제 PDF 업로드 및 인제스트")
    uploaded_file = st.file_uploader(
        "🗂️ 객관식 문제 PDF 업로드",
        type=["pdf"],
        key=f"exam_upload_{category_name}"
    )
    if not uploaded_file:
        return

    if st.button("🚀 문제 추출 및 저장 시작", key=f"exam_ingest_btn_{category_name}"):
        with st.spinner("⏳ PDF 분석 중... 잠시만 기다려주세요."):
            # 1) PDF 로드
            loader = PyPDFLoader(uploaded_file)
            pages: List[Document] = loader.load_and_split()  # 페이지별 Document

            # 2) OpenAI로 문제·보기·정답·해설 파싱
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
            prompt = PromptTemplate(
                input_variables=["page_content"],
                template="""
아래는 시험지의 한 페이지 내용입니다. 
이 중 객관식 문제(문제 번호, 보기 4개, 정답 번호, 해설)를 JSON 리스트 형태로 뽑아 주세요.
반드시 다음 형태로만 응답하세요:

[
  {{
    "question": "...",
    "choices": ["...", "...", "...", "..."],
    "answer": 2,         # 정답 보기의 인덱스(1~4)
    "explanation": "..."
  }},
  ... 
]

페이지 내용:
{page_content}
"""
            )
            all_items: List[Dict] = []
            for doc in pages:
                res = llm.invoke(prompt.format(page_content=doc.page_content))
                # GPT 응답을 JSON으로 변환
                items = json.loads(res.content)
                for itm in items:
                    itm["page"] = doc.metadata.get("page", None)
                all_items.extend(items)

            if not all_items:
                st.error("❌ 문제를 추출하지 못했습니다.")
                return

            # 3) 벡터스토어에 저장
            save_path = save_exam_questions(category_name, all_items)
            st.success(f"✅ {len(all_items)}문제 저장 완료: {save_path}")

# ————————————
# 2) 저장된 문제 불러와서 시험 응시 UI
# ————————————

def render(category_name: str):
    st.header(f"🖋️ {category_name} 기출문제 응시")

    # ingestion UI
    ingest_exam_pdf(category_name)
    st.markdown("---")

    # DB에서 불러오기
    questions = load_exam_questions(category_name)
    if not questions:
        st.info("❗ 아직 저장된 기출문제가 없습니다. PDF를 업로드 후 저장하세요.")
        return

    # 시험 시작 버튼
    if "exam_started" not in st.session_state:
        if st.button("▶️ 시험 시작"):
            st.session_state.exam_started = True
            st.session_state.current = 0
            st.session_state.user_answers = {}
        else:
            return

    # 시험 진행
    total = len(questions)
    idx = st.session_state.current
    q = questions[idx]

    st.markdown(f"**문제 {idx+1}/{total} (페이지 {q.get('page','-')})**")
    st.write(q["question"])
    choice = st.radio(
        "보기 선택",
        q["choices"],
        key=f"exam_choice_{idx}"
    )
    st.session_state.user_answers[idx] = q["choices"].index(choice) + 1

    col1, col2 = st.columns(2)
    with col1:
        if idx > 0:
            if st.button("◀️ 이전 문제"):
                st.session_state.current -= 1
    with col2:
        if idx < total - 1:
            if st.button("다음 문제 ▶️"):
                st.session_state.current += 1
        else:
            if st.button("✅ 시험 제출"):
                st.session_state.completed = True

    # 채점 & 해설
    if st.session_state.get("completed", False):
        score = sum(
            1 for i, q in enumerate(questions)
            if st.session_state.user_answers.get(i) == q["answer"]
        )
        pct = int(score / total * 100)
        st.success(f"🎉 점수: {score}/{total} ({pct}점)")
        with st.expander("🔍 해설 보기"):
            for i, q in enumerate(questions):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                st.markdown(f"- 정답: {q['choices'][q['answer']-1]}")
                st.markdown(f"- 해설: {q['explanation']}")
        # 초기화
        if st.button("🔄 다시 보기"):
            for k in ["exam_started","user_answers","current","completed"]:
                st.session_state.pop(k, None)
            st.experimental_rerun()
