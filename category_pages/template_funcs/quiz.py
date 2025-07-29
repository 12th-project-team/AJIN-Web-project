import streamlit as st
from langchain_openai import ChatOpenAI
from vectorstore_utils import load_chroma_vectorstore
import os
import re

CATEGORY_NAME = None  # 생성된 카테고리 모듈에서 실제 값이 넘어옵니다.

def build_context_from_docs(docs, max_length=8000):
    context = ""
    for doc in docs:
        if len(context) + len(doc.page_content) > max_length:
            break
        context += doc.page_content + "\n"
    return context

def generate_quiz(llm, context, topic):
    prompt = f"...(위와 동일)..."
    return llm.invoke(prompt)

def parse_quiz(text: str):
    # 위와 동일한 parse_quiz 함수 복사
    items = []
    for m in re.finditer(r"문제\s*\d+([\s\S]*?)(?=문제\s*\d+|$)", text):
        block = m.group(1).strip()
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        question = lines[0]
        choices = []
        for line in lines[1:]:
            mm = re.match(r"^[1-4]\.?\s*(.+)", line)
            if mm: choices.append(mm.group(1).strip())
            if len(choices) == 4: break
        if len(choices) < 4: continue
        answer = None
        for line in lines:
            aa = re.search(r"정답[:\s]*([1-4])", line)
            if aa:
                answer = int(aa.group(1))
                break
        explanation = ""
        ee = re.search(r"해설[:\-]\s*([\s\S]+)", block)
        if ee: explanation = ee.group(1).strip()
        items.append({
            "question": question,
            "choices": choices,
            "answer": answer,
            "explanation": explanation
        })
    return items

def render(category_name: str):
    st.header(f"📝 {category_name} - 객관식 퀴즈 풀기")
    base_path = os.path.join("chroma_db", category_name)
    if not os.path.exists(base_path):
        st.info("❗ 저장된 문서가 없습니다.")
        return

    docs = [d for d in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, d))]
    if not docs:
        st.info("❗ 저장된 문서가 없습니다.")
        return

    # 퀴즈 생성 전
    if "quiz_items" not in st.session_state:
        sel = st.selectbox(
            "문서 선택",
            docs,
            key=f"tpl_quiz_doc_{category_name}"
        )
        topic = st.text_input(
            "주제 입력",
            key=f"tpl_quiz_topic_{category_name}"
        )
        if st.button(
            "퀴즈 생성 및 풀기",
            key=f"tpl_quiz_create_{category_name}"
        ):
            if not topic:
                st.warning("주제를 입력해주세요.")
                return
            vectordb = load_chroma_vectorstore(category_name, sel)
            retriever = vectordb.as_retriever(search_kwargs={"k": 10})
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
            docs_ctx = retriever.get_relevant_documents(topic)
            context = build_context_from_docs(docs_ctx)
            with st.spinner("퀴즈 생성 중..."):
                resp = generate_quiz(llm, context, topic)
            text = getattr(resp, "content", resp)
            quiz_list = parse_quiz(text)
            if not quiz_list:
                st.error("문제를 파싱하지 못했습니다.")
                st.text_area("원문", text, height=200)
                return
            st.session_state.quiz_items = quiz_list
            st.session_state.answers    = {}
            st.session_state.incorrect  = []
            st.session_state.submitted  = False
        return

    # 퀴즈 풀기
    if not st.session_state.submitted:
        with st.form(f"tpl_quiz_form_{category_name}"):
            for idx, q in enumerate(st.session_state.quiz_items):
                st.markdown(f"**Q{idx+1}. {q['question']}**")
                choice = st.radio(
                    "",
                    q["choices"],
                    key=f"tpl_quiz_choice_{category_name}_{idx}"
                )
                st.session_state.answers[idx] = q["choices"].index(choice) + 1
            if st.form_submit_button(
                "제출",
                key=f"tpl_quiz_submit_{category_name}"
            ):
                score = 0
                for idx, q in enumerate(st.session_state.quiz_items):
                    if st.session_state.answers.get(idx) == q["answer"]:
                        score += 1
                    else:
                        st.session_state.incorrect.append(idx)
                st.session_state.score     = score
                st.session_state.submitted = True
        return

    # 채점 및 해설
    total = len(st.session_state.quiz_items)
    score = st.session_state.score
    pct   = int(score/total*100) if total else 0
    st.success(f"총 {total}문제 중 {score}문제 정답! ({pct}점)")
    if st.session_state.incorrect:
        with st.expander("틀린 문제 해설"):
            for idx in st.session_state.incorrect:
                q = st.session_state.quiz_items[idx]
                st.markdown(f"- Q{idx+1}. {q['question']}")
                st.markdown(f"  - 정답: {q['choices'][q['answer']-1]}")
                st.markdown(f"  - 해설: {q['explanation']}")
        if st.button(
            "오답 다시 풀기",
            key=f"tpl_quiz_retry_{category_name}"
        ):
            st.session_state.quiz_items = [
                st.session_state.quiz_items[i]
                for i in st.session_state.incorrect
            ]
            for k in ["answers","incorrect","submitted","score"]:
                st.session_state.pop(k, None)
            st.rerun()

    if st.button(
        "새 퀴즈 생성",
        key=f"tpl_quiz_new_{category_name}"
    ):
        for k in ["quiz_items","answers","incorrect","submitted","score"]:
            st.session_state.pop(k, None)
        st.rerun()
