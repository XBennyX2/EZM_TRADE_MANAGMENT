import os
from django.core.mail import send_mail
from django.conf import settings

# Set up Django settings if not already configured
if not settings.configured:
    settings.configure(
        EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',  # Use console backend by default
        EMAIL_HOST=os.getenv("EMAIL_HOST", ''),
        EMAIL_PORT=int(os.getenv("EMAIL_PORT", 587)),
        EMAIL_HOST_USER=os.getenv("EMAIL_HOST_USER", ''),
        EMAIL_HOST_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD", ''),
        EMAIL_USE_TLS=os.getenv("EMAIL_USE_TLS", 'True') == 'True',
        EMAIL_USE_SSL=False,
        DEFAULT_FROM_EMAIL=os.getenv("DEFAULT_FROM_EMAIL", 'EZM Trade Management <noreply@ezmtrade.com>'),
        SERVER_EMAIL=os.getenv("DEFAULT_FROM_EMAIL", 'EZM Trade Management <noreply@ezmtrade.com>'),
        COMPANY_NAME=os.getenv("COMPANY_NAME", 'EZM Trade Management'),
        COMPANY_EMAIL=os.getenv("COMPANY_EMAIL", 'noreply@ezmtrade.com'),
        SECRET_KEY='django-insecure-^yks9ofa5b)o(8w32xk2f$veo+c+o8sbukcdl-7ixv7z@su2c(',  # Replace with your actual secret key if needed
        INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.messages', 'django.contrib.staticfiles'],  # Minimal apps
        ROOT_URLCONF='core.urls',
        STATIC_URL='/static/',
    )

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