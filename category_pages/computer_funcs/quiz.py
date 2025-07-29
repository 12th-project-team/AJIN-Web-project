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

아래 조건을 반드시 지켜서 문제를 출제해:

1. 반드시 '{topic}'와 직접적으로 연관된 내용만 활용해서 문제를 낸다.
2. 객관식 문제는 반드시 총 10문제를 한 번에 모두 연속해서 출제한다. (누락 없이)
3. 각 문제는 반드시 4지선다형이다.
4. 아래 format 예시처럼 "문제 1" ~ "문제 10"까지 연속으로 출력한다.
5. 각 문제마다 보기, 정답, 해설을 모두 포함해야 한다.

--- format 예시 ---
문제 1
다음 중 [topic]에 해당하는 함수의 주요 용도는 무엇인가?
1. A 설명
2. B 설명
3. C 설명
4. D 설명
정답: 1. A 설명
해설:
- 정답: 이 보기가 정답인 이유를 구체적으로 설명.
- 오답: 각각 오답인 이유를 1~2문장으로 명확히 제시.

문제 2
[topic]에 대해 올바르게 설명한 것은 무엇인가?
1. A 설명
2. B 설명
3. C 설명
4. D 설명
정답: 2. B 설명
해설:
- 정답: 이 보기가 정답인 이유를 구체적으로 설명.
- 오답: - 오답: 각각의 오답 보기가 왜 틀렸는지, 개념적으로 어떤 부분이 잘못됐는지 또는 오해할 수 있는 점까지 구체적으로 설명.

---
반드시 위 format과 동일하게, 10문제를 연속 출력하고 빠진 문제 없이 답변할 것.
각 해설은 반드시 충분히 자세하고, 실제 적용 사례/비유/오답의 함정 등까지 포함하여 설명할 것.

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
        while len(choices) < 4:
            choices.append("보기 없음")
        answer_line = next((l for l in lines if l.startswith("정답")), "")
        answer_num = int(re.search(r"정답: (\d+)", answer_line).group(1)) if "정답" in answer_line else -1
        explanation_index = next((i for i, l in enumerate(lines) if l.startswith("해설")), None)
        if explanation_index is not None:
            explanation_lines = lines[explanation_index:]
            # 모든 "해설:" 제거 (각 줄 앞에 있을 수 있음)
            explanation = "\n".join([l.replace("해설:", "").strip() for l in explanation_lines])
        else:
            explanation = ""
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
                llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)
                docs = retriever.get_relevant_documents(query)
                context = build_context_from_docs(docs)
                with st.spinner("📝 퀴즈를 생성 중입니다..."):
                    response = generate_quiz(llm, context, query)
                    quiz_list = parse_quiz(response.content if hasattr(response, "content") else response)
                if len(quiz_list) < 10:
                    st.warning(f"⚠️ 10문제가 모두 생성되지 않았습니다. (생성된 문제: {len(quiz_list)}개) context 또는 topic을 확인하세요.")
                st.session_state.quiz = quiz_list
                st.session_state.answers = {}
                st.session_state.incorrect = []
                st.session_state.submitted = False
            except Exception as e:
                st.error(f"퀴즈 생성 중 오류 발생: {e}")

    # 생성 즉시 아래로 진행하여 바로 풀이 화면 렌더
    if "quiz" in st.session_state and not st.session_state.get("submitted", False):
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

    if "quiz" in st.session_state and st.session_state.get("submitted", False):
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
                st.rerun()  # 최신 rerun 함수

        if st.button("🔄 새 퀴즈 생성"):
            # 모든 퀴즈 상태 변수 삭제 → 첫 화면으로
            for key in ["quiz", "answers", "submitted", "score", "incorrect"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()  # 최신 rerun 함수
