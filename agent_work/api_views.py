import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import Project, WorkConversation, WorkMessage
from knowledge_base.services.pinecone_retriever import PineconeRetriever

from knowledge_base.services.openai_embeddings import OpenAIEmbeddingClient
from knowledge_base.services.pinecone_retriever import PineconeRetriever
from knowledge_base.services.rag_context import (
    sort_matches_with_importance,
    build_context_snippets,
    build_system_rules,
)

from knowledge_base.models import KBChunk  # kb_chunk_id로 텍스트/미리보기 가져오려면 필요

@login_required
@require_http_methods(["GET", "POST"])
def conversation_list_create(request, project_id):
    """
    GET:
        - 프로젝트의 대화 목록 조회
    POST:
        - 새 대화 생성
    """
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    if request.method == "GET":
        conversations = WorkConversation.objects.filter(project=project).order_by("-updated_at")

        items = []
        for c in conversations:
            items.append(
                {
                    "id": c.id,
                    "title": c.title,
                    "template_type": c.template_type,
                    "template_label": c.get_template_type_display(),
                    "updated_at": c.updated_at.isoformat(),
                }
            )

        return JsonResponse({"conversations": items})

    # POST
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        body = {}

    title = body.get("title", "새 대화")
    template_type = body.get("template_type", "short")

    conv = WorkConversation.objects.create(
        project=project,
        title=title,
        template_type=template_type,
    )

    return JsonResponse(
        {
            "conversation": {
                "id": conv.id,
                "title": conv.title,
                "template_type": conv.template_type,
                "template_label": conv.get_template_type_display(),
            }
        }
    )


@login_required
@require_http_methods(["GET"])
def message_list(request, conversation_id):
    """
    선택한 대화(conversation)의 메시지 목록 조회
    """
    conv = get_object_or_404(WorkConversation, id=conversation_id, project__owner=request.user)
    msgs = WorkMessage.objects.filter(conversation=conv).order_by("created_at")

    items = []
    for m in msgs:
        items.append(
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
        )

    return JsonResponse({"messages": items})


# (Step6-추가) Pinecone rerank(외부 API)
from knowledge_base.services.pinecone_reranker import PineconeHostedReranker


def parse_bool(value) -> bool:
    """
    JS에서 넘어오는 문자열 "false" 등이 bool("false")==True로 오동작하는 것을 방지합니다.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    s = str(value).strip().lower()
    if s in ["1", "true", "yes", "y", "on"]:
        return True
    return False



@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id: int):
    """
    Step6: RAG 연결된 메시지 전송 API
    - URL의 conversation_id만 신뢰합니다.
    - 프로젝트 스코프는 conv.project로 제한됩니다.
    - namespace는 user_id로 분리되어 있으므로 user scope도 자연히 제한됩니다.
    """

    # 1) JSON 파싱
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "요청 바디가 JSON 형식이 아닙니다."}, status=400)

    user_text = str(payload.get("message") or "").strip()
    if user_text == "":
        return JsonResponse({"error": "message 가 비었습니다."}, status=400)

    use_reranker = parse_bool(payload.get("use_reranker", False))

    # 2) conversation 조회 + 소유권 검증(매우 중요)
    conv = get_object_or_404(
        WorkConversation.objects.select_related("project"),
        id=int(conversation_id),
        project__owner=request.user,
    )
    project = conv.project

    # 3) 사용자 메시지 저장
    user_msg = WorkMessage.objects.create(
        conversation=conv,
        role="user",
        content=user_text,
    )

    # 4) 임베딩 생성
    embedder = OpenAIEmbeddingClient()
    query_vec = embedder.embed_texts([user_text])[0]

    # 5) Pinecone 검색(top_k 넉넉히)
    retriever = PineconeRetriever()
    raw_matches = retriever.query(
        namespace=str(request.user.id),
        vector=query_vec,
        project_id=project.id,
        top_k=30,
        include_metadata=True,
    )

    # 6) importance 반영 정렬
    sorted_matches = sort_matches_with_importance(raw_matches)

    # 7) match -> KBChunk 매핑 (kb_chunk_id 우선, 없으면 pinecone_id로 역조회)
    candidates = []
    i = 0
    while i < len(sorted_matches):
        m = sorted_matches[i]
        pinecone_id = m.get("id")
        meta = m.get("metadata", {}) or {}

        kb_chunk_id = meta.get("kb_chunk_id")

        ch = None
        if kb_chunk_id:
            try:
                ch = KBChunk.objects.select_related("document").get(
                    id=int(kb_chunk_id),
                    document__project=project,
                    document__owner=request.user,
                )
            except KBChunk.DoesNotExist:
                ch = None
        else:
            if pinecone_id:
                try:
                    ch = KBChunk.objects.select_related("document").get(
                        pinecone_id=str(pinecone_id),
                        document__project=project,
                        document__owner=request.user,
                    )
                except KBChunk.DoesNotExist:
                    ch = None

        if ch is not None:
            candidates.append(
                {
                    "pinecone_id": str(pinecone_id),
                    "kb_chunk": ch,
                    "score": m.get("score"),
                    "final_score": m.get("final_score"),
                }
            )

        i = i + 1

    # 8) (옵션) Pinecone rerank(bge-reranker-v2-m3)
    #    - 안정성 우선: 실패하면 rerank 없이 진행
    if use_reranker and len(candidates) > 0:
        reranker = PineconeHostedReranker()

        docs = []
        j = 0
        while j < len(candidates):
            ch = candidates[j]["kb_chunk"]
            docs.append(
                {
                    "id": candidates[j]["pinecone_id"],
                    "text": ch.chunk_text,
                }
            )
            j = j + 1

        try:
            reranked = reranker.rerank(
                query=user_text,
                documents=docs,
                top_n=8,
                rank_fields=["text"],
            )

            order = []
            k = 0
            while k < len(reranked):
                rid = reranked[k].get("id")
                if rid:
                    order.append(str(rid))
                k = k + 1

            new_candidates = []
            k = 0
            while k < len(order):
                target_id = order[k]

                t = 0
                while t < len(candidates):
                    if candidates[t]["pinecone_id"] == target_id:
                        new_candidates.append(candidates[t])
                        break
                    t = t + 1

                k = k + 1

            if len(new_candidates) > 0:
                candidates = new_candidates

        except Exception:
            pass

    # 9) 프롬프트 구성(importance 반영: 높은 것 우선, 최대 8개)
    context_blocks = []
    c = 0
    while c < len(candidates) and c < 8:
        ch = candidates[c]["kb_chunk"]
        title = ch.document.title
        imp = ch.importance
        idx = ch.chunk_index

        block = (
            f"[문서: {title} | chunk #{idx} | importance={imp}]\n"
            f"{ch.chunk_text}\n"
        )
        context_blocks.append(block)

        c = c + 1

    context_text = "\n\n".join(context_blocks).strip()

    # 10) GPT 호출
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_rules = build_system_rules()

    messages = []
    messages.append({"role": "system", "content": system_rules})

    if context_text != "":
        messages.append({"role": "system", "content": f"아래는 사용자가 업로드한 지식베이스 근거입니다.\n\n{context_text}"})
    else:
        messages.append({"role": "system", "content": "지식베이스 근거가 비어있습니다. 근거가 없으면 단정하지 말고 추가 정보를 요청하십시오."})

    messages.append({"role": "user", "content": user_text})

    resp = client.chat.completions.create(
        model="gpt-5.2",
        messages=messages,
    )

    answer_text = resp.choices[0].message.content or ""

    # 11) assistant 메시지 저장
    asst_msg = WorkMessage.objects.create(
        conversation=conv,
        role="assistant",
        content=answer_text,
    )

    # 12) Step7 대비: 근거 Top-5 반환
    evidence = []
    e = 0
    while e < len(candidates) and e < 5:
        ch = candidates[e]["kb_chunk"]
        evidence.append(
            {
                "kb_chunk_id": ch.id,
                "pinecone_id": ch.pinecone_id,
                "document_id": ch.document_id,
                "doc_title": ch.document.title,
                "chunk_index": ch.chunk_index,
                "importance": ch.importance,
                "tags": ch.tags,
                "text_preview": (ch.chunk_text[:300] + "...") if len(ch.chunk_text) > 300 else ch.chunk_text,
            }
        )
        e = e + 1

    return JsonResponse(
        {
            "message_id": asst_msg.id,
            "answer": answer_text,
            "evidence_top5": evidence,
            "use_reranker": use_reranker,
        }
    )