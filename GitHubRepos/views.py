import requests
from django.http import JsonResponse
from urllib.parse import urlparse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .registerForm import RegisterForm

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Hash password
            user.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")  # Change 'login' to your login page URL name
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home') 
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = AuthenticationForm()


# Use this function to fetch GitHub repository contents
# Created by Brad 3-6-25

def fetch_github_repo(request):
    """Fetch list of files in the given GitHub repository"""
    github_url = request.GET.get("repo_url", "").strip()

    if not github_url:
        return JsonResponse({"error": "No repository URL provided"}, status=400)

    try:
        parsed_url = urlparse(github_url)
        path_parts = parsed_url.path.strip("/").split("/")
        
        if len(path_parts) < 2:
            return JsonResponse({"error": "Invalid GitHub repository URL"}, status=400)

        owner, repo = path_parts[:2]

        # GitHub API URL to get repository contents
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"

        response = requests.get(api_url)
        if response.status_code != 200:
            return JsonResponse({"error": "Failed to fetch repository contents"}, status=response.status_code)

        return JsonResponse(response.json(), safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def fetch_file_contents(request):
    """Fetch the contents of a specific file from a GitHub repository"""
    file_url = request.GET.get("file_url", "")

    if not file_url:
        return JsonResponse({"error": "No file URL provided"}, status=400)

    try:
        response = requests.get(file_url)
        if response.status_code != 200:
            return JsonResponse({"error": "Failed to fetch file contents"}, status=response.status_code)

        return JsonResponse({"content": response.text})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    return render(request, "login.html", {"form": form})