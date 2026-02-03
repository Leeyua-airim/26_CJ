from typing import List
from django.conf import settings


class OpenAIEmbeddingClient:
    """
    OpenAI Embeddings 래퍼

    - model: settings.OPENAI_EMBEDDING_MODEL (text-embedding-3-large)
    - dimensions: settings.OPENAI_EMBEDDING_DIM (1024)
    """

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 가 설정되어 있지 않습니다.")

        from openai import OpenAI
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        입력 텍스트 리스트를 임베딩 벡터 리스트로 변환합니다.

        Parameters:
            texts (List[str]): 임베딩 대상 텍스트 목록

        Returns:
            List[List[float]]: 임베딩 벡터(각 벡터 차원=1024)
        """
        cleaned: List[str] = []

        for t in texts:
            if t is None:
                cleaned.append("")
                continue

            s = str(t).replace("\n", " ").strip()

            # PoC 안전장치: 지나치게 긴 텍스트는 임시로 절단
            if len(s) > 6000:
                s = s[:6000]

            cleaned.append(s)

        response = self.client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=cleaned,
            dimensions=settings.OPENAI_EMBEDDING_DIM,
            encoding_format="float",
        )

        vectors: List[List[float]] = []

        for item in response.data:
            vectors.append(item.embedding)

        # 차원 점검(인덱스 차원 mismatch를 조기에 발견)
        for v in vectors:
            if len(v) != settings.OPENAI_EMBEDDING_DIM:
                raise ValueError(
                    f"Embedding dim mismatch: expected={settings.OPENAI_EMBEDDING_DIM}, got={len(v)}"
                )

        return vectors
