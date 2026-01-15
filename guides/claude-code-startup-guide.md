# Claude Code Startup Guide

A comprehensive guide to getting started with Claude Code, Anthropic's command-line tool for agentic coding.

---

## Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Project Initialization](#project-initialization)
4. [Configuring CLAUDE.md](#configuring-claudemd)
5. [Project Configuration Examples](#project-configuration-examples)
6. [Additional Configuration](#additional-configuration)
7. [Best Practices](#best-practices)
8. [Common Commands](#common-commands)

---

## Installation

Install Claude Code globally using npm:

```bash
npm install -g @anthropic-ai/claude-code
```

Verify the installation:

```bash
claude --version
```

---

## Basic Usage

### Starting Claude Code

Navigate to your project directory and run:

```bash
claude
```

This starts Claude Code in interactive mode, where you can have a conversation about your codebase.

### Running with a Task

You can also start Claude with a specific task:

```bash
claude "explain this codebase"
claude "fix the bug in auth.ts"
claude "write tests for the user service"
```

### One-shot Mode

For quick, non-interactive tasks:

```bash
claude -p "what does this project do"
```

---

## Project Initialization

Claude Code automatically detects your project structure when you run it in a directory. For optimal results:

1. Navigate to your project root
2. Run `claude`
3. Claude will analyze your codebase and be ready to assist

For a more customized experience, create a `CLAUDE.md` file (see next section).

---

## Configuring CLAUDE.md

The `CLAUDE.md` file provides Claude with context about your project. Place it in your project root.

### Basic Template

```markdown
# Project Overview

Brief description of what your project does and its purpose.

# Tech Stack

- Language: [e.g., TypeScript, Python, Go]
- Framework: [e.g., Next.js, FastAPI, Gin]
- Database: [e.g., PostgreSQL, MongoDB]
- Other tools: [e.g., Redis, Docker, Kubernetes]

# Project Structure

- `/src` - main source code
- `/tests` - test files
- `/docs` - documentation
- `/scripts` - utility scripts

# Code Conventions

- Naming: use camelCase for variables, PascalCase for components
- Formatting: Prettier with default settings
- Linting: ESLint with strict mode

# Common Commands

- `npm run dev` - start development server
- `npm test` - run tests
- `npm run lint` - run linter
- `npm run build` - production build

# Important Context

Add any non-obvious information about your project here:
- Special architecture decisions
- External service integrations
- Known limitations or gotchas
```

### What to Include

| Section | Purpose |
|---------|---------|
| Project Overview | High-level description of the project |
| Tech Stack | Languages, frameworks, and tools used |
| Project Structure | Directory layout and organization |
| Code Conventions | Naming, formatting, and style guidelines |
| Common Commands | Build, test, and deployment commands |
| Important Context | Gotchas, integrations, and special notes |

---

## Project Configuration Examples

### TypeScript/Node.js Project

```markdown
# Project Overview

A REST API for managing user authentication and profiles.

# Tech Stack

- Language: TypeScript 5.x
- Runtime: Node.js 20
- Framework: Express.js
- Database: PostgreSQL with Prisma ORM
- Testing: Jest + Supertest

# Project Structure

- `/src/routes` - API route handlers
- `/src/services` - business logic
- `/src/models` - Prisma schema and types
- `/src/middleware` - Express middleware
- `/src/utils` - helper functions
- `/tests` - test files mirroring src structure

# Code Conventions

- Use async/await over Promises
- Prefer functional programming patterns
- All functions must have TypeScript types
- Use Zod for runtime validation

# Common Commands

- `npm run dev` - start with hot reload
- `npm test` - run Jest tests
- `npm run test:watch` - run tests in watch mode
- `npm run db:migrate` - run Prisma migrations
- `npm run db:generate` - regenerate Prisma client

# Important Context

- Authentication uses JWT with refresh tokens
- All API responses follow the format: `{ data, error, meta }`
- Database connections are pooled via Prisma
- Environment variables are validated at startup
```

### Python Project

```markdown
# Project Overview

A machine learning pipeline for text classification.

# Tech Stack

- Language: Python 3.11
- Framework: FastAPI
- ML: PyTorch, Transformers
- Database: SQLite (dev), PostgreSQL (prod)
- Task Queue: Celery with Redis

# Project Structure

- `/app` - FastAPI application
- `/app/api` - API endpoints
- `/app/models` - ML models and database models
- `/app/services` - business logic
- `/ml` - training scripts and notebooks
- `/tests` - pytest test files

# Code Conventions

- Follow PEP 8
- Use type hints everywhere
- Docstrings in Google format
- Use Pydantic for data validation

# Common Commands

- `poetry run uvicorn app.main:app --reload` - start dev server
- `poetry run pytest` - run tests
- `poetry run pytest --cov` - run tests with coverage
- `poetry run black .` - format code
- `poetry run mypy .` - type checking

# Important Context

- Models are loaded lazily on first request
- Use `@cached` decorator for expensive computations
- Celery tasks are in `/app/tasks`
- GPU is optional; falls back to CPU
```

### React/Next.js Project

```markdown
# Project Overview

An e-commerce storefront with cart and checkout functionality.

# Tech Stack

- Framework: Next.js 14 (App Router)
- Language: TypeScript
- Styling: Tailwind CSS
- State: Zustand
- API: tRPC
- Database: PlanetScale (MySQL)

# Project Structure

- `/app` - Next.js app router pages
- `/components` - React components
  - `/components/ui` - reusable UI primitives
  - `/components/features` - feature-specific components
- `/lib` - utilities and configurations
- `/server` - tRPC routers and procedures
- `/stores` - Zustand stores

# Code Conventions

- Components: PascalCase, one per file
- Hooks: prefix with `use`
- Server components by default; add 'use client' only when needed
- Colocate styles with components using Tailwind

# Common Commands

- `npm run dev` - start Next.js dev server
- `npm run build` - production build
- `npm run test` - run Vitest
- `npm run db:push` - push schema to PlanetScale

# Important Context

- Use Server Components for data fetching
- Cart state persists to localStorage
- Images served via Cloudinary
- Payments handled by Stripe
```

---

## Additional Configuration

### .claudeignore

Similar to `.gitignore`, this file tells Claude which files to ignore:

```
# Dependencies
node_modules/
vendor/

# Build outputs
dist/
build/
.next/

# Large files
*.min.js
*.bundle.js

# Sensitive files
.env
.env.local
secrets/
```

### Hierarchical Configuration

You can place `CLAUDE.md` files in subdirectories for context specific to those areas:

```
project/
├── CLAUDE.md              # Root config
├── frontend/
│   └── CLAUDE.md          # Frontend-specific context
└── backend/
    └── CLAUDE.md          # Backend-specific context
```

Claude reads all relevant `CLAUDE.md` files up the directory tree.

---

## Best Practices

### Writing Effective CLAUDE.md Files

1. **Be specific** - Include exact command names, file paths, and conventions
2. **Keep it updated** - Update CLAUDE.md when your project changes
3. **Include examples** - Show examples of good patterns in your codebase
4. **Document gotchas** - Note anything non-obvious or counterintuitive
5. **List dependencies** - Mention key libraries and how they're used

### Working with Claude Code

1. **Start with context** - Ask Claude to explain the codebase first
2. **Be specific** - Provide file names and specific requirements
3. **Review changes** - Always review Claude's proposed changes before accepting
4. **Iterate** - Refine your requests based on results
5. **Use git** - Commit before major changes so you can easily revert

### Security Considerations

1. Never include secrets or API keys in CLAUDE.md
2. Use `.claudeignore` to exclude sensitive files
3. Review all code changes before committing
4. Be cautious with commands that modify system files

---

## Common Commands

| Command | Description |
|---------|-------------|
| `claude` | Start interactive mode |
| `claude "task"` | Start with a specific task |
| `claude -p "query"` | One-shot query (non-interactive) |
| `claude --help` | Show help and options |
| `claude --version` | Show version |

---

## Getting Help

- Documentation: https://docs.anthropic.com/claude-code
- Support: https://support.anthropic.com
- Feedback: Use the thumbs down button in Claude's responses

---

*Happy coding with Claude!*
