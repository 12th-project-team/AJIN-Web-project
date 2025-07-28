import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pathlib import Path
import os
from dotenv import load_dotenv
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

# nltk punkt tokenizer 다운로드 (최초 1회 필요)
nltk.download('punkt')

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
st.title("🧠 컴활1급 PDF 기반 GPT vs RAG 성능 비교")

if not (save_dir / "index.faiss").exists():
    st.info("🔄 벡터스토어가 없습니다. PDF를 기반으로 생성합니다.")
    vectorstore = create_vectorstore()
    st.success("✅ 벡터스토어 생성 완료!")
else:
    vectorstore = load_vectorstore()

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# GPT 단독 모델
llm_gpt = ChatOpenAI(model_name="gpt-4o", temperature=0.3, openai_api_key=openai_api_key)

# RAG (벡터검색 + LLM)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm_gpt,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": PromptTemplate(
        template="""
당신은 친절하고 유능한 전문가입니다. 다음은 사용자의 질문과 관련된 참고 문서입니다:

{context}

질문: {question}

참고 문서를 기반으로 정확하게 답하세요. 모르는 내용은 추측하지 마세요.
""",
        input_variables=["context", "question"]
    )}
)

# --- 사용자 입력 UI ---
query = st.text_input("❓ 질문을 입력하세요:")
ground_truth = st.text_area("🔍 정답(기대 답변)을 입력하세요:")

if st.button("비교 실행") and query and ground_truth:
    # GPT 단독 답변 생성
    with st.spinner("GPT 단독 답변 생성 중..."):
        gpt_response = llm_gpt.invoke(f"질문에 대해 친절하고 정확하게 답변해줘:\n{query}")
        gpt_answer = gpt_response.content.strip()
    st.subheader("🤖 GPT 단독 답변")
    st.write(gpt_answer)

    # RAG 답변 생성
    with st.spinner("RAG 답변 생성 중..."):
        rag_response = qa_chain.invoke({"query": query})
        rag_answer = rag_response["result"].strip()
    st.subheader("🧠 RAG 답변")
    st.write(rag_answer)

    # 정답 토큰화 (BLEU 계산 준비)
    reference = [nltk.word_tokenize(ground_truth.lower())]
    candidate_gpt = nltk.word_tokenize(gpt_answer.lower())
    candidate_rag = nltk.word_tokenize(rag_answer.lower())

    # BLEU 계산 (smooth method 사용)
    smoothie = SmoothingFunction().method4
    bleu_gpt = sentence_bleu(reference, candidate_gpt, smoothing_function=smoothie)
    bleu_rag = sentence_bleu(reference, candidate_rag, smoothing_function=smoothie)

    st.subheader("📊 정량 평가 (BLEU 점수)")
    st.write(f"GPT 단독 BLEU 점수: {bleu_gpt:.4f}")
    st.write(f"RAG BLEU 점수: {bleu_rag:.4f}")

    # 간단 정확도 평가 (답변이 정답 텍스트 포함 여부)
    acc_gpt = int(ground_truth.strip() in gpt_answer)
    acc_rag = int(ground_truth.strip() in rag_answer)

    st.subheader("📊 간단 정확도 평가 (정답 텍스트 포함 여부)")
    st.write(f"GPT 단독 정확도: {acc_gpt}")
    st.write(f"RAG 정확도: {acc_rag}")
else:
    st.info("질문과 정답을 모두 입력한 후 '비교 실행' 버튼을 눌러주세요.")
