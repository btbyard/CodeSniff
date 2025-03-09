import requests
from django.http import JsonResponse
from urllib.parse import urlparse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .registerForm import RegisterForm

# Home View
def home(request):
    context = {
        'repo_name': request.GET.get("repo_name", "NONE")  # Default to "NONE" if no repo is loaded
    }
    return render(request, 'home.html', context)


# Register View
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Hash password
            user.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")  # Redirect to login page
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})

# Login View
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
    
    return render(request, "login.html", {"form": form})


# Fetch GitHub Repository Contents
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


# Fetch File Contents from GitHub
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


# 📌 View Coverage Page
def view_coverage(request, repo_name):
    """Display test coverage report for the selected repository"""
    if "/" in repo_name:  
        repo_name = repo_name.split("/")[-1]  # Only keep the repo name, discard the owner
    
    if repo_name == "NONE":
        return redirect('home')  # Redirect to home if no repo selected
    return render(request, 'coverage.html', {'repo_name': repo_name})

# 📌 View Smells Page
def view_smells(request, repo_name):
    """Display code smells report for the selected repository"""
    if repo_name == "NONE":
        return redirect('home')  # Redirect to home if no repo selected
    return render(request, 'smells.html', {'repo_name': repo_name})


# 📌 All Reports Page
def all_reports(request, repo_name):
    """Display all reports related to the repository"""
    if repo_name == "NONE":
        return redirect('home')  # Redirect to home if no repo selected
    return render(request, 'reports.html', {'repo_name': repo_name})
