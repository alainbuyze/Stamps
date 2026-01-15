# To set up a project to use a GitHub repository and enable issue-based development, follow these steps:

## 1. Create a New GitHub Repository
Go to github.com and sign in.
Click the “+” in the top right, then “New repository”.
Fill in the repository name and details, then click “Create repository”.
## 2. Clone the Repository to Your Local Machine
Open your terminal and run:
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```
## 3. Enable GitHub Issues
Issues are enabled by default on new GitHub repositories.
Check the “Issues” tab in your repository. If you don’t see it, go to Settings > Features and ensure Issues is checked.
## 4. Create and Use Issues for Development
In the GitHub repo, click the “Issues” tab.
Select “New issue” to create tickets for bugs, features, or tasks.
Each issue can be assigned to team members, labeled, and tracked.
## 5. Structure Development Around Issues
When working on an issue:
Create a new branch named after the issue (e.g., git checkout -b issue-12-title).
Link pull requests to issues by mentioning “Closes #issue-number” in your pull request description.
Use GitHub Projects or Milestones for more advanced tracking.
## 6. Close Issues via Pull Requests
When your code is ready, open a Pull Request and mention the related issue (e.g., Fixes #23).
When your Pull Request is merged, GitHub will automatically close the referenced issue.
## 7. Your project is now set up for issue-based development using GitHub! Team members can discuss, track, and resolve project work through the Issues system.