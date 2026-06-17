from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.models import AuditLog


@login_required
def audit_log_view(request):
    if not request.user.is_admin():
        logs = AuditLog.objects.filter(user=request.user).order_by("-timestamp")[:200]
    else:
        logs = AuditLog.objects.all().order_by("-timestamp")[:200]
    return render(request, "audit/log_list.html", {"logs": logs})
