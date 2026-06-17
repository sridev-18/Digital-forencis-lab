from rest_framework import serializers
from .models import Evidence, ChainOfCustody


class ChainOfCustodySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ChainOfCustody
        fields = "__all__"

    def get_performed_by_name(self, obj):
        return obj.performed_by.full_name if obj.performed_by else "System"


class EvidenceSerializer(serializers.ModelSerializer):
    file_size_human = serializers.ReadOnlyField()
    custody_chain = ChainOfCustodySerializer(many=True, read_only=True)

    class Meta:
        model = Evidence
        fields = "__all__"
        read_only_fields = ["md5_hash", "sha256_hash", "ssdeep_hash",
                            "uploaded_by", "uploaded_at", "file_type"]
