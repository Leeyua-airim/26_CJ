from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import ProfileCompleteForm

from agent_work.models import Project
from django.db import transaction


@login_required
def app_home(request):
    """
    /app/ 대시보드

    동작:
        - 사용자 프로젝트 목록 표시
        - PoC: 최대 3개 생성 가능
    """
    user = request.user

    projects = Project.objects.filter(owner=user).order_by("-created_at")

    can_create = True
    if projects.count() >= 3:
        can_create = False

    return render(
        request,
        "core/app_dashboard.html",
        {
            "projects": projects,
            "can_create": can_create,
        },
    )

@login_required
def project_create(request):
    """
    프로젝트 생성

    규칙:
        - PoC: 사용자당 최대 3개
        - name 필수
    """
    if request.method != "POST":
        return redirect("/app/")

    user = request.user

    current_count = Project.objects.filter(owner=user).count()
    if current_count >= 3:
        return redirect("/app/")

    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()

    if not name:
        return redirect("/app/")

    with transaction.atomic():
        Project.objects.create(
            owner=user,
            name=name,
            description=description,
        )

    return redirect("/app/")


@login_required
def profile_complete(request):
    """
    소셜 로그인 사용자가 /app/ 기능을 사용하기 전에 필수 프로필을 채우도록 유도합니다.
    """
    user = request.user

    if user.affiliation and user.employee_no and user.full_name:
        return redirect("/app/")

    if request.method == "POST":
        form = ProfileCompleteForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("/app/")
    else:
        form = ProfileCompleteForm(instance=user)

    return render(request, "core/profile_complete.html", {"form": form})
