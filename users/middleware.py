from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class FirstLoginPasswordChangeMiddleware:
    """
    Middleware to enforce password change for users on their first login.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # URLs that should be accessible even during first login
        allowed_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('first_login_password_change'),
            '/admin/',  # Allow admin access
        ]
        
        # Static and media URLs
        if (request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path.startswith('/admin/')):
            return self.get_response(request)
        
        # Check if user is authenticated and needs to change password
        if (request.user.is_authenticated and
            hasattr(request.user, 'is_first_login')):

            # Refresh user from database to get latest state
            request.user.refresh_from_db()

            if (request.user.is_first_login and
                request.path not in allowed_urls):

                # Don't redirect if already on password change page
                if request.path != reverse('first_login_password_change'):
                    messages.warning(
                        request,
                        'You must change your password before accessing other features.'
                    )
                    return redirect('first_login_password_change')
        
        response = self.get_response(request)
        return response
