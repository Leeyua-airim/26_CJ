from typing import Dict, List, Any
from django.conf import settings


class PineconeHostedReranker:
    """
    Pinecone Inference Rerank(호스티드) 호출 래퍼
    - bge-reranker-v2-m3 지원
    """

    def __init__(self):
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY 가 설정되어 있지 않습니다.")

        from pinecone import Pinecone
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 5,
        rank_fields: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Parameters:
            query: 사용자 질문
            documents: [{"id": "...", "chunk_text": "...", ...}, ...]
            top_n: rerank 후 반환 개수
            rank_fields: rerank에 사용할 필드명 리스트(기본 ["chunk_text"])

        Returns:
            [{"id": "...", "score": float, "document": {...}}, ...] 형태로 정리해 반환
        """
        if rank_fields is None:
            rank_fields = ["chunk_text"]

        # Pinecone rerank는 documents 개수 제한이 있으므로(모델별 상이),
        # Step6에서는 20개 후보 -> 5개로 줄이는 정도가 안전합니다.
        res = self.pc.inference.rerank(
            model="bge-reranker-v2-m3",
            query=query,
            documents=documents,
            top_n=top_n,
            rank_fields=rank_fields,
            return_documents=True,
            parameters={"truncate": "END"},
        )

        out: List[Dict[str, Any]] = []
        for item in getattr(res, "data", []) or []:
            doc = getattr(item, "document", None)
            if doc is None:
                continue

            out.append(
                {
                    "id": getattr(doc, "id", None),
                    "score": getattr(item, "score", None),
                    "document": doc.__dict__ if hasattr(doc, "__dict__") else doc,
                }
            )

        return out