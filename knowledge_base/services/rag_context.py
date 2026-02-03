from typing import Any, Dict, List, Tuple


def normalize_importance(x: int) -> float:
    """
    importance(1~5)를 0~1로 정규화합니다.
    """
    if x < 1:
        x = 1
    if x > 5:
        x = 5
    return (x - 1) / 4.0


def sort_matches_with_importance(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Pinecone score와 importance를 간단히 결합해 정렬합니다.
    - 안정성 우선: 과격한 재정렬 대신, score 우선 + importance 약간 가산
    """
    scored: List[Tuple[float, Dict[str, Any]]] = []

    for m in matches:
        meta = m.get("metadata", {}) or {}
        imp = int(meta.get("importance", 3))
        imp_w = normalize_importance(imp)

        score = m.get("score", 0.0) or 0.0

        # 간단 결합(가산). 필요하면 곱산으로 바꿀 수 있습니다.
        # importance=5면 +0.15, importance=1이면 +0.0 정도의 효과
        final_score = float(score) + (0.15 * imp_w)

        scored.append((final_score, m))

    scored.sort(key=lambda x: x[0], reverse=True)

    out: List[Dict[str, Any]] = []
    for s, m in scored:
        mm = dict(m)
        mm["final_score"] = s
        out.append(mm)

    return out


def build_context_snippets(
    matches: List[Dict[str, Any]],
    max_snippets: int = 8,
) -> List[Dict[str, Any]]:
    """
    LLM 프롬프트에 넣을 컨텍스트 목록을 생성합니다.
    - 중요도 높은 것 우선
    - Step7에서 근거 Top-5 표시에도 그대로 재사용 가능하도록 구조화합니다.
    """
    # 이미 정렬된 matches가 들어온다고 가정
    snippets: List[Dict[str, Any]] = []

    for m in matches:
        if len(snippets) >= max_snippets:
            break

        meta = m.get("metadata", {}) or {}

        snippets.append(
            {
                "pinecone_id": m.get("id"),
                "score": m.get("score"),
                "final_score": m.get("final_score"),
                "project_id": meta.get("project_id"),
                "document_id": meta.get("document_id"),
                "chunk_index": meta.get("chunk_index"),
                "importance": meta.get("importance", 3),
                "doc_title": meta.get("doc_title", ""),
                "source_type": meta.get("source_type", ""),
                "tags": meta.get("tags", []),
                # chunk_text는 Pinecone metadata에 넣지 않으셨으므로
                # DB에서 kb_chunk_id로 가져오는 방식이 Step7에 유리합니다.
                "kb_chunk_id": meta.get("kb_chunk_id"),
            }
        )

    return snippets


def build_system_rules() -> str:
    """
    importance 규칙을 시스템/지침에 반영합니다.
    """
    return (
        "당신은 조직의 HR 분석 및 커리어 개발 지원 업무를 돕는 에이전트입니다.\n"
        "다음 규칙을 반드시 지키십시오.\n"
        "1) 제공된 근거(컨텍스트)를 최우선으로 사용합니다.\n"
        "2) importance=5 근거는 '정답 기준'으로 최대한 따릅니다.\n"
        "3) 근거가 서로 충돌하거나 근거가 부족하면, 임의로 단정하지 말고 '근거 부족/상충'을 명시합니다.\n"
        "4) 근거에 없는 내용은 추정하지 말고, 필요한 추가 정보를 요청합니다.\n"
    )
