# users/utils.py
import random
from django.core.mail import send_mail

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(user):
    otp = generate_otp()
    user.otp_code = otp
    user.save()
    send_mail(
        'Your OTP for EZM BuildSync',
        f'Hello {user.username}, your OTP code is: {otp}',
        'no-reply@ezm-buildsync.com',
        [user.email],
        fail_silently=False,
    )
