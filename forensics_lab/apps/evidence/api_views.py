from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Evidence
from .serializers import EvidenceSerializer


class EvidenceViewSet(viewsets.ModelViewSet):
    serializer_class = EvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Evidence.objects.filter(
            case__in=self.request.user.assigned_cases.all()
        ) | Evidence.objects.filter(
            case__created_by=self.request.user
        )

    def perform_create(self, serializer):
        evidence = serializer.save(uploaded_by=self.request.user)
        evidence.compute_hashes()
        evidence.save()
