from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone

from .models import FCMDevice, Notification
from .utils import FirebaseNotification
from django.contrib.auth import get_user_model
from firebase_admin import messaging, exceptions as fb_exceptions

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])  # ✅ safer than AllowAny
def test_notification(request):
    """Send a test notification to all active devices of a user"""
    user_id = request.data.get('user_id')

    if not user_id:
        return Response(
            {'error': 'user_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    devices = FCMDevice.objects.filter(user=user, active=True)
    if not devices.exists():
        return Response(
            {'valid': False, 'message': 'No active devices found for this user'},
            status=status.HTTP_400_BAD_REQUEST
        )

    success = []
    failures = []

    for device in devices:
        message = messaging.Message(
            notification=messaging.Notification(
                title="Test Notification",
                body=f"Hello, this is a test notification!"
            ),
            data={'test': 'validation_check', 'timestamp': str(timezone.now())},
            token=device.registration_id
        )

        try:
            response = messaging.send(message)
            success.append({
                'device_id': device.id,
                'type': device.type,
                'firebase_message_id': response
            })
        except fb_exceptions.FirebaseError as e:
            error_code = getattr(e, 'code', None)
            failures.append({
                'device_id': device.id,
                'type': device.type,
                'error': str(e),
                'code': error_code
            })

            # deactivate invalid token
            if error_code == 'registration-token-not-registered':
                device.active = False
                device.save()
        except Exception as e:
            failures.append({
                'device_id': device.id,
                'type': device.type,
                'error': str(e)
            })

    return Response({
        'user_id': user.id,
        'success_count': len(success),
        'failure_count': len(failures),
        'success': success,
        'failures': failures,
        'checked_at': timezone.now().isoformat()
    })


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
        defaults={'type': device_type, 'active': True}
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
    """Get user's notifications (last 50)"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]

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
    """Mark a single notification as read"""
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
