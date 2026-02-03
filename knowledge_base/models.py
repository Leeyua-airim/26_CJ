from django.conf import settings
from django.db import models
from django.utils import timezone

from agent_work.models import Project


class KBDocument(models.Model):
    """
    Project 단위 지식베이스 원천 문서 메타

    주의:
        - PoC에서는 원문 파일 다운로드는 보류
        - 원문 텍스트는 제목/요약 수준만 노출(관리/개발 편의)
        - 실제 검색/임베딩은 KBChunk 단위로 수행합니다.
    """

    SOURCE_CHOICES = (
        ("excel", "excel"),
        ("pdf", "pdf"),
        ("text", "text"),
    )

    IMPORTANCE_CHOICES = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="kb_documents",
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="kb_documents",
    )

    title = models.CharField(max_length=200)
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)

    # 업로드 시 입력하는 중요도(1=약한 힌트, 5=정답 기준)
    importance = models.IntegerField(choices=IMPORTANCE_CHOICES, default=3)

    # 문서 전체 태그(우선 문서 단위로만 적용)
    tags = models.JSONField(blank=True, default=list)

    # 원문 전체 텍스트는 저장하되, 화면 노출은 최소화(보류 정책 반영)
    extracted_text = models.TextField(blank=True, default="")

    # 파일 메타(다운로드는 보류, 필요시 추후 확장)
    original_filename = models.CharField(max_length=255, blank=True, default="")
    file_size = models.IntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.project_id}:{self.title}"


class KBChunk(models.Model):
    """
    검색/임베딩/근거 표시는 Chunk 단위로 수행합니다.

    Step 4:
        - chunk_text 저장
        - chunk_index 저장
        - importance는 document의 값을 기본 상속
        - tags는 문서 태그를 기본 상속(추후 chunk 태그 확장 가능)
    """

    document = models.ForeignKey(
        KBDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
    )

    chunk_index = models.IntegerField(default=0)
    chunk_text = models.TextField()

    # 문서 중요도 상속(검색/프롬프트 가중치에 사용)
    importance = models.IntegerField(default=3)

    # chunk 태그(현재는 문서 태그 복사)
    tags = models.JSONField(blank=True, default=list)
    

    pinecone_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        db_index=True,
        help_text="Pinecone vector id (upsert 완료 시 저장)",
    )

    indexed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Pinecone upsert 완료 시각",
    )

    embedding_model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="임베딩 모델명(예: text-embedding-3-large)",
    )

    embedding_dim = models.IntegerField(
        blank=True,
        null=True,
        help_text="임베딩 차원(예: 1024)",
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index"],
                name="uq_kbchunk_document_chunkindex",
            )
        ]

    def mark_indexed(self, pinecone_id: str, model: str, dim: int) -> None:
        """
        upsert 완료 표기를 수행합니다.

        Parameters:
            pinecone_id (str): Pinecone에 저장된 벡터 ID
            model (str): 임베딩 모델명
            dim (int): 임베딩 차원수

        Returns:
            None: DB 필드만 갱신합니다.
        """
        self.pinecone_id = pinecone_id
        self.indexed_at = timezone.now()
        self.embedding_model = model
        self.embedding_dim = dim

    def __str__(self):
        return f"{self.document_id}:{self.chunk_index}"
