from django.urls import path
from GitHubRepos import views
from .views import register

urlpatterns = [
    path('', views.home, name='home'),  # Home page view
    path('register/', views.register, name='register'),  # Register page view
    path('login/', views.login_view, name='login'),  # Login page view
]