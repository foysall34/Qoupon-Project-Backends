from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import FCMDevice, Notification
from .utils import FirebaseNotification

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device(request):
    """Register a device for FCM notifications"""
    registration_id = request.data.get('registration_id')
    device_type = request.data.get('type')

    if not registration_id or not device_type:
        return Response(
            {'error': 'registration_id and type are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if device_type not in ['android', 'ios', 'web']:
        return Response(
            {'error': 'Invalid device type'},
            status=status.HTTP_400_BAD_REQUEST
        )

    device, created = FCMDevice.objects.get_or_create(
        user=request.user,
        registration_id=registration_id,
        defaults={'type': device_type}
    )

    if not created:
        device.active = True
        device.type = device_type
        device.save()

    return Response({
        'message': 'Device registered successfully',
        'created': created
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unregister_device(request):
    """Unregister a device from FCM notifications"""
    registration_id = request.data.get('registration_id')

    if not registration_id:
        return Response(
            {'error': 'registration_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        device = FCMDevice.objects.get(
            user=request.user,
            registration_id=registration_id
        )
        device.active = False
        device.save()
        return Response({'message': 'Device unregistered successfully'})
    except FCMDevice.DoesNotExist:
        return Response(
            {'error': 'Device not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Get user's notifications"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]  # Get last 50 notifications

    return Response([{
        'id': notif.id,
        'title': notif.title,
        'body': notif.body,
        'type': notif.type,
        'data': notif.data,
        'read': notif.read,
        'created_at': notif.created_at
    } for notif in notifications])

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        user=request.user,
        read=False
    ).update(read=True)
    
    return Response({'message': 'All notifications marked as read'})
