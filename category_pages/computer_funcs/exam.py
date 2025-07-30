import os
import json
import streamlit as st
import fitz  # PyMuPDF
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY", "").strip()

UPLOAD_DIR = "uploaded_pdfs"
EXAM_DB_DIR = "exam_db"

def ensure_dirs(category: str):
    pdf_dir  = os.path.join(UPLOAD_DIR, category)
    json_dir = os.path.join(EXAM_DB_DIR, category)
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)
    return pdf_dir, json_dir

def list_uploaded_pdfs(category: str):
    pdf_dir = os.path.join(UPLOAD_DIR, category)
    if not os.path.exists(pdf_dir):
        return []
    return [f[:-4] for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]

def list_saved_jsons(category: str):
    json_dir = os.path.join(EXAM_DB_DIR, category)
    if not os.path.exists(json_dir):
        return []
    return [f[:-5] for f in os.listdir(json_dir) if f.lower().endswith(".json")]

def extract_questions_with_gpt(text):
    prompt = (
        "아래 텍스트는 자격증 객관식 시험 문제지입니다.\n"
        "문항 번호(Q1, Q2, ...)로 시작하는 부분만 문제로 인식해서 추출하세요.\n"
        "정답, 해설, 정답표, 해설집, 해설 모음, 보충 설명 등은 문제로 인식하지 말고 무시하세요.\n"
        "각 문제는 question, choices(4지선다), answer(정답 번호 1~4), explanation(해설 또는 '없음') 필드를 갖는 JSON 배열로만 반환하세요.\n"
        "설명, 안내, 코드블록 없이 예시와 완전히 동일한 JSON 배열만 출력하세요.\n"
        "예시: [{\"question\": \"질문\", \"choices\": [\"보기1\", \"보기2\", \"보기3\", \"보기4\"], \"answer\": 2, \"explanation\": \"해설\"}]"
    )
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        temperature=0,
        max_tokens=2048,
    )
    content = completion.choices[0].message.content.strip()
    # 코드블록이나 안내문 제거
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    # 파싱
    return json.loads(content)

def parse_pdf_and_save(category: str, filename: str):
    pdf_dir, json_dir = ensure_dirs(category)
    pdf_path = os.path.join(pdf_dir, f"{filename}.pdf")
    doc = fitz.open(pdf_path)

    all_items = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()
        st.info(f"페이지 {page_num+1} 텍스트 미리보기:\n\n{page_text[:400]}")
        try:
            items = extract_questions_with_gpt(page_text)
            if isinstance(items, list):
                all_items.extend(items)
        except Exception as e:
            st.error(f"페이지 {page_num+1} 파싱 실패: {e}")
            continue

    out_path = os.path.join(json_dir, f"{filename}.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(all_items, fp, ensure_ascii=False, indent=2)
    return out_path

def render(category_name: str):
    st.header("📄 기출문제 모의 연습 (CBT)")

    pdfs = list_uploaded_pdfs(category_name)
    if not pdfs:
        st.info("❗ 먼저 PDF를 업로드하세요.")
        return

    sel_pdf = st.selectbox("▶️ PDF 선택", pdfs, key="exam_pdf_sel")
    if st.button("파싱하여 시험 문제 저장"):
        with st.spinner("⏳ GPT-4o로 문제 추출 중..."):
            try:
                saved = parse_pdf_and_save(category_name, sel_pdf)
                st.success(f"✅ JSON 저장: `{saved}`")
            except Exception as e:
                st.error(f"파싱 오류: {e}")
        st.rerun()

    st.markdown("---")

    jsons = list_saved_jsons(category_name)
    if not jsons:
        st.info("❗ 파싱된 JSON이 없습니다.")
        return

    sel_json = st.selectbox("💾 저장된 문제 파일", jsons, key="exam_json_sel")
    json_path = os.path.join(EXAM_DB_DIR, category_name, f"{sel_json}.json")
    with open(json_path, "r", encoding="utf-8") as fp:
        questions = json.load(fp)

    if "answers" not in st.session_state:
        st.session_state.answers = {}

    with st.form("exam_form"):
        for i, qi in enumerate(questions):
            st.markdown(f"**Q{i+1}. {qi['question']}**")
            c = st.radio(
                label="",
                options=qi["choices"],
                key=f"exam_choice_{i}",
                label_visibility="collapsed"
            )
            st.session_state.answers[i] = qi["choices"].index(c) + 1
        submitted = st.form_submit_button("제출")

    if submitted:
        correct = sum(
            1 for i, qi in enumerate(questions)
            if st.session_state.answers.get(i) == qi["answer"]
        )
        total = len(questions)
        pct = int(correct/total*100) if total else 0
        st.success(f"총 {total}문제 중 {correct}문제 정답 (점수: {pct}점)")

        if correct < total:
            with st.expander("❌ 오답 해설"):
                for i, qi in enumerate(questions):
                    if st.session_state.answers.get(i) != qi["answer"]:
                        st.markdown(f"- **Q{i+1}. {qi['question']}**")
                        st.markdown(f"  - 정답: {qi['choices'][qi['answer']-1]}")
                        st.markdown(f"  - 해설: {qi['explanation']}")

        if st.button("🔄 다시 풀기"):
            del st.session_state.answers
            st.rerun()
