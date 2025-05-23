import importlib
import shutil
import venv
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.core.files.storage import default_storage
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .registerForm import RegisterForm
from urllib.parse import urlparse
from django.http import JsonResponse
from django.core.files.base import ContentFile
import requests
import subprocess
import json
import tempfile
import git
import os
from .models import *
import xml.etree.ElementTree as ET
import pipreqs
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

# Home View and require login
@login_required(login_url='/login')
def home(request):
    context = {
        'repo_name': request.GET.get("repo_name", "NONE")  # Default to "NONE" if no repo is loaded
    }
    return render(request, 'home.html', context)

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])  # Ensure the password field name matches
            user.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")  # Ensure 'login' is the name of your login page URL
        
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
                messages.error(request, 'Invalid username or password')
        else:
            print(form.errors)  
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})

@csrf_exempt
def logout_user(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"message": "Logged out successfully"})
    return JsonResponse({"error": "Invalid request"}, status=405)
    

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

def get_coverage_data(request, repo_name):
    try:
        # Get the CodeCoverageResult object related to the repo_name
        coverage_result = CodeCoverageResult.objects.get(gitHubRepo__repositoryName=repo_name)
        coverage_file = coverage_result.codeCoverageFile
        gitHubRepo = coverage_result.gitHubRepo  # Get the related GitHub repo object

        # Parse the XML coverage file
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        coverage_data = []

        # Process each file entry in the coverage XML
        for file_element in root.findall("file"):
            file_name = file_element.get("name")
            coverage = float(file_element.get("coverage").strip('%'))
            lines_covered = int(file_element.get("lines_covered"))
            lines_missed = int(file_element.get("lines_missed"))
            total_lines = int(file_element.get("total_lines"))
            full_path = file_element.get("full_path")  # Get the full path directly from the XML

            # Construct the API URL to fetch the file from the GitHub repository
            owner = gitHubRepo.githubURL.split("/")[3]  # Extract owner from the GitHub URL
            repo = gitHubRepo.repositoryName  # The repository name is already stored
            download_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{full_path}"

            # Collect and format coverage data
            coverage_data.append({
                "file_name": file_name,
                "coverage_percent": coverage,
                "lines_covered": lines_covered,
                "lines_missed": lines_missed,
                "total_lines": total_lines,
                "covered_lines": [line.text for line in file_element.findall(".//covered_lines/line_covered")] or [],
                "missed_lines": [line.text for line in file_element.findall(".//missed_lines/line_missed")] or [],
                "download_url": download_url
            })

        return JsonResponse(coverage_data, safe=False)

    except CodeCoverageResult.DoesNotExist:
        return JsonResponse({"error": "Coverage data not found for this repository."}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

    
def parse_coverage_xml(file_path, url):
    """Parse the XML coverage file and return the relevant coverage data."""
    coverage_data = []
    
    tree = ET.parse(file_path)
    root = tree.getroot()

    for file in root.findall('file'):
        file_name = file.get('name')
        covered_lines = int(file.get('coveredlines', 0))
        total_lines = int(file.get('lines', 0))

        covered_percent = (covered_lines / total_lines) * 100 if total_lines > 0 else 0

        coverage_data.append({
            "file_name": file_name,
            "covered_percent": covered_percent,
            "file_url": url
        })

    return coverage_data

# 📌 View Smells Page
def view_smells(request, repo_name):
    """Render the smell report dashboard view"""
    if "/" in repo_name:  
        repo_name = repo_name.split("/")[-1]
    
    if repo_name == "NONE":
        return redirect('home')

    return render(request, "smells.html", {"repo_name": repo_name})

# 📌 All Reports Page
def all_report(request):
    # Fetch all repositories from the database
    all_repos = GitHubRepos.objects.all()

    # Get the list of selected repositories from the request (if any)
    selected_repos = request.GET.getlist('repos') or [repo.repositoryName for repo in all_repos]

    all_reports = []

    for repo_name in selected_repos:
        # Coverage Data
        try:
            coverage_response = get_coverage_data(request, repo_name)
            coverage_data = json.loads(coverage_response.content)  # Ensure JSON parsing
            average_coverage = (
                sum(file.get("coverage_percent", 0) for file in coverage_data) / len(coverage_data)
                if coverage_data else 0
            )
        except Exception as e:
            print(f"Coverage error for {repo_name}: {e}")
            average_coverage = 0

        # Smell Data
        try:
            repo = GitHubRepos.objects.get(repositoryName=repo_name)
            smell_result = CodeSmellResult.objects.get(gitHubRepo=repo)
            if smell_result.codeSmellFile and smell_result.codeSmellFile.path:
                with open(smell_result.codeSmellFile.path, 'r') as file:
                    smell_data = json.load(file)
                smell_count = len(smell_data)
            else:
                smell_count = 0
        except Exception as e:
            print(f"Smell error for {repo_name}: {e}")
            smell_count = 0

        all_reports.append({
            "repo": repo_name,
            "coverage": average_coverage,
            "smells": smell_count,
        })

    context = {
        "chart_data": json.dumps(all_reports),
        "all_repos": all_repos,  # Pass all repositories for checkboxes
        "selected_repos": selected_repos,  # Keep track of selected repos
        
    }

    return render(request, "reports_new.html", context)
    



@csrf_exempt
def analyze_coverage(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            repo_url = data.get("repo_url")

            if not repo_url:
                return JsonResponse({"error": "Repository URL is required."}, status=400)
            
            repo_url = check_git_url(repo_url)

            temp_dir = tempfile.mkdtemp()
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            repo_path = os.path.join(temp_dir, repo_name)

            user = request.user.id if request.user.is_authenticated else None
            
            repo = create_github_repo(data.get("repo_url"), repo_name, user)

            git.Repo.clone_from(repo_url, repo_path)  # Clone repo

            venv_path = os.path.join(repo_path, "venv")
            print("VENV PATH:", venv_path)
            create_virtualenv(venv_path)

            install_from_imports(repo_path, venv_path)

            python_exec = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", "python")
            subprocess.run([python_exec, "-m", "coverage", "run", "-m", '--omit="*/test/*,*/tests/*",test*.py,*test.py', "pytest"], cwd=repo_path, check=True)
            subprocess.run([python_exec, "-m", "coverage", "xml"], cwd=repo_path, check=True)

            coverage_file = os.path.join(repo_path, "coverage.xml")
            simplified_file = os.path.join(repo_path, "simplified_coverage.xml")

            simplify_coverage_report(coverage_file, simplified_file, repo_path)

            with open(simplified_file, "r") as f:
                coverage_xml_content = f.read()

            coverage_result = CodeCoverageResult.objects.filter(gitHubRepo=repo).first()

            # If there is an existing result, delete the old file
            if coverage_result:
                old_file_path = coverage_result.codeCoverageFile.path
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            # Update or create the new CodeCoverageResult
            coverage_result, created = CodeCoverageResult.objects.update_or_create(
                gitHubRepo=repo,
                defaults={"codeCoverageFile": ContentFile(coverage_xml_content, name=f"{repo_name}_coverage.xml")}
            )
            coverage_result.save()
           
            try: 
                pylint_cmd = [python_exec, "-m", "pylint", "./*/*.py", "--output-format=json"]
                pylint_proc = subprocess.run(pylint_cmd, capture_output=True, text=True,  cwd=repo_path)
                
                pylint_output = pylint_proc.stdout
                
                smell_result = CodeSmellResult.objects.filter(gitHubRepo=repo).first()

                if smell_result:
                 old_file_path = smell_result.codeSmellFile.path
                 if os.path.exists(old_file_path):
                   os.remove(old_file_path)
                   
                smell_result, created = CodeSmellResult.objects.update_or_create(gitHubRepo=repo, defaults={"codeSmellFile": ContentFile(pylint_output, name=f"{repo_name}_smells.json")}); smell_result.save() 
            except subprocess.CalledProcessError as e: 
                print("Pylint failed to run"); print("stdout:", e.stdout[:300]); 
                print("stderr:", e.stderr[:300]); 
                return JsonResponse({"error": "Pylint analysis failed", "stderr": e.stderr}, status=500) 
            
            except Exception as e: 
                import traceback; traceback.print_exc(); 
                return JsonResponse({"error": f"Failed to save smell report: {str(e)}"}, status=500)
        
  
            try:
                pylint_results = json.loads(pylint_output)
            except json.JSONDecodeError:
                pylint_results = []

            return JsonResponse({
                "message": "Coverage and code smell analysis completed",
                "smells": pylint_results
            })

        except git.exc.GitCommandError as e:
            return JsonResponse({"error": f"Git error: {str(e)}"}, status=500)
        except subprocess.CalledProcessError as e:
            return JsonResponse({"error": f"Coverage analysis failed: {str(e)}"}, status=500)
        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)

def get_smell_data(request, repo_name):
    try:
        smell_result = CodeSmellResult.objects.get(gitHubRepo__repositoryName=repo_name)
        print("🔍 Smell file path:", smell_result.codeSmellFile.path)

        with open(smell_result.codeSmellFile.path, "r") as f:
         data = json.load(f)
         print("📦 Pylint smell data:", json.dumps(data[:3], indent=2)) 
        print("inside get smell data")
        report_file = smell_result.codeSmellFile

        with open(report_file.path, "r") as f:
            pylint_data = json.load(f)

        return JsonResponse(pylint_data, safe=False)

    except CodeSmellResult.DoesNotExist:
        return JsonResponse({"error": "Smell data not found for this repository."}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

def create_github_repo(url, repoName, user):
    try:
        repo = GitHubRepos.objects.get(githubURL=url)
    except Exception:
        repo = None
    if repo is None:
        repo, created = GitHubRepos.objects.get_or_create(githubURL=url, repositoryName=repoName)
        if user and user not in repo.users.all():
            repo.users.add(user)
    repo.save()
    return repo

def create_virtualenv(venv_path):
    venv.create(venv_path, with_pip=True)

def install_from_imports(repo_path, venv_path):
    python_exec = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", "python")
    pip_exec = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", "pip")

    subprocess.run([python_exec, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    subprocess.run(["pipreqs", "--force", repo_path], check=True)
    with open(os.path.join(repo_path, "requirements.txt"), "r") as f:
        print(f.read())

    subprocess.run([pip_exec, "install", "-r", os.path.join(repo_path, "requirements.txt")], check=True)

    # Install coverage and pytest (if they're not already in the requirements file)
    subprocess.run([pip_exec, "install", "coverage", "pytest"], check=True)
    subprocess.run([pip_exec, "install", "pylint"], check=True)


def find_file_in_repo(repo_path, file_name):
    """Recursively search for the file in the cloned repo directory and return its relative path."""
    for root, dirs, files in os.walk(repo_path):
        if file_name in files:
            return os.path.relpath(os.path.join(root, file_name), repo_path)
    return None  # Return None if the file is not found

def simplify_coverage_report(input_file, output_file, repo_path):
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Create the root element for the simplified report
    simplified_root = ET.Element("coverage")
    line_rate = float(root.get("line-rate", "0")) * 100
    lines_covered = int(root.get("lines-covered", "0"))
    lines_missed = int(root.get("lines-missed", "0"))
    total_lines = lines_covered + lines_missed

    # Add attributes to the root element with total coverage data
    simplified_root.attrib.update({
        "total_coverage": f"{line_rate:.2f}%",
        "total_lines_covered": str(lines_covered),
        "total_lines_missed": str(lines_missed),
        "total_lines": str(total_lines)
    })

    # Iterate over each class (file) and extract coverage information
    for class_element in root.findall(".//class"):
        file_name = class_element.get("filename", "unknown")

        # Find the full path to the file by searching the cloned repo directory
        file_base_name = os.path.basename(file_name)
        full_file_path = find_file_in_repo(repo_path, file_base_name)

        file_line_rate = float(class_element.get("line-rate", "0")) * 100

        # Collect lines covered and missed by this file
        lines_covered_list = []
        lines_missed_list = []
        for line in class_element.findall("lines/line"):
            line_number = int(line.get("number"))
            hits = int(line.get("hits"))
            if hits > 0:
                lines_covered_list.append(line_number)
            else:
                lines_missed_list.append(line_number)

        # Create a file element under the root with the filename and its coverage
        file_element = ET.SubElement(simplified_root, "file", {
            "name": file_base_name,
            "coverage": f"{file_line_rate:.2f}%",
            "lines_covered": str(len(lines_covered_list)),
            "lines_missed": str(len(lines_missed_list)),
            "total_lines": str(len(class_element.findall("lines/line"))),
            "full_path": full_file_path  # Add the full path as an attribute
        })

        # Add covered lines under the <covered_lines> element
        covered_lines_element = ET.SubElement(file_element, "covered_lines")
        for line in lines_covered_list:
            ET.SubElement(covered_lines_element, "line_covered").text = str(line)

        # Add missed lines under the <missed_lines> element
        missed_lines_element = ET.SubElement(file_element, "missed_lines")
        for line in lines_missed_list:
            ET.SubElement(missed_lines_element, "line_missed").text = str(line)

    # Write the simplified XML to the output file
    simplified_tree = ET.ElementTree(simplified_root)
    ET.indent(simplified_tree, space="  ", level=0)
    simplified_tree.write(output_file, encoding="utf-8")

def check_git_url(url):
    if ".git" not in url:
        url += ".git"
    return url