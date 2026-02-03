import os
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from agent_work.models import Project
from .models import KBDocument, KBChunk
from .utils import (
    extract_text_from_excel,
    extract_text_from_pdf,
    build_units_from_text,
    chunk_with_context,
    safe_get_extension,
)
from django.db.models import Q
from django.db import transaction

from .services.openai_embeddings import OpenAIEmbeddingClient
from .services.pinecone_indexer import PineconeIndexer

MAX_UPLOAD_BYTES = 30 * 1024 * 1024  # 30MB
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".pdf"}


def parse_tags(raw: str):
    """
    쉼표 기반 태그 파싱
    """
    if raw is None:
        return []

    text = str(raw).strip()
    if not text:
        return []

    parts = text.split(",")
    tags = []
    for p in parts:
        t = p.strip()
        if t:
            tags.append(t)
    return tags


@login_required
@require_http_methods(["POST"])
def upload_document(request, project_id):
    """
    문서 업로드 API

    입력:
        - file: multipart file (.xlsx/.xls/.pdf)
        - importance: 1~5
        - tags: "태그1,태그2"
        - title: 문서 제목(선택, 없으면 파일명)
    동작:
        - 30MB 제한
        - 텍스트 추출
        - 청킹 생성(window=1)
        - KBDocument, KBChunk 저장
    """
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "file_required"}, status=400)

    if f.size > MAX_UPLOAD_BYTES:
        return JsonResponse({"error": "file_too_large", "max_mb": 30}, status=400)

    ext = safe_get_extension(f.name)
    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse({"error": "invalid_extension", "allowed": list(ALLOWED_EXTENSIONS)}, status=400)

    raw_importance = request.POST.get("importance", "3")
    try:
        importance = int(raw_importance)
    except ValueError:
        importance = 3

    if importance < 1:
        importance = 1
    if importance > 5:
        importance = 5

    title = request.POST.get("title", "").strip()
    if not title:
        title = f.name

    tags = parse_tags(request.POST.get("tags", ""))

    # 임시 저장 경로
    tmp_dir = os.path.join(settings.MEDIA_ROOT, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    tmp_name = f"{uuid.uuid4().hex}{ext}"
    tmp_path = os.path.join(tmp_dir, tmp_name)

    # 파일 저장
    with open(tmp_path, "wb") as fp:
        for chunk in f.chunks():
            fp.write(chunk)

    extracted_text = ""
    source_type = "text"

    try:
        if ext in {".xlsx", ".xls"}:
            extracted_text = extract_text_from_excel(tmp_path)
            source_type = "excel"
        elif ext == ".pdf":
            extracted_text = extract_text_from_pdf(tmp_path)
            source_type = "pdf"
    finally:
        # 원문 보관/다운로드는 보류 → 임시 파일 삭제
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    extracted_text = (extracted_text or "").strip()
    if not extracted_text:
        return JsonResponse({"error": "no_text_extracted"}, status=400)

    # 문서 저장
    doc = KBDocument.objects.create(
        owner=request.user,
        project=project,
        title=title,
        source_type=source_type,
        importance=importance,
        tags=tags,
        extracted_text=extracted_text,
        original_filename=f.name,
        file_size=f.size,
    )

    # 청킹
    units = build_units_from_text(extracted_text)
    chunks = chunk_with_context(units, window=1, max_chars=1200)

    created_count = 0
    idx = 0
    while idx < len(chunks):
        chunk_text = chunks[idx].strip()
        if chunk_text:
            KBChunk.objects.create(
                document=doc,
                chunk_index=idx,
                chunk_text=chunk_text,
                importance=importance,
                tags=tags,
            )
            created_count = created_count + 1
        idx = idx + 1

    return JsonResponse(
        {
            "document": {
                "id": doc.id,
                "title": doc.title,
                "source_type": doc.source_type,
                "importance": doc.importance,
                "tags": doc.tags,
                "file_size": doc.file_size,
            },
            "chunks_created": created_count,
        }
    )


@login_required
@require_http_methods(["GET"])
def document_list(request, project_id):
    """
    프로젝트 문서 목록
    """
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    docs = KBDocument.objects.filter(project=project).order_by("-created_at")

    items = []
    for d in docs:
        items.append(
            {
                "id": d.id,
                "title": d.title,
                "source_type": d.source_type,
                "importance": d.importance,
                "tags": d.tags,
                "created_at": d.created_at.isoformat(),
            }
        )

    return JsonResponse({"documents": items})


@login_required
@require_http_methods(["GET"])
def chunk_list(request, document_id):
    """
    문서 청크 목록(미리보기용)
    """
    doc = get_object_or_404(KBDocument, id=document_id, owner=request.user)

    chunks = KBChunk.objects.filter(document=doc).order_by("chunk_index")

    items = []
    for c in chunks[:200]:  # PoC: 과도한 응답 방지
        items.append(
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "importance": c.importance,
                "text_preview": c.chunk_text[:300],
            }
        )

    return JsonResponse({"chunks": items})

@login_required
@require_http_methods(["POST"])
def index_project_chunks(request, project_id: int):
    """
    프로젝트 내 KBChunk를 임베딩 후 Pinecone upsert 합니다.

    필터(넓게 커버):
        - pinecone_id is NULL
        - pinecone_id == ""
        - indexed_at is NULL
        - embedding_model is NULL
        - embedding_dim is NULL
        - embedding_model != 현재 모델
        - embedding_dim != 현재 dim

    Query params (선택):
        - limit: 이번 요청에서 처리할 최대 chunk 수(기본 300)
        - batch: 임베딩/업서트 배치 크기(기본 64)
        - force=1: 강제로 전체 재인덱싱(테스트용)
    """
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    # namespace = user_id (요구사항)
    namespace = str(request.user.id)

    # 파라미터
    raw_limit = request.GET.get("limit", "300")
    raw_batch = request.GET.get("batch", "64")
    raw_force = request.GET.get("force", "0")

    try:
        limit = int(raw_limit)
    except ValueError:
        limit = 300

    try:
        batch_size = int(raw_batch)
    except ValueError:
        batch_size = 64

    force = False
    if str(raw_force).strip() == "1":
        force = True

    if limit < 1:
        limit = 1
    if limit > 2000:
        limit = 2000

    if batch_size < 1:
        batch_size = 1
    if batch_size > 256:
        batch_size = 256

    # 넓은 필터 조건
    current_model = settings.OPENAI_EMBEDDING_MODEL
    current_dim = settings.OPENAI_EMBEDDING_DIM

    need_index_q = (
        Q(pinecone_id__isnull=True)
        | Q(pinecone_id__exact="")
        | Q(indexed_at__isnull=True)
        | Q(embedding_model__isnull=True)
        | Q(embedding_dim__isnull=True)
        | ~Q(embedding_model=current_model)
        | ~Q(embedding_dim=current_dim)
    )

    base_qs = KBChunk.objects.filter(
        document__project=project,
        document__owner=request.user,
    )

    if force:
        target_qs = base_qs
    else:
        target_qs = base_qs.filter(need_index_q)

    # 과도한 처리 방지
    target_qs = target_qs.order_by("document_id", "chunk_index")[:limit]

    targets = []
    for ch in target_qs:
        targets.append(ch)

    if len(targets) == 0:
        return JsonResponse(
            {
                "indexed_count": 0,
                "message": "처리 대상 청크가 없습니다.",
            }
        )

    embedder = OpenAIEmbeddingClient()
    pinecone = PineconeIndexer()

    indexed_count = 0

    start = 0
    while start < len(targets):
        end = start + batch_size
        batch = targets[start:end]

        # 1) 임베딩 입력 텍스트 준비
        texts = []
        for ch in batch:
            texts.append(ch.chunk_text)

        # 2) 임베딩 생성
        vectors = embedder.embed_texts(texts)

        # 3) Pinecone upsert items 구성
        upsert_items = []
        i = 0
        while i < len(batch):
            ch = batch[i]
            vec = vectors[i]

            # 이미 pinecone_id가 있으면 재사용(불완전 인덱싱 복구에 유리)
            chosen_id = None
            if ch.pinecone_id is not None:
                pid = str(ch.pinecone_id).strip()
                if pid != "":
                    chosen_id = pid

            if chosen_id is None:
                # deterministic id: user/project/document/chunk 기반
                chosen_id = f"u{request.user.id}-p{project.id}-d{ch.document_id}-c{ch.chunk_index}"

            doc = ch.document

            meta = {
                "user_id": int(request.user.id),
                "project_id": int(project.id),
                "document_id": int(doc.id),
                "chunk_index": int(ch.chunk_index),
                "kb_chunk_id": int(ch.id),
                "importance": int(ch.importance),
            }

            if doc.title:
                meta["doc_title"] = str(doc.title)

            if doc.source_type:
                meta["source_type"] = str(doc.source_type)

            # tags는 list[str] 형태로 보장
            if doc.tags:
                if isinstance(doc.tags, list):
                    meta["tags"] = [str(x) for x in doc.tags]
                else:
                    meta["tags"] = [str(doc.tags)]

            upsert_items.append((chosen_id, vec, meta))
            i = i + 1

        # 4) Pinecone upsert 실행
        pinecone.upsert_vectors(namespace=namespace, vectors=upsert_items)

        # 5) DB 갱신(트랜잭션)
        with transaction.atomic():
            j = 0
            while j < len(batch):
                ch = batch[j]
                chosen_id = upsert_items[j][0]

                ch.mark_indexed(
                    pinecone_id=chosen_id,
                    model=current_model,
                    dim=current_dim,
                )
                ch.save(
                    update_fields=[
                        "pinecone_id",
                        "indexed_at",
                        "embedding_model",
                        "embedding_dim",
                    ]
                )
                j = j + 1

        indexed_count = indexed_count + len(batch)
        start = end

    return JsonResponse(
        {
            "indexed_count": indexed_count,
            "limit": limit,
            "batch_size": batch_size,
            "force": force,
        }
    )