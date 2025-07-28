import streamlit as st
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pathlib import Path
import os
from dotenv import load_dotenv

# --- 환경변수 로드 ---
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI API 키가 없습니다. .env 파일을 확인하세요.")
    st.stop()

# --- 경로 설정 ---
pdf_path = Path(r"C:\woohyun\AJIN-12th-project\data\컴활1급.pdf")
save_dir = Path.cwd() / "faiss_db"
save_dir.mkdir(parents=True, exist_ok=True)

# --- 벡터스토어 생성 함수 ---
@st.cache_data(show_spinner=True)
def create_vectorstore():
    if not pdf_path.exists():
        st.error(f"PDF 파일이 없습니다: {pdf_path}")
        st.stop()

    loader = PyPDFLoader(str(pdf_path))
    all_docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    split_docs = text_splitter.split_documents(all_docs)

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(folder_path=str(save_dir), index_name="index")
    return vectorstore

# --- 벡터스토어 로드 함수 ---
@st.cache_resource(show_spinner=True)
def load_vectorstore():
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = FAISS.load_local(
        str(save_dir),
        embeddings,
        index_name="index",
        allow_dangerous_deserialization=True
    )
    return vectorstore

# --- 벡터스토어 준비 ---
st.title("🧠 컴활1급 PDF 기반 학습 도우미")

if not (save_dir / "index.faiss").exists():
    st.info("🔄 벡터스토어가 없습니다. PDF를 기반으로 생성합니다.")
    vectorstore = create_vectorstore()
    st.success("✅ 벡터스토어 생성 완료!")
else:
    vectorstore = load_vectorstore()

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
llm = ChatOpenAI(model_name="gpt-4o", temperature=0.3, openai_api_key=openai_api_key)

# --- 공통 프롬프트 ---
base_prompt = PromptTemplate(
    template="""
당신은 친절하고 유능한 전문가입니다. 다음은 사용자의 질문과 관련된 참고 문서입니다:

{context}

질문: {question}

참고 문서를 기반으로 정확하게 답하세요. 모르는 내용은 추측하지 마세요.
""",
    input_variables=["context", "question"]
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": base_prompt}
)

# --- 사용자 질문 입력 ---
query = st.text_input("❓ 궁금한 내용을 입력하세요:")

# --- 버튼 UI ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    run_qa = st.button("질문 답변")
with col2:
    run_summary = st.button("요약 요청")
with col3:
    run_quiz = st.button("퀴즈 생성")
with col4:
    run_exam = st.button("기출문제 생성")

# --- 관련 문서 불러오기 ---
def get_context(query):
    docs = retriever.get_relevant_documents(query)
    return "\n".join([doc.page_content for doc in docs])

# --- 기능별 실행 ---
if query:
    context = get_context(query)

    if run_qa:
        with st.spinner("🧠 답변 생성 중..."):
            response = qa_chain.invoke({"query": query})
        st.subheader("💬 답변")
        st.write(response["result"])

    if run_summary:
        with st.spinner("📘 요약 중..."):
            prompt = f"""
주제 10개정도 나눠서 다음 내용을 간단히 3~5줄로 요약해줘:

{context}
"""
            result = llm.invoke(prompt)
        st.subheader("📘 요약 결과")
        st.write(result.content)

    if run_quiz:
        with st.spinner("📝 퀴즈 문제 생성 중..."):
            prompt = f"""
다음 내용을 바탕으로 객관식 퀴즈 10개를 만들어줘. 각 문제는 보기 4개와 정답과 구체적인 해설을 포함해줘.

{context}
"""
            result = llm.invoke(prompt)
        st.subheader("📝 퀴즈 문제")
        st.write(result.content)

    if run_exam:
        with st.spinner("📄 기출문제 스타일 생성 중..."):
            prompt = f"""
다음 내용을 기반으로 컴활 1급 필기 시험에서 나올 수 있는 객관식 문제 10개를 만들어줘.
각 문제는 보기와 정답과 구체적인 해설을 포함해.

{context}
"""
            result = llm.invoke(prompt)
        st.subheader("📄 기출문제")
        st.write(result.content)
