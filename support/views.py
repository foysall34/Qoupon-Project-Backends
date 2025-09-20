from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FAQ, ReportIssue, IssueType
from .serializers import FAQSerializer, ReportIssueSerializer
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser

# Create your views here.

class FAQListView(APIView):
    def get(self, request, format=None):
        faqs = FAQ.objects.all()
        serializer = FAQSerializer(faqs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ReportIssueCreateAPI(APIView):
    """
    POST: create an issue (guest or authed)
    GET:  list current user's issues (if authed), else empty list
    """
    permission_classes = [permissions.AllowAny]
    # parser_classes = [MultiPartParser, FormParser]

    def get(self, request, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response([], status=status.HTTP_200_OK)

        issues = ReportIssue.objects.filter(reporter=user).order_by("-created_at")
        serializer = ReportIssueSerializer(issues, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = ReportIssueSerializer(data=request.data)
        if serializer.is_valid():
            reporter = request.user if request.user.is_authenticated else None
            issue = serializer.save(reporter=reporter)
            return Response(
                ReportIssueSerializer(issue).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)