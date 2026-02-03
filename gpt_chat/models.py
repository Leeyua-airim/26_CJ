from django.db import models


class Conversation(models.Model):
    """
    대화방(세션 단위로 1개를 만들고, 그 안에 메시지를 누적 저장합니다.)
    """

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation(id={self.id})"


class Message(models.Model):
    """
    대화 메시지
    - role: user / assistant / developer(또는 system) 등
    - content: 실제 텍스트
    """

    ROLE_CHOICES = (
        ("user", "user"),
        ("assistant", "assistant"),
        ("developer", "developer"),
        ("system", "system"),
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message(id={self.id}, role={self.role})"
