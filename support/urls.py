from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


urlpatterns = [
        path('faqs/', views.FAQListView.as_view(), name='faq-list'),
        path('report-issue/', views.ReportIssueCreateAPI.as_view(), name='report-issue'),
]
