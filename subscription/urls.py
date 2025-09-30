from django.urls import path
from . import views

urlpatterns = [
    path("plans/", views.list_plans, name="list_plans"),
    path("subscribe/<int:plan_id>/", views.create_subscription, name="create_subscription"),
    path("cancel/<int:subscription_id>/", views.cancel_subscription, name="cancel_subscription"),
    path("webhook/mollie/", views.mollie_webhook, name="mollie_subscription_webhook"),
]
