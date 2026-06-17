from rest_framework import serializers
from .models import Case, CaseNote


class CaseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    evidence_count = serializers.ReadOnlyField()

    class Meta:
        model = Case
        fields = "__all__"
        read_only_fields = ["case_number", "created_by", "created_at", "updated_at"]

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else "Unknown"
