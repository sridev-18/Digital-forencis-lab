from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Case
from .serializers import CaseSerializer


class CaseViewSet(viewsets.ModelViewSet):
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Case.objects.all()
        return Case.objects.filter(
            Q(created_by=user) | Q(assigned_to=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        return Response({
            "total": qs.count(),
            "open": qs.filter(status=Case.Status.OPEN).count(),
            "active": qs.filter(status=Case.Status.ACTIVE).count(),
            "closed": qs.filter(status=Case.Status.CLOSED).count(),
            "critical": qs.filter(priority=Case.Priority.CRITICAL).count(),
        })
