from typing import Any, Dict, List, Optional
from django.conf import settings


class PineconeRetriever:
    """
    Pinecone에서 벡터 검색을 수행합니다.
    - namespace: user_id
    - filter: project_id 기반
    """

    def __init__(self):
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY 가 설정되어 있지 않습니다.")
        if not settings.PINECONE_HOST:
            raise ValueError("PINECONE_HOST 가 설정되어 있지 않습니다.")

        from pinecone import Pinecone

        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(host=settings.PINECONE_HOST)

    def query(
        self,
        namespace: str,
        vector: List[float],
        project_id: int,
        top_k: int,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Pinecone query를 수행하고, match 리스트를 dict 형태로 반환합니다.
        """
        # project_id 단위로 scope 제한
        # Pinecone metadata filter는 flat JSON 기준입니다.
        flt = {"project_id": {"$eq": int(project_id)}}

        res = self.index.query(
            namespace=namespace,
            vector=vector,
            top_k=top_k,
            include_metadata=include_metadata,
            filter=flt,
        )

        matches: List[Dict[str, Any]] = []

        # SDK 응답 구조에 맞춰 안전하게 파싱
        # res.matches: [Match(id, score, metadata, values?)]
        for m in getattr(res, "matches", []) or []:
            matches.append(
                {
                    "id": getattr(m, "id", None),
                    "score": getattr(m, "score", None),
                    "metadata": getattr(m, "metadata", {}) or {},
                }
            )

        return matches
