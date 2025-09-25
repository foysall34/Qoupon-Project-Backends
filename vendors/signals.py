from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Create_Deal, Business_profile
from django.contrib.auth import get_user_model
from notifications.utils import FirebaseNotification

User = get_user_model()

@receiver(post_save, sender=Create_Deal)
def notify_users_new_deal(sender, instance, created, **kwargs):
    """
    Send notifications to all non-vendor users when a new deal is created
    """
    if created:  # Only for newly created deals
        try:
            # Get all users who are not vendors (don't have a business profile)
            non_vendor_users = User.objects.exclude(
                id__in=Business_profile.objects.values_list('owner_id', flat=True)
            )

            # Prepare deal details for the notification
            deal_data = {
                'deal_id': instance.id,
                'title': instance.title,
                'discount_value': str(instance.discount_value),
                'type': 'new_deal'
            }

            # Format discount text based on value
            if instance.discount_value <= 100:
                discount_text = f"{instance.discount_value}% off"
            else:
                discount_text = f"€{instance.discount_value} off"

            # Send notification to each non-vendor user
            for user in non_vendor_users:
                FirebaseNotification.send_to_user(
                    user=user,
                    title="New Deal Available! 🎉",
                    body=f"{instance.title} - {discount_text}",
                    data=deal_data,
                    notification_type='promotion'
                )
        except Exception as e:
            # Log the error but don't prevent deal creation
            print(f"Error sending new deal notifications: {e}")