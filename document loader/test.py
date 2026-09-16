from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("document loader/synopsis.pdf")

docs = loader.load()

print(len(docs))