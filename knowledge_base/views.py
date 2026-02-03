from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from agent_work.models import Project


@login_required
def kb_project(request, project_id):
    """
    프로젝트 지식베이스 화면(최소)

    Step 4 목표:
        - 업로드 폼
        - 문서 목록 표시
        - 업로드 후 문서/청크가 DB에 저장되는지 점검
    """
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    return render(
        request,
        "knowledge_base/kb_project.html",
        {"project": project},
    )
