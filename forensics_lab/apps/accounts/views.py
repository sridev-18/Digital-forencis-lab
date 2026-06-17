from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import User, AuditLog


def login_view(request):
    if request.user.is_authenticated:
        return redirect("cases:dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)

        if user and user.is_active:
            login(request, user)
            AuditLog.objects.create(
                user=user,
                action=AuditLog.Action.LOGIN,
                resource_type="Auth",
                description=f"User {user.email} logged in",
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            return redirect(request.GET.get("next", "cases:dashboard"))
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "accounts/login.html")


@require_POST
@login_required
def logout_view(request):
    AuditLog.objects.create(
        user=request.user,
        action=AuditLog.Action.LOGOUT,
        resource_type="Auth",
        description=f"User {request.user.email} logged out",
        ip_address=get_client_ip(request),
    )
    logout(request)
    return redirect("accounts:login")


@login_required
def profile_view(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.phone = request.POST.get("phone", user.phone)
        user.department = request.POST.get("department", user.department)
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("accounts:profile")

    recent_logs = AuditLog.objects.filter(user=request.user).order_by("-timestamp")[:20]
    return render(request, "accounts/profile.html", {"recent_logs": recent_logs})


@login_required
def user_list_view(request):
    if not request.user.is_admin():
        messages.error(request, "Admin access required.")
        return redirect("cases:dashboard")

    users = User.objects.all().order_by("role", "email")
    return render(request, "accounts/user_list.html", {"users": users})


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
