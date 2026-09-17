# load pdf
# split into chunks
# create embeddings
# store into chroma

from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()


# --------------------------------
# 1. Load PDF
# --------------------------------

pdf_path = "document loader/deep-learning.pdf"

reader = PdfReader(pdf_path)

docs = []

for page_number, page in enumerate(reader.pages[:30]):

    text = page.extract_text()

    if text:
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": pdf_path,
                    "page": page_number + 1
                }
            )
        )

print("PDF loaded successfully!")
print("Number of pages:", len(docs))


# --------------------------------
# 2. Split into chunks
# --------------------------------

def split_text(text, chunk_size=1000, chunk_overlap=200):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - chunk_overlap

    return chunks


chunks = []

for doc in docs:

    text_chunks = split_text(
        doc.page_content,
        chunk_size=1000,
        chunk_overlap=200
    )

    for chunk in text_chunks:

        chunks.append(
            Document(
                page_content=chunk,
                metadata=doc.metadata
            )
        )


print("Number of chunks:", len(chunks))

# --------------------------------
# 3. Gemini Embeddings
# --------------------------------

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)

# --------------------------------
# 4. Store in ChromaDB in batches
# --------------------------------

import time

vectorstore = Chroma(
    collection_name="deep_learning",
    embedding_function=embeddings,
    persist_directory="chroma_db"
)

batch_size = 50

for i in range(0, len(chunks), batch_size):

    batch = chunks[i:i + batch_size]

    print(
        f"Embedding chunks {i + 1} - "
        f"{min(i + batch_size, len(chunks))} "
        f"of {len(chunks)}"
    )

    vectorstore.add_documents(batch)

    time.sleep(2)

print("Documents successfully stored in ChromaDB!")