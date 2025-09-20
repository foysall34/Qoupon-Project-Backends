from rest_framework import serializers
from . models import FAQ, ReportIssue, IssueType


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer']


class ReportIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportIssue
        fields = ["id", "reporter", "issue_type", "description", "screenshot", "created_at", "updated_at"]
        read_only_fields = ["reporter", "created_at", "updated_at"]

    def validate_issue_type(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This issue type is not available.")
        return value