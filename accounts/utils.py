import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    """4-সংখ্যার একটি র‍্যান্ডম OTP তৈরি করে।"""
    return str(random.randint(100000, 999999))

def send_otp_via_email(email, otp):
    """
    প্রদত্ত ইমেইলে OTP পাঠায়।
    এই ফাংশনটি settings.py-তে কনফিগার করা SMTP সার্ভার ব্যবহার করবে।
    """
    subject = 'Your Account Verification OTP'
    message = f'Your One-Time Password (OTP) is: {otp}'
    # settings.py থেকে EMAIL_HOST_USER স্বয়ংক্রিয়ভাবে ব্যবহৃত হবে
    email_from = settings.EMAIL_HOST_USER 
    recipient_list = [email]
    
    try:
        send_mail(subject, message, email_from, recipient_list)
    except Exception as e:
        # ইমেইল পাঠাতে ব্যর্থ হলে লগ বা প্রিন্ট করতে পারেন
        print(f"Failed to send email to {email}: {e}")