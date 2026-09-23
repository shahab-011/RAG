from pypdf import PdfReader
from embeddings import LocalHuggingFaceEmbeddings

# 1. Load PDF from document loader directory
pdf_path = "document loader/deep-learning.pdf"
reader = PdfReader(pdf_path)

# Extract text from the first page for testing
page_text = reader.pages[0].extract_text()

print("=" * 60)
print(f"Loaded PDF: {pdf_path}")
print(f"Total Pages in PDF: {len(reader.pages)}")
print(f"Sample Text (Page 1 - first 250 chars):\n{page_text[:250]}...")
print("=" * 60)

# 2. Create embedding using local Hugging Face model
embeddings_model = LocalHuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector = embeddings_model.embed_query(page_text)

print("\nGENERATED EMBEDDING VECTOR:")
print("=" * 60)
print(f"Vector Dimensions: {len(vector)}")
print(f"\nFull Vector Values:\n{vector}")
print("=" * 60)
