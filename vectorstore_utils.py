# vectorstore_utils.py

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
import shutil
import json

# ─────────────────────────────────────────────────────────────────────────────
# 1) OpenAI 임베딩 모델 초기화 (벡터 저장용)
load_dotenv()
EMBED_API_KEY = os.getenv("OPENAI_API_KEY", "").strip("[]")
embedding_model = OpenAIEmbeddings(openai_api_key=EMBED_API_KEY)

# ─────────────────────────────────────────────────────────────────────────────
# 2) Chroma 벡터스토어 경로 헬퍼
def get_chroma_path(category: str, filename: str) -> str:
    """
    Chroma 벡터스토어 경로:
    chroma_db/<category>/<filename>
    """
    return os.path.join("chroma_db", category, filename)

# ─────────────────────────────────────────────────────────────────────────────
# 3) 문서 리스트를 Chroma로 저장
def save_chroma_vectorstore(docs, category: str, filename: str):
    """
    LangChain Document 객체 목록을 받아 Chroma에 임베딩 후 저장합니다.
    """
    persist_path = get_chroma_path(category, filename)
    os.makedirs(persist_path, exist_ok=True)

    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embedding_model,
        persist_directory=persist_path
    )
    vectordb.persist()
    return persist_path

# ─────────────────────────────────────────────────────────────────────────────
# 4) 저장된 Chroma 벡터스토어 로드
def load_chroma_vectorstore(category: str, filename: str):
    """
    이미 저장된 Chroma 벡터스토어를 불러옵니다.
    """
    persist_path = get_chroma_path(category, filename)
    if not os.path.exists(persist_path):
        raise FileNotFoundError(f"Chroma 경로가 존재하지 않음: {persist_path}")
    return Chroma(
        persist_directory=persist_path,
        embedding_function=embedding_model
    )

# ─────────────────────────────────────────────────────────────────────────────
# 5) 특정 카테고리의 저장된 문서(폴더) 리스트 반환
def list_chroma_files(category: str) -> list[str]:
    """
    chroma_db/<category> 하위의 서브폴더 목록을 반환합니다.
    """
    base_path = os.path.join("chroma_db", category)
    if not os.path.exists(base_path):
        return []
    return [
        name for name in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, name))
    ]

# ─────────────────────────────────────────────────────────────────────────────
# 6) Chroma 데이터 및 PDF 삭제
def delete_chroma_vectorstore(category: str, filename: str, doc_type: str = ""):
    """
    지정된 category/filename 의 벡터스토어와 업로드된 PDF를 삭제합니다.
    """
    # 6.1) 벡터스토어 삭제
    persist_path = get_chroma_path(category, filename)
    if os.path.exists(persist_path):
        shutil.rmtree(persist_path)

    # 6.2) 업로드된 PDF 삭제 (optional doc_type 디렉토리 안에 저장된 경우)
    if doc_type:
        pdf_path = os.path.join("uploaded_pdfs", doc_type, f"{filename}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

# ─────────────────────────────────────────────────────────────────────────────
# 7) 기출문제(CBT) JSON 저장/로드 기능 추가
def get_exam_json_path(category: str) -> str:
    """
    기출문제 JSON 파일 경로:
    exam_db/<category>/questions.json
    """
    folder = os.path.join("exam_db", category)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "questions.json")

def save_exam_questions(category: str, items: list[dict]):
    """
    추출된 문제 항목 리스트(items)를 JSON으로 저장합니다.
    items 각 요소는 다음 키들을 가져야 합니다:
      - question, choices (리스트), answer (정답 인덱스), explanation, page (기출페이지)
    """
    path = get_exam_json_path(category)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def load_exam_questions(category: str) -> list[dict]:
    """
    저장된 기출문제 JSON을 로드해 리스트로 반환합니다.
    """
    path = get_exam_json_path(category)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
