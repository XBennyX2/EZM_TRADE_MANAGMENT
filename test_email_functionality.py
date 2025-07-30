import os
from django.core.mail import send_mail
from django.conf import settings

# Set up Django settings if not already configured

def test_send_email(recipient_email):
    try:
        send_mail(
            'Test Email',
            'This is a test email sent from Django.',
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        print(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
        return False

if __name__ == "__main__":
    recipient_email = "abeneman123@gmail.com"
    test_send_email(recipient_email)