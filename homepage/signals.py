from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from datetime import time

from ..vendors.models import BusinessHours, Shop

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_initial_shop_and_hours(sender, instance, created, **kwargs):
    """
    যখন একজন নতুন User তৈরি হয় (created=True) এবং তার user_type 'vendor' হয়,
    শুধুমাত্র তখনই তার জন্য একটি ডিফল্ট Shop এবং সপ্তাহের ৭ দিনের BusinessHours তৈরি হবে।
    """
    # প্রথমে চেক করা হচ্ছে যে ইউজারটি নতুন তৈরি হয়েছে কি না।
    if created:
        # ===> মূল পরিবর্তনটি এখানে <===
        # এখন আমরা চেক করছি যে নতুন ব্যবহারকারীর টাইপ 'vendor' কি না।
        # hasattr() ব্যবহার করা একটি ভালো অভ্যাস, এটি নিশ্চিত করে যে instance অবজেক্টে user_type নামে ফিল্ড আছে।
        if hasattr(instance, 'user_type') and instance.user_type == 'vendor':
            
            # ধাপ ১: ব্যবহারকারীর জন্য একটি ডিফল্ট শপ তৈরি
            new_shop, shop_created = Shop.objects.get_or_create(
                user=instance, 
                defaults={
                    'name': f"{instance.username}'s Shop",
                    'shop_title': f"Welcome to {instance.username}'s Shop"
                }
            )

            # ধাপ ২: ৭ দিনের জন্য ডিফল্ট BusinessHours অবজেক্ট তৈরি
            hours_to_create = []
            default_time = time(12, 12)  # 12:00 AM

            for day_index, _ in BusinessHours.DayOfWeek.choices:
                business_hour = BusinessHours(
                    user=instance,
                    shop=new_shop,
                    day=day_index,
                    open_time=default_time,
                    close_time=default_time,
                    is_closed=False
                )
                hours_to_create.append(business_hour)

            # ধাপ ৩: bulk_create ব্যবহার করে একসাথে সব অবজেক্ট ডেটাবেসে সেভ করা
            if hours_to_create:
                BusinessHours.objects.bulk_create(hours_to_create)