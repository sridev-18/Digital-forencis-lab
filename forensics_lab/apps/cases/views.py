from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from apps.accounts.models import AuditLog, User
from .models import Case, CaseNote


@login_required
def dashboard_view(request):
    """Main dashboard — summary stats + recent cases."""
    user = request.user
    if user.is_admin():
        cases = Case.objects.all()
    elif user.is_investigator():
        cases = Case.objects.filter(
            Q(created_by=user) | Q(assigned_to=user)
        ).distinct()
    else:
        cases = Case.objects.filter(assigned_to=user)

    stats = {
        "total": cases.count(),
        "open": cases.filter(status=Case.Status.OPEN).count(),
        "active": cases.filter(status=Case.Status.ACTIVE).count(),
        "critical": cases.filter(priority=Case.Priority.CRITICAL).count(),
    }
    recent_cases = cases.order_by("-updated_at")[:10]
    recent_logs = AuditLog.objects.order_by("-timestamp")[:10]

    return render(request, "cases/dashboard.html", {
        "stats": stats,
        "recent_cases": recent_cases,
        "recent_logs": recent_logs,
    })


@login_required
def case_list_view(request):
    user = request.user
    if user.is_admin():
        cases = Case.objects.all()
    else:
        cases = Case.objects.filter(
            Q(created_by=user) | Q(assigned_to=user)
        ).distinct()

    # Filtering
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    search = request.GET.get("q")

    if status:
        cases = cases.filter(status=status)
    if priority:
        cases = cases.filter(priority=priority)
    if search:
        cases = cases.filter(
            Q(title__icontains=search) |
            Q(case_number__icontains=search) |
            Q(description__icontains=search)
        )

    return render(request, "cases/case_list.html", {
        "cases": cases.order_by("-updated_at"),
        "status_choices": Case.Status.choices,
        "priority_choices": Case.Priority.choices,
    })


@login_required
def case_create_view(request):
    if not request.user.is_investigator():
        messages.error(request, "Investigator access required to create cases.")
        return redirect("cases:list")

    if request.method == "POST":
        case = Case.objects.create(
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            case_type=request.POST.get("case_type"),
            priority=request.POST.get("priority", "medium"),
            incident_location=request.POST.get("incident_location", ""),
            suspect_name=request.POST.get("suspect_name", ""),
            victim_name=request.POST.get("victim_name", ""),
            jurisdiction=request.POST.get("jurisdiction", ""),
            created_by=request.user,
        )
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.CREATE,
            resource_type="Case",
            resource_id=str(case.id),
            description=f"Created case {case.case_number}: {case.title}",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        messages.success(request, f"Case {case.case_number} created successfully.")
        return redirect("cases:detail", pk=case.pk)

    return render(request, "cases/case_form.html", {
        "case_types": Case.CaseType.choices,
        "priority_choices": Case.Priority.choices,
        "analysts": User.objects.filter(is_active=True),
    })


@login_required
def case_detail_view(request, pk):
    case = get_object_or_404(Case, pk=pk)

    AuditLog.objects.create(
        user=request.user,
        action=AuditLog.Action.READ,
        resource_type="Case",
        resource_id=str(case.id),
        description=f"Viewed case {case.case_number}",
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    notes = case.notes.filter(
        Q(is_private=False) | Q(author=request.user)
    ).order_by("-created_at")

    return render(request, "cases/case_detail.html", {
        "case": case,
        "evidence_list": case.evidence_set.order_by("-uploaded_at"),
        "notes": notes,
        "analysis_tasks": case.analysis_tasks.order_by("-created_at"),
    })


@login_required
def case_update_view(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if not request.user.is_investigator():
        messages.error(request, "Investigator access required.")
        return redirect("cases:detail", pk=pk)

    if request.method == "POST":
        case.title = request.POST.get("title", case.title)
        case.description = request.POST.get("description", case.description)
        case.status = request.POST.get("status", case.status)
        case.priority = request.POST.get("priority", case.priority)
        case.incident_location = request.POST.get("incident_location", case.incident_location)
        case.suspect_name = request.POST.get("suspect_name", case.suspect_name)
        case.save()

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            resource_type="Case",
            resource_id=str(case.id),
            description=f"Updated case {case.case_number}",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        messages.success(request, "Case updated.")
        return redirect("cases:detail", pk=pk)

    return render(request, "cases/case_form.html", {
        "case": case,
        "case_types": Case.CaseType.choices,
        "priority_choices": Case.Priority.choices,
        "status_choices": Case.Status.choices,
        "analysts": User.objects.filter(is_active=True),
    })


@login_required
def add_note_view(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            CaseNote.objects.create(
                case=case,
                author=request.user,
                content=content,
                is_private=request.POST.get("is_private") == "on",
            )
            messages.success(request, "Note added.")
    return redirect("cases:detail", pk=pk)
