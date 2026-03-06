from app.domain.interfaces import EmbedderInterface
from openai import OpenAI

class OpenAIEmbedder(EmbedderInterface):
    def __init__(self, api_key: str, model_name: str):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
    
    def embed_text(self, text: str) -> list[float]:
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise ValueError("Text cannot be empty.")
        
        response = self.client.embeddings.create(input=cleaned_text, model=self.model_name)
        
        return response.data[0].embedding
