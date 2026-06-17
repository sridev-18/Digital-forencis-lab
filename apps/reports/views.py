from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from apps.cases.models import Case
from apps.accounts.models import AuditLog


@login_required
def report_view(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    return render(request, "reports/report.html", {
        "case": case,
        "evidence_list": case.evidence_set.all(),
        "analysis_tasks": case.analysis_tasks.filter(status="completed"),
        "custody_logs": [e.custody_chain.all() for e in case.evidence_set.all()],
        "timeline_events": case.timeline_events.order_by("event_time"),
        "audit_logs": AuditLog.objects.filter(resource_id=str(case.id), resource_type="Case"),
    })


@login_required
def export_pdf_view(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    try:
        from weasyprint import HTML
        html_string = render_to_string("reports/pdf_template.html", {
            "case": case,
            "evidence_list": case.evidence_set.all(),
            "analysis_tasks": case.analysis_tasks.filter(status="completed"),
            "timeline_events": case.timeline_events.order_by("event_time"),
        })
        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{case.case_number}_report.pdf"'
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.EXPORT,
            resource_type="Case",
            resource_id=str(case.id),
            description=f"Exported PDF report for case {case.case_number}",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return response
    except ImportError:
        return HttpResponse("WeasyPrint not installed. Run: pip install weasyprint", status=500)


