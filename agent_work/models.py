from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    """
    사용자(=Workspace) 하위의 작업 단위(Project)입니다.

    설계 규칙:
        - PoC: 사용자당 최대 3개
        - 지식베이스/대화는 Project 단위로 분리됩니다.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    name = models.CharField(max_length=80)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.owner_id}:{self.name}"


class WorkConversation(models.Model):
    """
    Project 하위의 대화 컨테이너입니다.

    사용 의도:
        - 대화방 전환(드롭다운) 기준이 되는 모델
        - 템플릿(단기/중기/장기)은 이후 Step 6에서 프롬프트 구성에 사용합니다.
    """

    TEMPLATE_CHOICES = (
        ("short", "단기"),
        ("mid", "중기"),
        ("long", "장기"),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    title = models.CharField(max_length=120, default="새 대화")
    template_type = models.CharField(max_length=10, choices=TEMPLATE_CHOICES, default="short")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def touch(self):
        """
        대화가 갱신되었음을 표시하기 위해 updated_at을 갱신합니다.
        """
        self.updated_at = timezone.now()
        self.save(update_fields=["updated_at"])

    def __str__(self):
        return f"{self.project_id}:{self.title}"


class WorkMessage(models.Model):
    """
    Conversation 하위의 메시지입니다.

    role:
        - user: 사용자 입력
        - assistant: 모델 응답(현재 Step 3-3에서는 임시 문구로 저장)
    """

    ROLE_CHOICES = (
        ("user", "user"),
        ("assistant", "assistant"),
    )

    conversation = models.ForeignKey(
        WorkConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()

    # Step 6~에서 OpenAI response_id, 사용 chunk ids 등 확장용
    meta = models.JSONField(blank=True, default=dict)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.conversation_id}:{self.role}:{self.created_at}"
