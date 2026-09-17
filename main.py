from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv()  # Load environment variables from .env file 

# PDF loader
data = PyPDFLoader("document loader/deep-learning.pdf")
docs = data.load()


# Split the document into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(docs)


# Prompt template for the chat model
template = chat_prompt_template = ChatPromptTemplate.from_messages(
    [("system", "You are a helpful assistant."), ("human", "{data}")]
)


model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=1024,
)


# Send one chunk to the model for testing
prompt = template.format_messages(data=chunks[0].page_content)
res=model.invoke(prompt)
print(res.content)