from rest_framework import serializers
from .models import SubscriptionPlan, Subscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = "__all__" 
        read_only_fields = ["is_active"]

    def get_is_active(self, obj):
        return obj.is_active
