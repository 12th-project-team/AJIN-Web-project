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

    # k값 늘려서 맥락 다양하게 확보 (실험적으로 10~15도 가능)
    retriever = vectordb.as_retriever(search_kwargs={"k": 12})
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)

    query = st.text_input(
        "요약할 주제를 입력하세요:",
        placeholder="예) 함수 종류와 특징, 엑셀 논리연산자, 운영체제의 역할 등"
    )

    if st.button("요약 실행"):
        if not query.strip():
            st.warning("요약할 주제를 입력해주세요.")
            return

        docs = retriever.get_relevant_documents(query)
        context = "\n".join([doc.page_content for doc in docs if doc.page_content.strip()])

        # 프롬프트: 실제 시험 대비, '직접적 관련성' 강조, 분류/제목/불필요한 내용 제외 요구
        prompt = f"""
너는 컴퓨터활용능력 공식 문서 기반 요약 전문가야.

- 아래 문서 내용에서 '{query}'와 직접적으로 관련된 핵심만 추려서 10개 이내의 소주제(소단락)로 분류해서 각 소주제별로 3~5줄 이내로만 간결하게 요약해.
- 각 소주제(소단락)마다 한글 제목을 붙이고, 해당 내용이 불확실하거나 없으면 '관련 내용 없음'이라고 써.
- 배경 설명, 발전사, 주변 개념, 일반론, 추측, 사족 등은 모두 빼고 실제 시험 대비에 필요한 구체적 요약만 제시해.
- 출력 형식(예시):
    1. [소주제1 제목]: (3~5줄 요약)
    2. [소주제2 제목]: (3~5줄 요약)
    ...

아래는 참고할 문서 내용이다:
-------------------------
{context}
-------------------------
"""

        with st.spinner("📘 요약 중..."):
            response = llm.invoke(prompt)
        st.subheader("📘 요점정리 결과")
        st.write(response.content if hasattr(response, "content") else response)
