import streamlit as st
from langchain_openai import ChatOpenAI
from vectorstore_utils import load_chroma_vectorstore
import os, re

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
'{topic}'와 직접적으로 관련된 내용만 사용해 10문제 출제해줘.
각 문제는 보기 4개, 정답 번호, 해설을 포함해야 해.
형식:

문제 1. <질문>
1. 보기1
2. 보기2
3. 보기3
4. 보기4
정답: <번호>
해설: <설명>

{context}
"""
    # ChatOpenAI 인스턴스에 맞춰 호출합니다.
    return llm.invoke(prompt)

def parse_quiz(text: str):
    items = []
    for m in re.finditer(r"문제\s*\d+\.?([\s\S]*?)(?=문제\s*\d+\.?|$)", text):
        block = m.group(1).strip()
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue

        question = lines[0]
        # 보기 4개
        choices = []
        for ln in lines[1:]:
            if match := re.match(r"^[1-4]\.?\s*(.+)", ln):
                choices.append(match.group(1).strip())
            if len(choices) == 4:
                break
        if len(choices) < 4:
            continue

        # 정답
        answer = None
        for ln in lines:
            if ans := re.search(r"정답[:\s]*([1-4])", ln):
                answer = int(ans.group(1))
                break

        # 해설
        explanation = ""
        if heil := re.search(r"해설[:\-]\s*(.+)", block, re.DOTALL):
            explanation = heil.group(1).strip()

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
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    subfolders = [
        d for d in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, d))
    ]
    if not subfolders:
        st.info("❗ 저장된 문서가 없습니다.")
        return

    # 1) 문제 생성 전
    if "quiz_items" not in st.session_state:
        selected_doc = st.selectbox(
            "퀴즈를 생성할 문서를 선택하세요",
            subfolders,
            key=f"quiz_doc_{category_name}"
        )
        topic = st.text_input(
            "퀴즈 생성 주제를 입력하세요:",
            key=f"quiz_topic_{category_name}"
        )
        if st.button("퀴즈 생성 및 풀기", key=f"quiz_create_{category_name}"):
            if not topic.strip():
                st.warning("주제를 입력해주세요.")
            else:
                try:
                    vectordb = load_chroma_vectorstore(category_name, selected_doc)
                    retriever = vectordb.as_retriever(search_kwargs={"k": 15})
                    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)

                    docs_ctx = retriever.get_relevant_documents(topic)
                    context = build_context_from_docs(docs_ctx)

                    with st.spinner("📝 퀴즈 생성 중..."):
                        resp = generate_quiz(llm, context, topic)
                        text = getattr(resp, "content", resp)
                        quiz_list = parse_quiz(text)

                    if not quiz_list:
                        st.error("❗ 파싱된 문제가 없습니다. LLM 원문을 확인하세요.")
                        st.text_area("LLM 원문", text, height=200)
                    else:
                        st.session_state.quiz_items = quiz_list
                        st.session_state.answers    = {}
                        st.session_state.incorrect  = []
                        st.session_state.submitted  = False
                except Exception as e:
                    st.error(f"퀴즈 생성 오류: {e}")

        # 아직 생성 전이면 이 시점에서 함수 종료
        if "quiz_items" not in st.session_state:
            return

    # 2) 퀴즈 풀기
    if not st.session_state.get("submitted", False):
        with st.form(f"quiz_form_{category_name}"):
            for idx, q in enumerate(st.session_state.quiz_items):
                st.markdown(f"**Q{idx+1}. {q['question']}**")
                selected = st.radio(
                    label="",
                    options=q["choices"],
                    key=f"quiz_choice_{category_name}_{idx}",
                    label_visibility="collapsed"
                )
                st.session_state.answers[idx] = q["choices"].index(selected) + 1

            if st.form_submit_button("제출"):
                score = 0
                wrong = []
                for i, q in enumerate(st.session_state.quiz_items):
                    if st.session_state.answers.get(i) == q["answer"]:
                        score += 1
                    else:
                        wrong.append(i)

                st.session_state.score     = score
                st.session_state.incorrect = wrong
                st.session_state.submitted = True
        return

    # 3) 채점 및 해설
    total = len(st.session_state.quiz_items)
    score = st.session_state.score
    percent = int(score / total * 100) if total else 0
    st.success(f"총 {total}문제 중 {score}문제 정답! ({percent}점)")

    if st.session_state.incorrect:
        with st.expander("❌ 틀린 문제 해설 보기"):
            for i in st.session_state.incorrect:
                q = st.session_state.quiz_items[i]
                st.markdown(f"**Q{i+1}. {q['question']}**")
                st.markdown(f"- 정답: {q['choices'][q['answer']-1]}")
                st.markdown(f"- 해설: {q['explanation']}")

        if st.button("🔁 오답 다시 풀기", key=f"quiz_retry_{category_name}"):
            st.session_state.quiz_items = [
                st.session_state.quiz_items[i]
                for i in st.session_state.incorrect
            ]
            for k in ["answers","incorrect","submitted","score"]:
                st.session_state.pop(k, None)
            st.experimental_rerun()

    if st.button("🔄 새 퀴즈 생성", key=f"quiz_new_{category_name}"):
        for k in ["quiz_items","answers","incorrect","submitted","score"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()
