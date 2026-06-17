from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.cases.models import Case
from apps.evidence.models import Evidence
from .models import AnalysisTask, TimelineEvent
from .tasks import run_full_analysis


@login_required
def analysis_list_view(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    tasks = AnalysisTask.objects.filter(case=case).order_by("-created_at")
    return render(request, "analysis/list.html", {"case": case, "tasks": tasks})


@login_required
def analysis_detail_view(request, pk):
    task = get_object_or_404(AnalysisTask, pk=pk)
    return render(request, "analysis/detail.html", {"task": task})


@login_required
def run_analysis_view(request, evidence_pk):
    evidence = get_object_or_404(Evidence, pk=evidence_pk)
    if request.method == "POST":
        job = run_full_analysis.delay(evidence.id, request.user.id)
        return JsonResponse({"task_id": job.id, "status": "queued"})
    return JsonResponse({"error": "POST required"}, status=405)


@login_required
def task_status_view(request, pk):
    task = get_object_or_404(AnalysisTask, pk=pk)
    return JsonResponse({
        "status": task.status,
        "is_suspicious": task.is_suspicious,
        "threat_score": task.threat_score,
        "summary": task.result_summary,
        "yara_matches": task.yara_matches,
        "completed_at": str(task.completed_at) if task.completed_at else None,
    })


@login_required
def timeline_view(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    events = TimelineEvent.objects.filter(case=case).order_by("event_time")
    return render(request, "analysis/timeline.html", {"case": case, "events": events})
