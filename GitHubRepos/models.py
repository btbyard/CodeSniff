from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class GitHubRepos:
    githubURL = models.URLField() # URL Field for the github URL ; not unique so many users can track it. 
    githubID = models.AutoField(primary_key=True) # auto incrementing id for primary key
    repositoryName = models.CharField(max_length=255) # Repo name field
    user = models.ForeignKey(User, on_delete=models.CASCADE) # which user it is connected to