import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from langchain_core.embeddings import Embeddings

class LocalHuggingFaceEmbeddings(Embeddings):
    """
    Local Hugging Face embeddings using sentence-transformers/all-MiniLM-L6-v2.
    Runs locally on machine using PyTorch and Transformers without requiring any API keys.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        encoded_input = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            model_output = self.model(**encoded_input)
        sentence_embeddings = self._mean_pooling(model_output, encoded_input["attention_mask"])
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        return sentence_embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
