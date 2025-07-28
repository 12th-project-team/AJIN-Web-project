from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
import shutil

# 환경 변수에서 OpenAI API 키 로딩
load_dotenv()
embedding_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY", "").strip("[]"))

def get_chroma_path(category: str, filename: str) -> str:
    """
    Chroma 벡터스토어 경로를 category/filename 기준으로 구성 (한글 그대로 사용)
    """
    return os.path.join("chroma_db", category, filename)

def save_chroma_vectorstore(docs, category: str, filename: str):
    """
    문서 리스트를 Chroma로 저장 (persist_directory 기준)
    """
    persist_path = get_chroma_path(category, filename)
    os.makedirs(persist_path, exist_ok=True)

    vectordb = Chroma.from_documents(docs, embedding_model, persist_directory=persist_path)
    vectordb.persist()
    return persist_path

def load_chroma_vectorstore(category: str, filename: str):
    """
    저장된 Chroma 벡터스토어를 불러오기
    """
    persist_path = get_chroma_path(category, filename)
    if not os.path.exists(persist_path):
        raise FileNotFoundError(f"Chroma 경로가 존재하지 않음: {persist_path}")

    return Chroma(persist_directory=persist_path, embedding_function=embedding_model)

def list_chroma_files(category: str):
    """
    해당 카테고리 경로 아래의 저장된 문서 목록 반환
    """
    base_path = os.path.join("chroma_db", category)
    if not os.path.exists(base_path):
        return []
    return [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

def delete_chroma_vectorstore(category: str, filename: str, doc_type: str = ""):
    """
    특정 카테고리/문서에 해당하는 Chroma 벡터스토어 및 업로드된 PDF 삭제
    """
    # Chroma 임베딩 데이터 삭제
    persist_path = get_chroma_path(category, filename)
    if os.path.exists(persist_path):
        shutil.rmtree(persist_path)

    # 업로드된 PDF 원본 삭제
    if doc_type:
        pdf_path = os.path.join("uploaded_pdfs", doc_type, f"{filename}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
