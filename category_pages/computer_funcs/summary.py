import streamlit as st
from langchain_openai import ChatOpenAI
from vectorstore_utils import load_chroma_vectorstore
import os

CATEGORY_NAME = "컴퓨터활용능력"

def render():
    st.header(f"📌 {CATEGORY_NAME} - 요점정리")

    base_path = os.path.join("chroma_db", CATEGORY_NAME)
    if not os.path.exists(base_path):
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    subfolders = os.listdir(base_path)
    if not subfolders:
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    selected_doc = st.selectbox("요약할 문서를 선택하세요", subfolders)

    try:
        vectordb = load_chroma_vectorstore(CATEGORY_NAME, selected_doc)
    except Exception as e:
        st.error(f"벡터스토어 로드 실패: {e}")
        return

    retriever = vectordb.as_retriever(search_kwargs={"k": 20})  # 다양한 맥락 확보
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.1)

    query = st.text_input(
        "요약할 주제를 입력하세요:",
        placeholder="예) 함수 종류와 특징, 엑셀 논리연산자, 운영체제의 역할 등"
    )

    if st.button("요약 실행"):
        if not query.strip():
            st.warning("요약할 주제를 입력해주세요.")
            return

        docs = retriever.get_relevant_documents(query)
        # 주제 키워드 filtering (korean/english 띄어쓰기, 콤마 구분)
        keywords = [kw.strip() for kw in query.replace(',', ' ').split()]
        filtered_docs = [
            doc for doc in docs if any(kw in doc.page_content for kw in keywords)
        ]
        if not filtered_docs:
            st.info("❗ 해당 주제와 관련된 내용이 문서에서 검색되지 않았습니다.")
            return

        context = "\n".join([doc.page_content for doc in filtered_docs if doc.page_content.strip()])

        prompt = f"""
너는 컴퓨터활용능력 공식 문서 기반 요약 전문가이자, 채점관이야.

[필수 지침]
- 반드시 아래 문서 내용에서 '{query}'와 직접적 또는 부분적으로 연관된 내용도 모두 포함 뽑아라.
- '{query}'와 관련 없는 배경 설명, 주변 개념, 추측, 일반론, 사족 등은 절대 포함하지 마라.
- 주제와 완전히 무관한 문장은 절대 생성하지 마라. 근거 없는 일반론, 상식, 부연설명 금지.
- '관련 내용 없음'은 해당 주제 키워드가 실제 문서에 없을 때만 출력하라.
- 실제 시험 대비에 필요한 **구체적, 실무적, 명확한 요약**만 제시하라.

[출력 형식]
- 관련 핵심 내용을 10개 이내의 소주제로 분류하여, 각 소주제(소단락)마다 **한글 제목**을 붙이고, 각 단락을 3~5줄 이내로 간결하게 요약하라.
- 반드시 번호와 제목, 요약이 구분되게 예시처럼 출력하라.

[출력 예시]
1. [소주제1 제목]: (3~5줄 요약)
2. [소주제2 제목]: (3~5줄 요약)
...

[문서에서 '{query}'와 직접적으로 연관된 문단(문장)만 활용하여 요약하라.]

-------------------------
{context}
-------------------------
"""
        with st.spinner("📘 요약 중..."):
            response = llm.invoke(prompt)
        st.subheader("📘 요점정리 결과")
        st.write(response.content if hasattr(response, "content") else response)
