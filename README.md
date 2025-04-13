"CodeSniff" is a Django-based web application that analyzes GitHub repositories for code coverage and code smells. It integrates tools like GitPython, coverage.py, pytest, pylint, and more.

Features:
- Analyze GitHub repositories
- Display code coverage reports
- Identify code smells using pylint
- Visualize analysis with graphs


## Installation

1. Clone the repository

```bash
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


## Configuration
settings.py handles environment configuration.
add your api secret key in settings.py
  SECRET_KEY=your-secret-key



## Running the Server
python manage.py runserver
Visit: http://127.0.0.1:8000


Repository Used for Coverage and Code smell analysis: https://github.com/pypa/packaging 
