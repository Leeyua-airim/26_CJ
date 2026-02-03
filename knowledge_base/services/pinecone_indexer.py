from typing import Any, Dict, List, Tuple
from django.conf import settings


class PineconeIndexer:
    """
    Pinecone upsert 전용 래퍼

    - Index(host=...) 방식 사용
    - namespace는 user_id 문자열 사용(요구사항)
    """

    def __init__(self):
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY 가 설정되어 있지 않습니다.")
        if not settings.PINECONE_HOST:
            raise ValueError("PINECONE_HOST 가 설정되어 있지 않습니다.")

        from pinecone import Pinecone

        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(host=settings.PINECONE_HOST)

    def upsert_vectors(
        self,
        namespace: str,
        vectors: List[Tuple[str, List[float], Dict[str, Any]]],
    ):
        """
        vectors: (id, values, metadata) 튜플 리스트

        metadata는 flat JSON + 제한된 타입을 지켜야 합니다.
        """
        return self.index.upsert(vectors=vectors, namespace=namespace)
