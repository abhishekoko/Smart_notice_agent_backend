# backend/utils/summarizer.py
from typing import List
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

class TransformerSummarizer:
    _instance = None

    def __new__(cls, model_name: str = "facebook/bart-large-cnn", device: int = -1):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init(model_name, device)
        return cls._instance

    def _init(self, model_name: str, device: int):
        self.model_name = model_name
        self.device = device
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self._pipe = pipeline("summarization", model=self._model, tokenizer=self._tokenizer, device=device)

    def _chunk_text(self, text: str, max_tokens: int = 800, overlap: int = 200) -> List[str]:
        tokens = self._tokenizer.encode(text, truncation=False)
        if len(tokens) <= max_tokens:
            return [text]

        chunks = []
        start = 0
        while start < len(tokens):
            end = min(len(tokens), start + max_tokens)
            chunk = tokens[start:end]
            chunk_text = self._tokenizer.decode(chunk, skip_special_tokens=True)
            chunks.append(chunk_text)
            if end == len(tokens):
                break
            start += max_tokens - overlap
        return chunks

    def summarize(self, text: str, min_length: int = 30, max_length: int = 120) -> str:
        text = text.strip()
        if not text:
            return ""

        # 🚀 NEW: If text is less than 15 words, skip summarizing
        if len(text.split()) < 15:
            return text

        chunks = self._chunk_text(text)
        summaries = []
        for chunk in chunks:
            result = self._pipe(
                chunk,
                min_length=min_length,
                max_length=max_length,
                truncation=True
            )
            summaries.append(result[0]["summary_text"].strip())

        if len(summaries) > 1:
            combined = " ".join(summaries)
            final = self._pipe(
                combined,
                min_length=min_length,
                max_length=max_length,
                truncation=True
            )
            return final[0]["summary_text"].strip()

        return summaries[0]
