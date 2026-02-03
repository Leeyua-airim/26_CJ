from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from .models import Project, WorkConversation


@login_required
def agent_project(request, project_id):
    """
    프로젝트 단위 Agent 화면입니다.

    Step 3-3 목표:
        - Project 접근 권한(owner) 검증
        - Conversation 목록 로딩
        - 대화가 없으면 기본 대화 1개 자동 생성
        - 템플릿에서 드롭다운으로 대화 전환 가능하게 준비
    """
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    conversations = WorkConversation.objects.filter(project=project).order_by("-updated_at")

    if conversations.count() == 0:
        WorkConversation.objects.create(
            project=project,
            title="기본 대화",
            template_type="short",
        )
        conversations = WorkConversation.objects.filter(project=project).order_by("-updated_at")

    return render(
        request,
        "agent_work/agent_project.html",
        {
            "project": project,
            "conversations": conversations,
        },
    )
