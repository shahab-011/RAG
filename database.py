# load pdf 
# split into chunks
# create emb
# store intp chroma

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
emb model

load_dotenv()  # Load environment variables from .env file

loader = PyPDFLoader("document loader/deep-learning.pdf")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,    
    chubk_overlap=200
)   

embeddings = OpenAIEmbeddings()

vectorstore = Chroma.from_documents(
    documants = chunks,  
    embedding = embeddings,
    persist_directory = "chroma_db"     
) 