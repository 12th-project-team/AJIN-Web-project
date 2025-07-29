import streamlit as st
from langchain_openai import ChatOpenAI
from vectorstore_utils import load_chroma_vectorstore
import os
import re

CATEGORY_NAME = "컴퓨터활용능력"

def build_context_from_docs(docs, max_length=8000):
    context = ""
    for doc in docs:
        if len(context) + len(doc.page_content) > max_length:
            break
        context += doc.page_content + "\n"
    return context

def generate_quiz(llm, context, topic):
    prompt = f"""
너는 컴퓨터활용능력 자격시험의 객관식 문제 출제자야.

아래 조건을 모두 반드시 지켜서 문제를 출제해:

1. 반드시 '{topic}'와 직접적으로 연관된 내용(컴퓨터의 분류, 종류별 특징/정의/차이/예시/적용 등)만 활용해서 문제를 낸다.
2. 컴퓨터 분류와 상관없는 내용(컴퓨터 부품, 보안, 하드웨어/소프트웨어 관리, 파티션 등)은 출제하지 않는다.
3. 매번 새로운 문제, 보기, 정답, 예시, 설명으로 구성한다. (과거 출제한 문제, 보기, 설명과 중복 금지)
4. 문제, 보기, 예시, 정답, 해설 모두 무작위로 다양하게 섞어 구성한다.
5. 각 문제는 반드시 아래 형식으로 10개 연속 출력한다.

문제 1
문제 내용 (반드시 컴퓨터 분류와 직접적 연관! 예: "다음 중 아날로그 컴퓨터의 특징은?", "슈퍼컴퓨터와 마이크로컴퓨터의 차이점은?" 등)
1. 보기1 (항상 의미 있는 보기 작성)
2. 보기2 (항상 의미 있는 보기 작성)
3. 보기3 (항상 의미 있는 보기 작성)
4. 보기4 (항상 의미 있는 보기 작성)
정답: 번호. 보기 내용
해설:
- 정답: 왜 이 보기가 정답인지 구체적으로 설명하고, 가능한 실용적/실제 예시도 추가해라.
- 오답: 각각 왜 오답인지 1~2문장씩 근거를 명확히 제시해라.

{context}
"""
    return llm.invoke(prompt)

def parse_quiz(text):
    blocks = re.findall(r"문제 \d+\n(.+?)(?=문제 \d+|$)", text, re.DOTALL)
    parsed = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 6:
            continue
        q = lines[0]
        choices = lines[1:5]
        # 항상 4지선다 보장
        while len(choices) < 4:
            choices.append("보기 없음")
        answer_line = next((l for l in lines if l.startswith("정답")), "")
        answer_num = int(re.search(r"정답: (\d+)", answer_line).group(1)) if "정답" in answer_line else -1
        explanation_index = next((i for i, l in enumerate(lines) if l.startswith("해설")), None)
        explanation = "\n".join(lines[explanation_index:]).split("해설: ")[-1].strip() if explanation_index is not None else ""
        parsed.append({"question": q, "choices": choices, "answer": answer_num, "explanation": explanation})
    return parsed

def render():
    st.header(f"📝 {CATEGORY_NAME} - 객관식 퀴즈 풀기")

    base_path = os.path.join("chroma_db", CATEGORY_NAME)
    if not os.path.exists(base_path):
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    subfolders = os.listdir(base_path)
    if not subfolders:
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    # 초기 화면: 세션 상태가 없으면(퀴즈 시작 전)
    if "quiz" not in st.session_state:
        selected_doc = st.selectbox("퀴즈를 생성할 문서를 선택하세요", subfolders)
        query = st.text_input("퀴즈 생성 주제를 입력하세요:", placeholder="예) 함수, IF, 논리연산자 등")
        if st.button("퀴즈 생성 및 풀기") and query:
            try:
                vectordb = load_chroma_vectorstore(CATEGORY_NAME, selected_doc)
                retriever = vectordb.as_retriever(search_kwargs={"k": 15})
                llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.4)
                docs = retriever.get_relevant_documents(query)
                context = build_context_from_docs(docs)
                with st.spinner("📝 퀴즈를 생성 중입니다..."):
                    response = generate_quiz(llm, context, query)  # <-- query가 topic 역할
                    quiz_list = parse_quiz(response.content if hasattr(response, "content") else response)
                st.session_state.quiz = quiz_list
                st.session_state.answers = {}
                st.session_state.incorrect = []
                st.session_state.submitted = False
            except Exception as e:
                st.error(f"퀴즈 생성 중 오류 발생: {e}")
        return

    # 퀴즈 풀이 화면
    if not st.session_state.get("submitted", False):
        score = 0
        with st.form("quiz_form"):
            for idx, q in enumerate(st.session_state.quiz):
                st.markdown(f"<h5 style='font-size: 22px;'>Q{idx + 1}. {q['question']}</h5>", unsafe_allow_html=True)
                selected = st.radio("선택지", q['choices'], key=f"q_{idx}", index=None, label_visibility="collapsed")
                st.session_state.answers[idx] = q['choices'].index(selected) + 1 if selected in q['choices'] else None
            submitted = st.form_submit_button("제출")

        if submitted:
            for idx, q in enumerate(st.session_state.quiz):
                if st.session_state.answers.get(idx) == q['answer']:
                    score += 1
                else:
                    st.session_state.incorrect.append(idx)
            st.session_state.submitted = True
            st.session_state.score = score
        return

    # 채점 및 해설 화면
    if st.session_state.get("submitted", False):
        total = len(st.session_state.quiz)
        st.success(f"총 {total}문제 중 {st.session_state.score}문제 정답! 점수: {int(st.session_state.score / total * 100)}점")

        if st.session_state.incorrect:
            with st.expander("❌ 틀린 문제 해설 보기"):
                for idx in st.session_state.incorrect:
                    q = st.session_state.quiz[idx]
                    st.markdown(f"**Q{idx + 1}. {q['question']}**")
                    st.markdown(f"- 정답: {q['choices'][q['answer'] - 1]}")
                    st.markdown(f"- 해설: {q['explanation']}")

            if st.button("🔁 오답 다시 풀기"):
                st.session_state.quiz = [st.session_state.quiz[i] for i in st.session_state.incorrect]
                st.session_state.answers = {}
                st.session_state.incorrect = []
                st.session_state.submitted = False
                st.rerun()  # ✅ 최신 rerun 함수

        if st.button("🔄 새 퀴즈 생성"):
            # 모든 퀴즈 상태 변수 삭제 → 첫 화면으로
            for key in ["quiz", "answers", "submitted", "score", "incorrect"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()  # ✅ 최신 rerun 함수

