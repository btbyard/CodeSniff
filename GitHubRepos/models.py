from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class GitHubRepos(models.Model):  # Added models.Model here:
    githubURL = models.URLField() # URL Field for the github URL ; not unique so many users can track it. 
    githubID = models.AutoField(primary_key=True) # auto incrementing id for primary key
    repositoryName = models.CharField(max_length=255) # Repo name field
    users = models.ManyToManyField(User) # which users it is connected to

class CodeSmellResult(models.Model):
    gitHubRepo = models.OneToOneField(GitHubRepos, on_delete=models.CASCADE)
    codeSmellFile = models.FileField(upload_to='code_smell_results/')
    
class CodeCoverageResult(models.Model):
    gitHubRepo = models.OneToOneField(GitHubRepos, on_delete=models.CASCADE) # Relation for mapping repo to the smell results
    codeCoverageFile = models.FileField(upload_to='coverage_results/') # File upload locations for the results (Assuming XML Format possibly). Mby use XML tree to generate and read the results
