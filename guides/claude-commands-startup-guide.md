# Claude Code Commands Startup Guide

A comprehensive guide to defining and organizing slash commands for your Claude Code projects.

---

## Table of Contents

1. [What Are Slash Commands?](#what-are-slash-commands)
2. [Directory Structure](#directory-structure)
3. [Command File Anatomy](#command-file-anatomy)
4. [Essential Starter Commands](#essential-starter-commands)
5. [Advanced Command Features](#advanced-command-features)
6. [Real-World Example: PIV Loop Workflow](#real-world-example-piv-loop-workflow)
7. [Organizing Commands with Namespaces](#organizing-commands-with-namespaces)
8. [Best Practices](#best-practices)
9. [Quick Setup Script](#quick-setup-script)

---

## What Are Slash Commands?

Slash commands are reusable prompts stored as Markdown files. When you type `/command-name` in Claude Code, Claude loads and executes the instructions from that file.

**Benefits:**
- Codify expertise and best practices
- Ensure consistency across your team
- Automate repetitive workflows
- Version control your AI workflows with git

---

## Directory Structure

### Project-Scoped Commands

Available only in the current project. Store in:

```
your-project/
└── .claude/
    └── commands/
        ├── commit.md
        ├── validate.md
        └── core_workflow/
            ├── plan.md
            └── execute.md
```

Access with: `/project:command-name` or `/project:folder:command-name`

### Personal Commands

Available across all projects. Store in:

```
~/.claude/
└── commands/
    ├── security-review.md
    └── optimize.md
```

Access with: `/user:command-name`

---

## Command File Anatomy

Every command is a Markdown file with optional YAML frontmatter:

```markdown
---
description: Brief description shown in autocomplete
allowed-tools: Bash(git:*), Read, Write, Grep
model: claude-sonnet-4-5-20250929
argument-hint: [optional-argument-description]
---

# Command Title

Instructions for Claude go here.

Use $ARGUMENTS to capture user input passed to the command.
```

### Frontmatter Options

| Field | Description |
|-------|-------------|
| `description` | Shows in `/help` and autocomplete |
| `allowed-tools` | Tools the command can use |
| `model` | Override the default model (e.g., `haiku` for speed) |
| `argument-hint` | Hint for expected arguments |
| `disable-model-invocation` | Prevent programmatic invocation |

---

## Essential Starter Commands

### 1. Initialize Project (`init-project.md`)

```markdown
---
description: Install dependencies and start development servers
allowed-tools: Bash, Read
---

# Initialize Project

1. Check for package managers and install dependencies:
   - If `package.json` exists: `npm install`
   - If `pyproject.toml` exists: `uv sync` or `pip install -e .`
   - If `requirements.txt` exists: `pip install -r requirements.txt`

2. Start development servers as needed

3. Verify the setup is working

Report any errors encountered during setup.
```

### 2. Commit (`commit.md`)

```markdown
---
description: Create a git commit with conventional message
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git diff:*)
model: haiku
---

## Context

- Current git status: !`git status`
- Staged changes: !`git diff --cached`
- Unstaged changes: !`git diff`
- Current branch: !`git branch --show-current`
- Recent commits for style reference: !`git log --oneline -5`

## Task

Based on the above changes, create a single git commit:

1. Stage relevant files if needed
2. Write a commit message following Conventional Commits:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation
   - `style:` formatting
   - `refactor:` code restructuring
   - `test:` adding tests
   - `chore:` maintenance

Keep the message concise but descriptive.
```

### 3. Validate (`validate.md`)

```markdown
---
description: Run full validation suite (tests, lint, type-check, build)
allowed-tools: Bash, Read
---

# Full Validation

Run the complete validation suite for this project:

## Steps

1. **Linting**: Run the linter and fix auto-fixable issues
2. **Type Checking**: Run type checker if applicable
3. **Tests**: Run the test suite with coverage
4. **Build**: Verify the project builds successfully

## Detection

Detect the project type and use appropriate commands:
- Node.js: `npm run lint`, `npm run test`, `npm run build`
- Python: `ruff check`, `mypy`, `pytest`, `python -m build`

## Output

Report:
- ✅ Passed checks
- ❌ Failed checks with details
- 📊 Test coverage summary

If any check fails, provide specific remediation steps.
```

### 4. Code Review (`code-review.md`)

```markdown
---
description: Technical code review on changed files
allowed-tools: Bash(git diff:*), Read, Grep
---

# Code Review

## Changed Files

!`git diff --name-only HEAD~1`

## Detailed Changes

!`git diff HEAD~1`

## Review Checklist

Review the above changes for:

1. **Code Quality**
   - Readability and maintainability
   - Consistent naming conventions
   - Appropriate comments

2. **Logic & Correctness**
   - Edge cases handled
   - Error handling
   - Race conditions

3. **Security**
   - Input validation
   - SQL injection risks
   - Exposed credentials

4. **Performance**
   - Unnecessary loops or allocations
   - Database query efficiency
   - Caching opportunities

5. **Tests**
   - Adequate test coverage
   - Test edge cases

Provide specific, actionable feedback organized by priority (critical, major, minor).
```

### 5. Plan Feature (`plan-feature.md`)

```markdown
---
description: Create comprehensive implementation plan for a feature
allowed-tools: Read, Grep, Glob, Bash(find:*)
---

# Plan Feature: $ARGUMENTS

## Analysis Phase

1. **Understand the Request**
   - What is the feature?
   - What problem does it solve?
   - Who are the users?

2. **Codebase Analysis**
   - Identify relevant existing code
   - Find similar patterns to follow
   - Note integration points

3. **Technical Design**
   - Data models needed
   - API endpoints
   - UI components
   - Database changes

## Implementation Plan

Create a step-by-step plan with:
- [ ] Step description
- Files to create/modify
- Dependencies on other steps
- Estimated complexity (S/M/L)

## Risks & Considerations

- Breaking changes
- Migration needs
- Performance implications
- Security considerations

Save the plan to `.claude/plans/$ARGUMENTS.md`
```

### 6. Fix Issue (`fix-issue.md`)

```markdown
---
description: Analyze and fix a GitHub issue by number
allowed-tools: Bash, Read, Write, Grep
argument-hint: [issue-number]
---

# Fix GitHub Issue #$ARGUMENTS

## Steps

1. **Fetch Issue Details**
   ```bash
   gh issue view $ARGUMENTS
   ```

2. **Understand the Problem**
   - What is the expected behavior?
   - What is the actual behavior?
   - Are there reproduction steps?

3. **Locate Relevant Code**
   - Search codebase for related files
   - Identify root cause

4. **Implement Fix**
   - Make minimal, focused changes
   - Follow existing code patterns
   - Add/update tests

5. **Validate**
   - Run tests
   - Verify the fix works
   - Check for regressions

6. **Document**
   - Add comments if needed
   - Update documentation
```

### 7. Create Branch (`branch.md`)

```markdown
---
description: Create a feature branch with proper naming
allowed-tools: Bash(git:*)
model: haiku
argument-hint: [branch-description]
---

# Create Branch

Create a properly named feature branch:

1. Ensure on main/master and pull latest:
   ```bash
   git checkout main && git pull
   ```

2. Create branch with conventional naming:
   - `feat/` for features
   - `fix/` for bug fixes
   - `docs/` for documentation
   - `refactor/` for refactoring

3. Convert description to kebab-case: "$ARGUMENTS"

Example: "add dark mode toggle" → `feat/add-dark-mode-toggle`
```

### 8. Create PR (`pr.md`)

```markdown
---
description: Create a pull request with generated description
allowed-tools: Bash(git:*), Bash(gh:*)
---

# Create Pull Request

## Context

- Current branch: !`git branch --show-current`
- Commits on branch: !`git log main..HEAD --oneline`
- Changed files: !`git diff main --name-only`

## Task

1. Check if PR already exists:
   ```bash
   gh pr view 2>/dev/null
   ```

2. If no PR exists, create one:
   - Generate title from branch name or commits
   - Write description summarizing changes
   - List key modifications
   - Note any breaking changes

3. Use `gh pr create` with generated content
```

---

## Advanced Command Features

### Dynamic Content with Bash (`!`)

Execute bash commands and inject output into the prompt:

```markdown
## Current State
- Git status: !`git status --short`
- Last 5 commits: !`git log --oneline -5`
- Node version: !`node --version`
```

### File References (`@`)

Include file contents in your command:

```markdown
# Review Implementation

Review the implementation in @src/utils/helpers.js

Compare with the spec in @docs/spec.md
```

### Arguments (`$ARGUMENTS`)

Capture user input:

```markdown
---
argument-hint: [search-term]
---

Search the codebase for: $ARGUMENTS

Find all occurrences and suggest improvements.
```

Usage: `/project:search authentication`

### Tool Restrictions

Limit what tools a command can use:

```markdown
---
allowed-tools: Read, Grep, Glob
---

This command can only read files, not modify them.
```

Common tool patterns:
- `Bash(git:*)` - All git commands
- `Bash(npm:*)` - All npm commands  
- `Read, Write` - File operations
- `Grep, Glob` - Search operations

### Model Selection

Use faster/cheaper models for simple tasks:

```markdown
---
model: haiku
---

Quick task that doesn't need deep reasoning.
```

---

## Real-World Example: PIV Loop Workflow

Based on the [habit-tracker](https://github.com/coleam00/habit-tracker) project's PIV (Prime, Implement, Validate) workflow:

### Directory Structure

```
.claude/
└── commands/
    ├── commit.md
    ├── init-project.md
    ├── create-prd.md
    ├── core_piv_loop/
    │   ├── prime.md
    │   ├── plan-feature.md
    │   └── execute.md
    ├── validation/
    │   ├── validate.md
    │   ├── code-review.md
    │   ├── code-review-fix.md
    │   ├── execution-report.md
    │   └── system-review.md
    └── github_bug_fix/
        ├── rca.md
        └── implement-fix.md
```

### Command Categories

| Category | Commands | Purpose |
|----------|----------|---------|
| **Core PIV Loop** | `prime`, `plan-feature`, `execute` | Main development workflow |
| **Validation** | `validate`, `code-review`, `code-review-fix` | Quality assurance |
| **Bug Fixing** | `rca`, `implement-fix` | Issue resolution |
| **Utility** | `commit`, `init-project`, `create-prd` | Common tasks |

### Sample: Prime Command (`core_piv_loop/prime.md`)

```markdown
---
description: Load project context and codebase understanding
allowed-tools: Read, Grep, Glob, Bash(find:*)
---

# Prime: Load Project Context

## Objectives

1. Read and understand the project structure
2. Load key configuration files
3. Understand coding conventions
4. Identify tech stack and dependencies

## Files to Examine

- @CLAUDE.md (project instructions)
- @README.md (project overview)
- @.claude/PRD.md (requirements, if exists)
- Package files (package.json, pyproject.toml)

## Output

Provide a summary of:
- Project purpose
- Tech stack
- Key directories
- Coding conventions
- Available commands
```

### Sample: Execute Command (`core_piv_loop/execute.md`)

```markdown
---
description: Execute an implementation plan step-by-step
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Execute Implementation Plan

## Prerequisites

Verify a plan exists in `.claude/plans/` or `.agents/plans/`

## Process

For each step in the plan:

1. **Read** the step requirements
2. **Implement** the changes
3. **Test** the implementation
4. **Validate** against acceptance criteria
5. **Mark** the step complete

## Rules

- Complete one step fully before moving to the next
- Run tests after each significant change
- If blocked, document the issue and continue
- Update the plan file with progress

## After Completion

Run `/project:validation:validate` to verify everything works.
```

---

## Organizing Commands with Namespaces

Use subdirectories to create logical groupings:

```
.claude/commands/
├── git/
│   ├── commit.md      → /project:git:commit
│   ├── branch.md      → /project:git:branch
│   └── pr.md          → /project:git:pr
├── testing/
│   ├── unit.md        → /project:testing:unit
│   ├── integration.md → /project:testing:integration
│   └── e2e.md         → /project:testing:e2e
└── docs/
    ├── readme.md      → /project:docs:readme
    └── api.md         → /project:docs:api
```

---

## Best Practices

### 1. Start Simple

Begin with 3-5 essential commands:
- `commit` - Commit workflow
- `validate` - Run tests and linting
- `review` - Code review
- `plan` - Feature planning
- `fix` - Bug fixing

### 2. Be Specific

Include exact instructions, not vague guidance:

```markdown
# ❌ Vague
Review the code.

# ✅ Specific
Review the code for:
1. SQL injection in user inputs
2. Missing null checks on API responses
3. Console.log statements that should be removed
```

### 3. Include Context

Use `!` to inject current state:

```markdown
## Current State
- Branch: !`git branch --show-current`
- Modified files: !`git status --short`
```

### 4. Use Appropriate Models

Fast tasks → `model: haiku`
Complex reasoning → `model: claude-sonnet-4-5-20250929` (default)

### 5. Version Control

Commit `.claude/commands/` to your repository so your team shares the same workflows.

### 6. Document Commands

Add clear descriptions in frontmatter:

```markdown
---
description: Run security audit on dependencies and code
---
```

### 7. Iterate and Improve

Start with basic commands and refine based on usage. Ask Claude to help improve your commands!

---

## Quick Setup Script

Create your initial command structure:

```bash
#!/bin/bash
# setup-claude-commands.sh

# Create directory structure
mkdir -p .claude/commands/{git,testing,validation}

# Create commit command
cat > .claude/commands/git/commit.md << 'EOF'
---
description: Create a git commit with conventional message
allowed-tools: Bash(git:*)
model: haiku
---

## Context
- Status: !`git status --short`
- Diff: !`git diff --cached`
- Recent commits: !`git log --oneline -5`

## Task
Create a commit with a conventional message (feat/fix/docs/refactor/test/chore).
EOF

# Create validate command
cat > .claude/commands/validation/validate.md << 'EOF'
---
description: Run full validation suite
allowed-tools: Bash, Read
---

# Validate

Run all checks:
1. Linting (with auto-fix)
2. Type checking
3. Tests with coverage
4. Build verification

Report results with ✅/❌ indicators.
EOF

# Create code review command
cat > .claude/commands/validation/review.md << 'EOF'
---
description: Code review on changed files
allowed-tools: Bash(git:*), Read, Grep
---

# Code Review

!`git diff --name-only HEAD~1`

Review for:
1. Logic errors and bugs
2. Security vulnerabilities
3. Performance issues
4. Test coverage
5. Code style

Provide prioritized, actionable feedback.
EOF

echo "✅ Claude commands created in .claude/commands/"
echo "📝 Customize these files for your project"
echo "🚀 Use /project:git:commit, /project:validation:validate, etc."
```

Run with:
```bash
chmod +x setup-claude-commands.sh
./setup-claude-commands.sh
```

---

## Getting Help

- **List all commands**: Type `/` in Claude Code
- **Command help**: `/help`
- **Official docs**: https://code.claude.com/docs/en/slash-commands
- **Community commands**: https://github.com/hesreallyhim/awesome-claude-code

---

*Happy coding with Claude!*
