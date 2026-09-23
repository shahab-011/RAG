from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from embeddings import LocalHuggingFaceEmbeddings
from langchain_chroma import Chroma
load_dotenv()

# 1. Load embeddings model and vectorstore
embeddings_model = LocalHuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 2. Load Chroma vectorstore
vectorstore = Chroma(
    collection_name="deep_learning",
    persist_directory="chroma_db",
    embedding_function=embeddings_model
)



# 3. Create retriever from vectorstore
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,
        "fetch_k": 10,
        "lambda_mult": 0.5
    }
)


# 4. Create ChatGroq model for RAG
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=1024,
)

   

# 5. Create prompt template for RAG
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a helpful assistant.

Use only the provided context to answer the question.

If the answer is not present in the context, say:
"I could not find the answer in the document."
"""
    ),
    (
        "human",
        """Context:
{context}

Question:
{question}"""
    )
])

print("Rag system is created successfully")


# 6. Start the RAG loop for user queries
print("Press 0 to exit :")

while True:
    query = input("You: ")
    if query == "0":
        break
    
     # Retrieve relevant documents
    docs = retriever.invoke(query)

    # Combine retrieved chunks into a single context
    context = "\n\n".join([doc.page_content for doc in docs])


    # Create final prompt
    final_prompt = prompt.invoke({
        "context": context,
        "question": query
    })

    # Send to Groq
    response = llm.invoke(final_prompt)
    print("\nAI: ", response.content)





































# # Prompt template for the chat model
# template = chat_prompt_template = ChatPromptTemplate.from_messages(
#     [("system", "You are a helpful assistant."), ("human", "{data}")]
# )


# model = ChatGroq(
#     model="openai/gpt-oss-20b",
#     temperature=0,
#     max_tokens=1024,
# )


# # Send one chunk to the model for testing
# prompt = template.format_messages(data=chunks[0].page_content)
# res=model.invoke(prompt)
# print(res.content)