from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_core.documents import Document
load_dotenv()


# 1. Documents to be stored in ChromaDB
docs = [
    Document(page_content="Gradient descent is an optimization algorithm used in machine learning."),
    Document(page_content="Gradient descent minimizes the loss function."),
    Document(page_content="Gradient descent is an optimization that minimizes the loss function."),
    Document(page_content="Neural networks use gradient descent for training."),
    Document(page_content="Support Vector Machines are supervised learning algorithms.")
]

#  2. Create embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# 3. Store embeddings into Chroma vector store
vectorstores = Chroma.from_documents(
    documents = docs,  
    embedding = embeddings,
    persist_directory = "chroma_db"
)


# 4. Normal retriver
retriever = vectorstores.as_retriever()



# 5. Groq Model for multi query retriever
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)



# 6. Multi query retriever
multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=retriever,   
    llm=llm
)  



# 7. User Query
query = "What is gradient descent?"


# 8. Retrieve documents using multi query retriever
docs = multi_query_retriever.invoke(query)

print("\nRetrieved documents:")


for doc in docs:
    print(doc.page_content) 
