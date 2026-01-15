# UV Installation and Project Initialization Guide
Follow these steps to install [UV](https://github.com/astral-sh/uv) and initialize it in your Python project.

## 1. Install UV Globally
Open your terminal and run:
```bash
pip install uv
```
## 2. Navigate to Your Project
In your terminal, use cd to enter your project folder, for example:
```bash
cd path/to/your/project
```
## 3. Initialize UV in the Project
Inside your project folder, run:
```bash
uv init
```
This creates files like pyproject.toml and uv.lock to manage your Python dependencies.
## 4. Add Dependencies (If Needed)
If you want to install a package, for example requests, run:
```bash
uv pip install requests
```
This updates your lockfile and installs the package.
## 5. Check Everything is Set
Make sure you see pyproject.toml and uv.lock in your folder, and check installed packages: