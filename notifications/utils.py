import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from django.utils import timezone
from .models import FCMDevice, Notification

# Initialize Firebase Admin with your credentials
cred = credentials.Certificate(os.path.join(settings.BASE_DIR, 'secrets/quopon-8b833-firebase-adminsdk-fbsvc-d9570ee0f3.json'))
firebase_admin.initialize_app(cred)

class FirebaseNotification:
    @staticmethod
    def send_to_user(user, title, body, data=None, notification_type='system'):
        """
        Send notification to all active devices of a user
        """
        if data is None:
            data = {}

        # Create notification record
        notification = Notification.objects.create(
            user=user,
            title=title,
            body=body,
            type=notification_type,
            data=data
        )

        # Get all active devices for the user
        devices = FCMDevice.objects.filter(user=user, active=True)
        
        if not devices.exists():
            notification.error = "No active devices found"
            notification.save()
            return False

        # Prepare the message
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data,
            tokens=[device.registration_id for device in devices]
        )

        try:
            # Send the message
            response = messaging.send_multicast(message)
            
            # Update notification status
            notification.sent = True
            notification.sent_at = timezone.now()
            
            if response.failure_count > 0:
                # Some tokens failed
                failures = []
                for idx, result in enumerate(response.responses):
                    if not result.success:
                        error_info = f"Failed to send to {devices[idx].type}: {result.exception}"
                        failures.append(error_info)
                        
                        # Deactivate failed tokens
                        if 'registration-token-not-registered' in str(result.exception):
                            devices[idx].active = False
                            devices[idx].save()
                
                notification.error = "; ".join(failures)
            
            notification.save()
            return response.success_count > 0

        except Exception as e:
            notification.error = str(e)
            notification.save()
            return False

    @staticmethod
    def send_to_multiple_users(users, title, body, data=None, notification_type='system'):
        """
        Send the same notification to multiple users
        """
        success_count = 0
        for user in users:
            if FirebaseNotification.send_to_user(user, title, body, data, notification_type):
                success_count += 1
        return success_count

    @staticmethod
    def send_order_status_update(order, status_message):
        """
        Send order status update notification
        """
        title = "Order Status Update"
        body = f"Your order #{order.order_id} {status_message}"
        data = {
            'order_id': str(order.order_id),
            'status': order.status,
            'type': 'order_update'
        }
        return FirebaseNotification.send_to_user(
            user=order.user,
            title=title,
            body=body,
            data=data,
            notification_type='order_status'
        )

    @staticmethod
    def send_payment_update(order, payment_status):
        """
        Send payment status update notification
        """
        title = "Payment Update"
        body = f"Payment for order #{order.order_id} is {payment_status}"
        data = {
            'order_id': str(order.order_id),
            'payment_status': payment_status,
            'type': 'payment_update'
        }
        return FirebaseNotification.send_to_user(
            user=order.user,
            title=title,
            body=body,
            data=data,
            notification_type='payment'
        )