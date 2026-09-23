import os
import shutil
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Student RAG API",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENTS_DIR = "document loader"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "deep_learning"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

os.makedirs(DOCUMENTS_DIR, exist_ok=True)


# ============================================================
# LAZY-LOADED COMPONENTS
# ============================================================

embeddings_model = None
vectorstore = None
llm = None


def get_embeddings():
    """
    Load the HuggingFace embedding model only when needed.
    This prevents Render from blocking during startup.
    """

    global embeddings_model

    if embeddings_model is None:
        print("Loading HuggingFace embedding model...")

        from embeddings import LocalHuggingFaceEmbeddings

        embeddings_model = LocalHuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME
        )

        print("HuggingFace embedding model loaded successfully.")

    return embeddings_model


def get_vectorstore():
    """
    Create/load Chroma only when needed.
    """

    global vectorstore

    if vectorstore is None:
        print("Initializing Chroma vector store...")

        from langchain_chroma import Chroma

        vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=CHROMA_DIR,
            embedding_function=get_embeddings()
        )

        print("Chroma vector store initialized successfully.")

    return vectorstore


def get_llm():
    """
    Initialize Groq only when needed.
    """

    global llm

    if llm is None:
        print("Initializing Groq LLM...")

        from langchain_groq import ChatGroq

        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0,
            max_tokens=1024,
        )

        print("Groq LLM initialized successfully.")

    return llm


# ============================================================
# RAG PROMPT
# ============================================================

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert academic tutor and AI assistant helping students study from their books and documents.

Answer the question thoroughly and accurately using ONLY the provided context snippets from the student's books/documents.

If the answer is not in the provided context, state:

"I could not find the answer in your uploaded documents."
"""
        ),
        (
            "human",
            """Context from textbook:

{context}

Question:

{question}"""
        )
    ]
)


# ============================================================
# TEXT SPLITTER
# ============================================================

def split_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - chunk_overlap

    return chunks


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class ChatRequest(BaseModel):
    question: str
    k: Optional[int] = 4


class SourceItem(BaseModel):
    source: str
    page: int
    content: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "message": "Student RAG API is running"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():

    return {
        "status": "healthy",
        "embedding_model": EMBEDDING_MODEL_NAME,
        "vector_store": "ChromaDB",
        "llm": "Groq (openai/gpt-oss-20b)"
    }


# ============================================================
# LIST DOCUMENTS
# ============================================================

@app.get("/api/documents")
def list_documents():

    docs_list = []

    if os.path.exists(DOCUMENTS_DIR):

        for fname in os.listdir(DOCUMENTS_DIR):

            fpath = os.path.join(
                DOCUMENTS_DIR,
                fname
            )

            if (
                os.path.isfile(fpath)
                and fname.lower().endswith((".pdf", ".txt"))
            ):

                size_mb = round(
                    os.path.getsize(fpath)
                    / (1024 * 1024),
                    2
                )

                page_count = 0

                if fname.lower().endswith(".pdf"):

                    try:

                        reader = PdfReader(fpath)

                        page_count = len(reader.pages)

                    except Exception:

                        page_count = 0

                docs_list.append(
                    {
                        "filename": fname,
                        "size_mb": size_mb,
                        "pages": page_count,
                        "path": fpath
                    }
                )

    return {
        "documents": docs_list
    }


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    from langchain_core.documents import Document

    if not file.filename.lower().endswith(
        (".pdf", ".txt")
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    file_path = os.path.join(
        DOCUMENTS_DIR,
        file.filename
    )

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # Get vector store only when actually needed
    store = get_vectorstore()

    chunks = []

    page_count = 0

    # ========================================================
    # PDF
    # ========================================================

    if file.filename.lower().endswith(".pdf"):

        reader = PdfReader(file_path)

        page_count = len(reader.pages)

        for page_number, page in enumerate(
            reader.pages
        ):

            text = page.extract_text()

            if text:

                text_chunks = split_text(
                    text,
                    chunk_size=1000,
                    chunk_overlap=200
                )

                for chunk in text_chunks:

                    chunks.append(
                        Document(
                            page_content=chunk,
                            metadata={
                                "source": file.filename,
                                "page": page_number + 1
                            }
                        )
                    )

    # ========================================================
    # TXT
    # ========================================================

    else:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            text = f.read()

        text_chunks = split_text(
            text,
            chunk_size=1000,
            chunk_overlap=200
        )

        for chunk in text_chunks:

            chunks.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": file.filename,
                        "page": 1
                    }
                )
            )

    # ========================================================
    # ADD TO CHROMA
    # ========================================================

    if chunks:

        batch_size = 50

        for i in range(
            0,
            len(chunks),
            batch_size
        ):

            batch = chunks[
                i:i + batch_size
            ]

            store.add_documents(batch)

    return {
        "filename": file.filename,
        "message": (
            f"Successfully uploaded and indexed "
            f"{len(chunks)} chunks across "
            f"{page_count} pages."
        ),
        "pages": page_count,
        "chunks": len(chunks)
    }


# ============================================================
# CHAT
# ============================================================

@app.post(
    "/api/chat",
    response_model=ChatResponse
)
def chat(req: ChatRequest):

    if not req.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # ========================================================
    # LOAD COMPONENTS ONLY WHEN REQUEST ARRIVES
    # ========================================================

    store = get_vectorstore()

    model = get_llm()

    # ========================================================
    # RETRIEVER
    # ========================================================

    retriever = store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": req.k,
            "fetch_k": req.k * 3,
            "lambda_mult": 0.5
        }
    )

    retrieved_docs = retriever.invoke(
        req.question
    )

    # ========================================================
    # SOURCES
    # ========================================================

    sources = []

    context_blocks = []

    for doc in retrieved_docs:

        src_name = doc.metadata.get(
            "source",
            "Unknown Document"
        )

        pg_num = doc.metadata.get(
            "page",
            1
        )

        sources.append(
            SourceItem(
                source=os.path.basename(src_name),
                page=pg_num,
                content=doc.page_content.strip()
            )
        )

        context_blocks.append(
            f"[Document: {os.path.basename(src_name)} | "
            f"Page: {pg_num}]\n"
            f"{doc.page_content.strip()}"
        )

    context_str = "\n\n---\n\n".join(
        context_blocks
    )

    # ========================================================
    # PROMPT
    # ========================================================

    formatted_prompt = prompt_template.invoke(
        {
            "context": (
                context_str
                if context_str
                else "No context available."
            ),
            "question": req.question
        }
    )

    # ========================================================
    # GROQ
    # ========================================================

    try:

        response = model.invoke(
            formatted_prompt
        )

        answer_text = response.content

    except Exception as e:

        answer_text = (
            f"Error generating response from LLM: {str(e)}"
        )

    return ChatResponse(
        answer=answer_text,
        sources=sources
    )


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            "8765"
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )