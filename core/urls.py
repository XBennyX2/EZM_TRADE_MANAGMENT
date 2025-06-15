from django.contrib import admin
from django.urls import path, include
from users.views import login_view

urlpatterns = [
    path('', login_view, name='login'),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
]
