from django.urls import path
from GitHubRepos import views
from .views import get_smell_data, register, view_smells
from .views import fetch_github_repo, fetch_file_contents  # Import from the same app

urlpatterns = [
    path('', views.home, name='home'),  # Home page view
    path('register/', views.register, name='register'),  # Register page view
    path('login/', views.login_view, name='login'),  # Login page view
    path('fetch-github/', fetch_github_repo, name='fetch_github'),  # Fetch GitHub Repo API
    path('fetch-file/', fetch_file_contents, name='fetch_file'),  # New endpoint for file contents
    path('coverage/<str:repo_name>/', views.view_coverage, name='view_coverage'), # View coverage page
    path('smells/<str:repo_name>/', views.view_smells, name='view_smells'), # View smells page
    path('analyze-coverage/', views.analyze_coverage, name='analyze_coverage'), # API endpoint to analyze the code coverage of the repo
    path('api/coverage/<str:repo_name>/', views.get_coverage_data, name='get_coverage_data'),
    path("smells/<str:repo_name>/", view_smells, name="view_smells"),
    path("api/smells/<str:repo_name>/", views.get_smell_data, name="get_smell_data"),
]