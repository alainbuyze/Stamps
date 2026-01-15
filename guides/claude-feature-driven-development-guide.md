# Feature-Driven Development with Claude Code

A comprehensive guide to setting up projects for autonomous, feature-driven iteration using the patterns from Anthropic's `autonomous-coding` quickstart.

---

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Project Structure](#project-structure)
4. [The Two-Agent Pattern](#the-two-agent-pattern)
5. [Setting Up Your Project](#setting-up-your-project)
6. [The Feature List (Source of Truth)](#the-feature-list-source-of-truth)
7. [The Development Loop](#the-development-loop)
8. [Progress Tracking](#progress-tracking)
9. [Prompts and Commands](#prompts-and-commands)
10. [Adapting for Claude Code CLI](#adapting-for-claude-code-cli)
11. [Best Practices](#best-practices)
12. [Quick Setup Script](#quick-setup-script)

---

## Overview

Feature-driven development with Claude is a structured approach where:

1. **A detailed specification** defines what to build
2. **A feature list** breaks requirements into testable cases
3. **Claude works incrementally**, implementing one feature at a time
4. **Git persists progress** across sessions
5. **A progress file** tracks context between fresh context windows

This pattern enables building complete applications over multiple sessions, with each session picking up exactly where the last one left off.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Feature-Driven Development Flow                   │
└─────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  app_spec.txt │ ─────────────────────────────────────┐
    │ (Requirements)│                                       │
    └───────┬──────┘                                       │
            │                                               │
            ▼                                               │
    ┌──────────────┐                                       │
    │  INITIALIZER │                                       │
    │    AGENT     │                                       │
    └───────┬──────┘                                       │
            │ Creates:                                     │
            │  • feature_list.json (200+ tests)           │
            │  • init.sh (setup script)                   │
            │  • Project scaffolding                      │
            │  • Initial git commit                       │
            ▼                                               │
    ┌──────────────────────────────────────┐               │
    │          feature_list.json            │               │
    │      (Source of Truth - Tests)        │ ◄────────────┘
    └───────────────┬──────────────────────┘        Reads spec
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│   CODING     │ ─────► │   CODING     │ ─────► ...
│   AGENT #1   │        │   AGENT #2   │
└──────┬───────┘        └──────┬───────┘
       │                       │
       │ Implements            │ Implements
       │ Feature(s)            │ Feature(s)
       │                       │
       ▼                       ▼
┌──────────────┐        ┌──────────────┐
│  git commit  │        │  git commit  │
│  + progress  │        │  + progress  │
└──────────────┘        └──────────────┘
```

---

## Core Concepts

### The Problem This Solves

Claude Code has a finite context window. For large projects:
- Context gets exhausted mid-project
- Sessions end before work is complete
- Restarting loses all context

### The Solution

1. **Externalize state** to files (feature list, progress notes, git history)
2. **Use git** as the source of truth for code
3. **Use feature_list.json** as the backlog and completion tracker
4. **Use claude-progress.txt** for session handoff notes

### Key Principles

| Principle | Why It Matters |
|-----------|----------------|
| **Single Source of Truth** | `feature_list.json` is the canonical list of what to build |
| **Atomic Commits** | Each feature = one git commit with clear message |
| **Incremental Progress** | One feature at a time, fully tested before moving on |
| **Context Recovery** | Every session starts by reading state from files |
| **Verification First** | Always verify existing functionality before adding new |

---

## Project Structure

```
my_project/
├── app_spec.txt              # Application specification (PRD)
├── feature_list.json         # Test cases - THE source of truth
├── claude-progress.txt       # Session handoff notes
├── init.sh                   # Environment setup script
├── .claude/
│   ├── settings.json         # Claude Code settings
│   └── commands/
│       ├── init-session.md   # Session startup command
│       ├── implement-feature.md
│       ├── verify-features.md
│       └── end-session.md
├── CLAUDE.md                 # Project context for Claude
├── prompts/                  # (Optional) Stored prompts
│   ├── initializer.md
│   └── coding.md
├── src/                      # Application source code
├── tests/                    # Test files
└── verification/             # Screenshots and verification artifacts
```

---

## The Two-Agent Pattern

The pattern uses two specialized "agents" (really, two different prompts/contexts):

### 1. Initializer Agent (Session 1)

**Purpose:** Set up the foundation for all future work

**Responsibilities:**
- Read and analyze `app_spec.txt`
- Create `feature_list.json` with detailed test cases
- Create `init.sh` for environment setup
- Set up project scaffolding
- Initialize git repository
- Make first commit with foundation

**When it runs:** Only once, at project start

### 2. Coding Agent (Sessions 2+)

**Purpose:** Implement features incrementally

**Responsibilities:**
- Recover context from files (feature list, progress, git)
- Verify existing functionality still works
- Pick the next failing feature
- Implement and test it
- Mark as passing in `feature_list.json`
- Commit changes
- Document progress for next session

**When it runs:** Every session after initialization

---

## Setting Up Your Project

### Step 1: Create the Application Specification

Create `app_spec.txt` with detailed requirements:

```text
# Application Specification: Task Management App

## Overview
Build a modern task management application with real-time collaboration,
project organization, and progress tracking.

## Core Features

### User Management
- User registration with email/password
- OAuth login (Google, GitHub)
- Profile management with avatar upload
- Password reset flow

### Projects
- Create/edit/delete projects
- Project settings and permissions
- Team member management
- Project templates

### Tasks
- Create tasks with title, description, due date
- Assign tasks to team members
- Task status: todo, in-progress, review, done
- Subtasks and checklists
- File attachments
- Comments and mentions
- Task history/activity log

### Views
- Kanban board view
- List view with sorting/filtering
- Calendar view
- Timeline/Gantt view

## Technical Requirements
- Frontend: Next.js 14 with App Router
- Styling: Tailwind CSS
- Database: PostgreSQL with Prisma
- Auth: NextAuth.js
- Real-time: WebSockets or Server-Sent Events
- Testing: Playwright for E2E, Jest for unit tests

## Non-Functional Requirements
- Responsive design (mobile-first)
- Keyboard shortcuts for power users
- Dark/light theme support
- Loading states and optimistic updates
- Error handling with user-friendly messages

## API Design
RESTful API with the following endpoints:
- /api/auth/* - Authentication
- /api/projects/* - Project CRUD
- /api/tasks/* - Task CRUD
- /api/users/* - User management
```

**Tips for good specs:**
- Be specific about UI flows and edge cases
- Include technical stack decisions
- Define acceptance criteria
- Specify non-functional requirements
- The more detailed, the better the feature list

### Step 2: Create the Feature List Structure

Create `feature_list.json` (or let the initializer agent create it):

```json
[
  {
    "id": 1,
    "category": "setup",
    "priority": "critical",
    "description": "Project scaffolding with Next.js 14, Tailwind, and basic folder structure",
    "steps": [
      "Run: npx create-next-app@latest with TypeScript and Tailwind",
      "Verify: Project starts with npm run dev",
      "Verify: Homepage loads at localhost:3000"
    ],
    "passes": false
  },
  {
    "id": 2,
    "category": "setup",
    "priority": "critical",
    "description": "Database setup with Prisma and PostgreSQL",
    "steps": [
      "Install Prisma and initialize",
      "Create initial schema with User model",
      "Run migration",
      "Verify: Can connect to database"
    ],
    "passes": false
  },
  {
    "id": 3,
    "category": "auth",
    "priority": "high",
    "description": "User registration form with email/password",
    "steps": [
      "Navigate to /register",
      "Fill in email: test@example.com",
      "Fill in password: SecurePass123!",
      "Click Submit button",
      "Verify: User created in database",
      "Verify: Redirect to dashboard"
    ],
    "passes": false
  },
  {
    "id": 4,
    "category": "auth",
    "priority": "high",
    "description": "User login with email/password",
    "steps": [
      "Navigate to /login",
      "Enter registered email and password",
      "Click Login button",
      "Verify: Session created",
      "Verify: Redirect to dashboard",
      "Verify: User menu shows username"
    ],
    "passes": false
  },
  {
    "id": 5,
    "category": "functional",
    "priority": "high",
    "description": "Create new project from dashboard",
    "steps": [
      "Login as authenticated user",
      "Click 'New Project' button",
      "Enter project name: 'My First Project'",
      "Click Create",
      "Verify: Project appears in project list",
      "Verify: Redirect to project view"
    ],
    "passes": false
  }
]
```

### Feature List Schema

```json
{
  "id": "number - Unique identifier",
  "category": "string - setup|auth|functional|style|performance|edge-case",
  "priority": "string - critical|high|medium|low",
  "description": "string - What this feature/test verifies",
  "steps": ["array - Step-by-step verification instructions"],
  "passes": "boolean - false until verified, then true",
  "implemented_in": "string (optional) - Session/commit where implemented",
  "notes": "string (optional) - Implementation notes"
}
```

### Categories Explained

| Category | Description | Example |
|----------|-------------|---------|
| `setup` | Infrastructure, scaffolding, configuration | Database setup, CI/CD |
| `auth` | Authentication and authorization | Login, permissions |
| `functional` | Core features and user flows | Create task, edit project |
| `style` | UI/UX, visual design, responsiveness | Dark mode, mobile layout |
| `performance` | Speed, optimization | Lazy loading, caching |
| `edge-case` | Error handling, edge scenarios | Empty states, validation |

### Step 3: Create the Progress Tracking File

Create `claude-progress.txt`:

```text
# Claude Progress Notes
# This file tracks progress across sessions

## Project Status
- Initialized: [DATE]
- Total Features: [COUNT]
- Completed: 0
- Remaining: [COUNT]

## Session Log

### Session 1 - [DATE]
- Type: Initializer
- Completed:
  - Created feature_list.json with X test cases
  - Set up project scaffolding
  - Initialized git repository
- Notes:
  - Using Next.js 14 with App Router
  - PostgreSQL database configured
- Next Session Should:
  - Start implementing setup features
  - Begin with feature #1 (scaffolding verification)

---
(New sessions append below)
```

### Step 4: Create the Setup Script

Create `init.sh`:

```bash
#!/bin/bash
# Project initialization script
# Run this to set up the development environment

set -e

echo "🚀 Setting up development environment..."

# Check prerequisites
command -v node >/dev/null 2>&1 || { echo "Node.js is required"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required"; exit 1; }

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Set up environment
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local from template..."
    cp .env.example .env.local
    echo "⚠️  Please update .env.local with your configuration"
fi

# Database setup
echo "🗄️ Setting up database..."
npx prisma generate
npx prisma db push

# Verify setup
echo "✅ Running verification..."
npm run build

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo "  npm run dev"
echo ""
echo "Application will be available at:"
echo "  http://localhost:3000"
```

### Step 5: Create CLAUDE.md

Create `CLAUDE.md` for project context:

```markdown
# Task Management App

## Project Overview
A modern task management application with real-time collaboration.

## Quick Reference

### Commands
- `npm run dev` - Start development server (localhost:3000)
- `npm run build` - Production build
- `npm run test` - Run tests
- `npm run lint` - Run linter

### Key Files
- `app_spec.txt` - Full application specification
- `feature_list.json` - Test cases (SOURCE OF TRUTH)
- `claude-progress.txt` - Session progress notes

### Architecture
- Next.js 14 App Router
- Prisma ORM with PostgreSQL
- NextAuth.js for authentication
- Tailwind CSS for styling

### Development Workflow

**Starting a Session:**
1. Read `claude-progress.txt` for context
2. Check `feature_list.json` for next feature
3. Review recent git commits
4. Verify existing features still work
5. Implement next feature

**Ending a Session:**
1. Commit all changes with descriptive message
2. Update `feature_list.json` (mark passes: true)
3. Update `claude-progress.txt` with session notes
4. Document what the next session should do

### Feature Implementation Process
1. Read the feature from `feature_list.json`
2. Understand the verification steps
3. Implement the feature
4. Test manually following the steps
5. Take screenshots if UI changes
6. Mark as passing only after verification
7. Commit with message format:
   `feat: [description] - verified E2E`

### Rules
- NEVER remove or modify feature descriptions
- ONLY change `passes: false` to `passes: true`
- Always verify before marking complete
- One feature at a time
- Commit after each feature
```

---

## The Development Loop

### Session Startup Protocol

Every coding session should start with context recovery:

```bash
# 1. See your working directory
pwd

# 2. List files to understand project structure
ls -la

# 3. Read the project specification
cat app_spec.txt

# 4. Read the feature list (first 50 lines)
cat feature_list.json | head -100

# 5. Read progress notes from previous sessions
cat claude-progress.txt

# 6. Check recent git history
git log --oneline -20

# 7. Count remaining features
cat feature_list.json | grep '"passes": false' | wc -l

# 8. Find the next feature to implement
cat feature_list.json | jq '.[] | select(.passes == false) | .id' | head -1
```

### Feature Implementation Protocol

For each feature:

```
1. READ the feature specification
   ↓
2. UNDERSTAND what needs to be built
   ↓
3. VERIFY existing features still work
   ↓
4. IMPLEMENT the feature
   ↓
5. TEST following the exact steps
   ↓
6. VERIFY with screenshots (if UI)
   ↓
7. UPDATE feature_list.json (passes: true)
   ↓
8. COMMIT with descriptive message
   ↓
9. UPDATE claude-progress.txt
```

### Session End Protocol

Before ending each session:

```bash
# 1. Commit any pending changes
git add .
git commit -m "feat: [feature name] - verified E2E

- Added [specific changes]
- Tested with [method]
- Updated feature_list.json: marked feature #X as passing"

# 2. Update progress file
cat >> claude-progress.txt << 'EOF'

### Session [N] - [DATE]
- Completed Features: #X, #Y
- Work Done:
  - [Description of work]
- Issues Encountered:
  - [Any problems]
- Next Session Should:
  - Continue with feature #Z
  - [Any setup needed]
EOF

# 3. Final commit with progress
git add claude-progress.txt
git commit -m "docs: update progress notes for session [N]"
```

---

## Prompts and Commands

### Initializer Prompt

Create `.claude/commands/initialize-project.md`:

```markdown
---
description: Initialize a new feature-driven project
allowed-tools: Bash, Read, Write, Edit
---

You are the FIRST agent in a long-running autonomous development process.
Your job is to set up the foundation for all future coding sessions.

## Your Tasks

### 1. Read the Specification
Start by reading `app_spec.txt` in your working directory. This contains
the complete specification for what needs to be built.

### 2. Create Feature List
Create `feature_list.json` with detailed test cases. Structure:

```json
[
  {
    "id": 1,
    "category": "setup|auth|functional|style|performance|edge-case",
    "priority": "critical|high|medium|low",
    "description": "What this test verifies",
    "steps": ["Step 1", "Step 2", "Verify result"],
    "passes": false
  }
]
```

Create at least 50 features covering:
- Setup and infrastructure (10-15)
- Authentication flows (5-10)
- Core functionality (20-30)
- UI/UX polish (5-10)
- Edge cases and error handling (5-10)

### 3. Create Setup Script
Create `init.sh` that future sessions can use to set up the environment.

### 4. Initialize Git
```bash
git init
git add .
git commit -m "feat: initial project setup with feature list"
```

### 5. Create Progress File
Create `claude-progress.txt` documenting this session.

## Critical Rules
- Features can ONLY be marked as passing (false → true)
- NEVER remove or modify feature descriptions
- NEVER modify testing steps
- This ensures no functionality is missed

Begin by reading app_spec.txt.
```

### Coding Session Prompt

Create `.claude/commands/continue-development.md`:

```markdown
---
description: Continue feature-driven development
allowed-tools: Bash, Read, Write, Edit
---

You are continuing work on a long-running development task.
This is a FRESH context window - you have no memory of previous sessions.

## Recover Context First

Run these commands to understand the current state:

```bash
# 1. See working directory
pwd

# 2. List files
ls -la

# 3. Read specification
cat app_spec.txt

# 4. Read feature list
cat feature_list.json | head -100

# 5. Read progress notes
cat claude-progress.txt

# 6. Check git history
git log --oneline -20

# 7. Count remaining features
cat feature_list.json | grep '"passes": false' | wc -l
```

## Before Implementing New Features

The previous session may have introduced bugs. Run verification:

1. Start the development server
2. Test any recently implemented features
3. Fix any regressions before continuing

## Implementation Loop

For each feature:

1. **Read** - Get the next failing feature from feature_list.json
2. **Implement** - Write the code
3. **Test** - Follow the exact steps in the feature
4. **Verify** - Confirm it works (screenshots for UI)
5. **Update** - Change passes: false → passes: true
6. **Commit** - With descriptive message

## Commit Message Format

```
feat: [Feature description] - verified E2E

- Added [specific changes]
- Tested with [method]
- Updated feature_list.json: marked #X as passing
```

## Session Goals

- Complete at least ONE feature perfectly
- It's okay if you only complete one feature
- Quality over quantity
- There will be more sessions

## Before Ending Session

1. Commit all changes
2. Update claude-progress.txt
3. Document what next session should do

Focus on completing one feature perfectly before moving on.
```

### Verification Command

Create `.claude/commands/verify-features.md`:

```markdown
---
description: Verify all passing features still work
allowed-tools: Bash, Read
---

Run verification tests on all features marked as passing.

## Process

1. Read feature_list.json
2. For each feature where passes: true
3. Follow the test steps
4. Document any failures

## Output Format

```
Feature #1: [description]
- Status: ✅ PASS / ❌ FAIL
- Notes: [any observations]

Feature #2: ...
```

If any features fail, they need to be fixed before implementing new features.
```

---

## Adapting for Claude Code CLI

While Anthropic's quickstart uses the Agent SDK with Python orchestration, you can achieve similar results with Claude Code CLI using slash commands and good practices.

### Manual Session Flow

**Start a session:**
```bash
cd my-project
claude

# In Claude Code:
> /continue-development
```

**Or manually:**
```
> Read claude-progress.txt and feature_list.json. 
  Understand the current state and continue implementing 
  the next failing feature. Follow the feature-driven 
  development process documented in CLAUDE.md.
```

### Using Headless Mode for Automation

For automated/CI scenarios:

```bash
# Single feature implementation
claude -p "Read feature_list.json, implement the next failing feature, \
  verify it works, update the feature list, and commit. \
  Follow the process in CLAUDE.md." \
  --allowedTools "Bash,Read,Write,Edit"
```

### Batch Processing Script

```bash
#!/bin/bash
# run-feature-session.sh
# Run one feature implementation session

set -e

cd "$(dirname "$0")"

# Count remaining features
REMAINING=$(cat feature_list.json | grep '"passes": false' | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo "🎉 All features complete!"
    exit 0
fi

echo "📋 $REMAINING features remaining"
echo "🚀 Starting development session..."

# Run Claude Code in headless mode
claude -p "
You are continuing feature-driven development.

1. Read claude-progress.txt and feature_list.json
2. Verify existing features still work
3. Implement the NEXT failing feature
4. Test it following the exact steps
5. Update feature_list.json (passes: true)
6. Commit with descriptive message
7. Update claude-progress.txt

Focus on ONE feature only. Quality over quantity.
" --allowedTools "Bash,Read,Write,Edit"

echo "✅ Session complete"
echo "📋 $(cat feature_list.json | grep '"passes": false' | wc -l) features remaining"
```

---

## Best Practices

### 1. Write Detailed Specifications

❌ **Bad:**
```
Build a chat app.
```

✅ **Good:**
```
Build a real-time chat application with:
- User registration with email verification
- Direct messages between users
- Group channels with admin controls
- Message reactions and threading
- File attachments (images, documents)
- Typing indicators and read receipts
- Push notifications
- Search across all messages

Technical: Next.js 14, Socket.io, PostgreSQL
```

### 2. Make Features Small and Testable

❌ **Bad:**
```json
{
  "description": "Implement user authentication",
  "passes": false
}
```

✅ **Good:**
```json
{
  "description": "User registration form renders with email, password, and submit button",
  "steps": [
    "Navigate to /register",
    "Verify: Email input field exists",
    "Verify: Password input field exists",
    "Verify: Submit button exists"
  ],
  "passes": false
}
```

### 3. Maintain the Feature List Integrity

**CRITICAL RULES:**
- NEVER delete features
- NEVER modify feature descriptions
- NEVER change test steps
- ONLY change `passes: false` → `passes: true`

### 4. Commit After Each Feature

```bash
git add .
git commit -m "feat: user registration form - verified E2E

- Added /register route
- Created RegistrationForm component
- Added form validation
- Updated feature_list.json: #3 passing"
```

### 5. Document Session Handoffs

Always update `claude-progress.txt` with:
- What was completed
- Any issues encountered
- What the next session should do
- Current blockers

### 6. Verify Before Implementing

Each session should:
1. Run existing tests
2. Manually check recent features
3. Fix any regressions
4. THEN implement new features

### 7. Use Reasonable Feature Counts

| Project Size | Recommended Features |
|--------------|---------------------|
| Small (MVP) | 20-50 |
| Medium | 50-100 |
| Large | 100-200 |
| Enterprise | 200+ |

Start smaller - you can always add more features.

---

## Quick Setup Script

Bootstrap a feature-driven project:

```bash
#!/bin/bash
# setup-feature-driven-project.sh

set -e

PROJECT_NAME="${1:-my-project}"

echo "🚀 Setting up feature-driven project: $PROJECT_NAME"

# Create project directory
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Create directory structure
mkdir -p .claude/commands
mkdir -p prompts
mkdir -p src
mkdir -p tests
mkdir -p verification

# Create app_spec.txt template
cat > app_spec.txt << 'EOF'
# Application Specification

## Overview
[Describe what you're building]

## Core Features
[List the main features]

## Technical Requirements
[Specify the tech stack]

## Non-Functional Requirements
[Performance, security, UX requirements]
EOF

# Create feature_list.json template
cat > feature_list.json << 'EOF'
[
  {
    "id": 1,
    "category": "setup",
    "priority": "critical",
    "description": "Project initialization and basic scaffolding",
    "steps": [
      "Verify project structure exists",
      "Verify can run development server",
      "Verify homepage loads"
    ],
    "passes": false
  }
]
EOF

# Create claude-progress.txt
cat > claude-progress.txt << 'EOF'
# Claude Progress Notes

## Project Status
- Initialized: $(date +%Y-%m-%d)
- Total Features: 1 (add more after planning)
- Completed: 0
- Remaining: 1

## Session Log

### Session 0 - $(date +%Y-%m-%d)
- Type: Project Setup
- Completed: Created project structure
- Next Session Should:
  - Complete app_spec.txt with detailed requirements
  - Run /initialize-project to generate full feature list
EOF

# Create CLAUDE.md
cat > CLAUDE.md << 'EOF'
# Project Name

## Overview
[Brief description]

## Quick Reference

### Commands
- `npm run dev` - Start development
- `npm run test` - Run tests

### Key Files
- `app_spec.txt` - Application specification
- `feature_list.json` - Test cases (SOURCE OF TRUTH)
- `claude-progress.txt` - Session progress

### Development Workflow
1. Read claude-progress.txt for context
2. Check feature_list.json for next feature
3. Verify existing features work
4. Implement next feature
5. Test and verify
6. Update feature_list.json (passes: true)
7. Commit changes
8. Update claude-progress.txt

### Rules
- NEVER modify feature descriptions
- ONLY change passes: false → true
- One feature at a time
- Commit after each feature
EOF

# Create init.sh
cat > init.sh << 'EOF'
#!/bin/bash
set -e
echo "🚀 Setting up development environment..."
npm install
echo "✅ Setup complete! Run: npm run dev"
EOF
chmod +x init.sh

# Create initialize command
cat > .claude/commands/initialize-project.md << 'EOF'
---
description: Initialize feature list from app_spec.txt
---

Read app_spec.txt and create a comprehensive feature_list.json with
50+ detailed test cases covering:
- Setup (10-15 features)
- Core functionality (20-30 features)
- UI/UX (5-10 features)
- Edge cases (5-10 features)

Each feature must have:
- Unique id
- category (setup/auth/functional/style/edge-case)
- priority (critical/high/medium/low)
- description
- steps (array of verification steps)
- passes: false

After creating, initialize git and commit.
EOF

# Create continue command
cat > .claude/commands/continue-development.md << 'EOF'
---
description: Continue feature-driven development
---

1. Read claude-progress.txt and feature_list.json
2. Verify existing features still work
3. Implement the NEXT failing feature
4. Test following exact steps
5. Update feature_list.json (passes: true)
6. Commit with descriptive message
7. Update claude-progress.txt

Focus on ONE feature. Quality over quantity.
EOF

# Create verify command
cat > .claude/commands/verify-features.md << 'EOF'
---
description: Verify all passing features still work
---

For each feature where passes: true in feature_list.json:
1. Follow the test steps
2. Document pass/fail status
3. Report any regressions
EOF

# Initialize git
git init
git add .
git commit -m "feat: initial feature-driven project setup"

echo ""
echo "✅ Project created: $PROJECT_NAME"
echo ""
echo "Next steps:"
echo "1. Edit app_spec.txt with your requirements"
echo "2. Run: cd $PROJECT_NAME && claude"
echo "3. Use: /initialize-project to generate feature list"
echo "4. Use: /continue-development to implement features"
```

---

## Summary

Feature-driven development with Claude enables building complete applications through:

| Component | Purpose |
|-----------|---------|
| `app_spec.txt` | Detailed requirements |
| `feature_list.json` | Testable features (source of truth) |
| `claude-progress.txt` | Session handoff notes |
| `init.sh` | Environment setup |
| `CLAUDE.md` | Project context |
| `/initialize-project` | Generate feature list |
| `/continue-development` | Implement features |
| `/verify-features` | Regression testing |

**The key insight:** Externalize all state to files, let git persist code, and always recover context at session start.

---

## Resources

- [Anthropic autonomous-coding quickstart](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)
- [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Long-running agents guide](https://docs.anthropic.com/en/docs/agents/long-running-agents)

---

*Build complete applications one feature at a time!*
