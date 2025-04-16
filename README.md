"CodeSniff" is a Django-based web application that analyzes GitHub repositories for code coverage and code smells. It integrates tools like GitPython, coverage.py, pytest, pylint, and more.

Features:
- Analyze GitHub repositories
- Display code coverage reports
- Identify code smells using pylint
- Visualize analysis with graphs


## Installation

1. Clone the repository

git clone https://github.com/yourusername/codesniff.git
cd codesniff


2. Install dependencies
Django 5.1.7
django-tailwind 3.8.0
gitdb 4.0.12
GitPython 3.1.44
pipreqs 0.4.13
Pytest
Coverage.py
Pylint
pipreqs


## Database Setup
sqliteUses SQLite (default with Django)
Run the following to set up the database:
  python manage.py makemigrations  
  python manage.py migrate


## Configuration
settings.py handles environment configuration.


## Running the Server
Run this command: "python manage.py runserver"
Visit: http://127.0.0.1:8000


Repository Used for Coverage and Code smell analysis: 
https://github.com/sharabhshukla/pytest-tutorial
https://github.com/balram-vis/Python-Calculator---Unit-Testing-Code-Coverage

