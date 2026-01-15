# Claude Code Skills Startup Guide

A comprehensive guide to creating, organizing, and using Agent Skills in Claude Code to extend Claude's capabilities.

---

## Table of Contents

1. [What Are Skills?](#what-are-skills)
2. [Skills vs Slash Commands vs Subagents](#skills-vs-slash-commands-vs-subagents)
3. [Directory Structure](#directory-structure)
4. [Skill File Anatomy](#skill-file-anatomy)
5. [How Skills Work: Progressive Disclosure](#how-skills-work-progressive-disclosure)
6. [Essential Starter Skills](#essential-starter-skills)
7. [Advanced Skill Features](#advanced-skill-features)
8. [Multi-File Skills with Scripts](#multi-file-skills-with-scripts)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Quick Setup Script](#quick-setup-script)

---

## What Are Skills?

Skills are **model-invoked** capabilities that teach Claude how to perform specific tasks. Unlike slash commands (which you explicitly type), Skills are automatically discovered and used by Claude when your request matches the Skill's description.

**Key Benefits:**
- Work across Claude.ai, Claude Code, and the Claude API
- Automatically activated based on context
- Can bundle executable scripts for deterministic operations
- Support progressive disclosure to manage context efficiently
- Shareable via git or plugins

**Example:** If you have a PDF processing Skill, simply saying "extract text from this PDF" will trigger Claude to use it automatically.

---

## Skills vs Slash Commands vs Subagents

| Feature | Skills | Slash Commands | Subagents |
|---------|--------|----------------|-----------|
| **Invocation** | Model-invoked (automatic) | User-invoked (`/command`) | User or model-invoked |
| **Context** | Added to current conversation | Executed immediately | Separate context window |
| **Best for** | Domain knowledge, workflows | Quick actions, shortcuts | Isolated tasks, parallelism |
| **Location** | `skills/` directory | `commands/` directory | `agents/` directory |
| **Can bundle scripts** | ✅ Yes | ❌ No | ✅ Yes |
| **Cross-platform** | ✅ Works everywhere | ❌ Claude Code only | ❌ Claude Code only |

**When to use Skills:**
- Teaching Claude domain-specific knowledge
- Complex multi-step workflows
- When you need bundled scripts
- When you want cross-platform portability

**When to use Slash Commands:**
- Quick, on-demand actions
- When you want explicit control
- Simple prompts without scripts

---

## Directory Structure

### Personal Skills (Global)

Available across all your projects:

```
~/.claude/skills/
├── code-review/
│   └── SKILL.md
├── commit-helper/
│   └── SKILL.md
└── pdf-processing/
    ├── SKILL.md
    ├── REFERENCE.md
    └── scripts/
        └── extract.py
```

### Project Skills (Shared via Git)

Available only in the current project, shared with your team:

```
your-project/
└── .claude/
    └── skills/
        ├── api-testing/
        │   └── SKILL.md
        └── database-queries/
            ├── SKILL.md
            └── scripts/
                └── query_helper.py
```

### Plugin Skills

Skills bundled with installed plugins are automatically available.

---

## Skill File Anatomy

Every Skill requires a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: skill-name-in-kebab-case
description: What this skill does and WHEN to use it. Include trigger words users might say.
allowed-tools: Read, Grep, Glob, Bash
---

# Skill Title

## Overview
Brief description of the skill's purpose.

## When to Use This Skill
- Trigger condition 1
- Trigger condition 2

## Instructions
Step-by-step guidance for Claude.

## Examples
Concrete examples showing the skill in action.

## Best Practices
Guidelines and recommendations.
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | Lowercase letters, numbers, hyphens (max 64 chars) |
| `description` | ✅ | What + When (max 1024 chars). Critical for discovery! |
| `allowed-tools` | ❌ | Restrict tools Claude can use |
| `model` | ❌ | Override model (e.g., `haiku` for speed) |

---

## How Skills Work: Progressive Disclosure

Skills use a three-level loading system to manage context efficiently:

```
┌─────────────────────────────────────────────────────────────┐
│ Level 1: Metadata (~100 tokens)                             │
│ ─────────────────────────────────                           │
│ At startup, Claude loads only name + description            │
│ from all available skills                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (if skill matches request)
┌─────────────────────────────────────────────────────────────┐
│ Level 2: SKILL.md Body (<5k tokens)                         │
│ ─────────────────────────────────────                       │
│ Full instructions loaded when Claude determines             │
│ the skill is relevant                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (as needed during execution)
┌─────────────────────────────────────────────────────────────┐
│ Level 3: Bundled Resources                                  │
│ ──────────────────────────                                  │
│ Scripts, references, templates loaded only when needed      │
└─────────────────────────────────────────────────────────────┘
```

This design allows you to have many Skills without overwhelming the context window.

---

## Essential Starter Skills

### 1. Code Review Skill

```markdown
---
name: code-reviewer
description: Review code for best practices, security issues, and potential bugs. Use when reviewing code, checking PRs, analyzing code quality, or when user says "review this code".
allowed-tools: Read, Grep, Glob
---

# Code Reviewer

## Review Checklist

1. **Code Quality**
   - Readability and maintainability
   - Consistent naming conventions
   - Appropriate comments and documentation

2. **Logic & Correctness**
   - Edge cases handled
   - Error handling present
   - No race conditions

3. **Security**
   - Input validation
   - No SQL injection risks
   - No exposed credentials
   - Proper authentication/authorization

4. **Performance**
   - No unnecessary loops
   - Efficient algorithms
   - Caching opportunities

5. **Testing**
   - Adequate test coverage
   - Edge cases tested

## Output Format

Provide feedback organized by priority:
- 🔴 **Critical**: Must fix before merge
- 🟠 **Major**: Should fix soon
- 🟡 **Minor**: Nice to have
- 💡 **Suggestion**: Consider for future

Include specific line numbers and code examples for each issue.
```

### 2. Commit Message Generator

```markdown
---
name: commit-message-generator
description: Generate clear, conventional commit messages from git diffs. Use when writing commit messages, reviewing staged changes, or when user mentions commits.
allowed-tools: Bash(git:*)
---

# Commit Message Generator

## Instructions

1. Run `git diff --staged` to see changes
2. Analyze what was changed
3. Generate commit message following Conventional Commits

## Commit Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Rules
- Subject line: max 50 characters, imperative mood
- Body: explain what and why (not how)
- Footer: reference issues (e.g., `Closes #123`)

## Examples

**Good:**
```
feat(auth): add OAuth2 login support

Implement OAuth2 authentication flow with Google and GitHub providers.
Add token refresh logic and secure session management.

Closes #456
```

**Bad:**
```
updated stuff
```
```

### 3. API Testing Skill

```markdown
---
name: api-tester
description: Test REST APIs and validate responses. Use when testing API endpoints, verifying responses, debugging API calls, or when user mentions API testing.
allowed-tools: Bash(curl:*), Read, Write
---

# API Tester

## When to Use This Skill

- Testing HTTP endpoints
- Validating response structures
- Debugging API issues
- Creating API test scripts

## Instructions

1. Identify the endpoint to test
2. Determine HTTP method and parameters
3. Send request using curl
4. Validate response status and body
5. Report results

## Request Examples

### GET Request
```bash
curl -s -X GET "https://api.example.com/users/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### POST Request
```bash
curl -s -X POST "https://api.example.com/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com"}'
```

## Response Validation

Check for:
- ✅ Expected status code (200, 201, etc.)
- ✅ Required fields present
- ✅ Correct data types
- ✅ Valid JSON structure
- ✅ Response time acceptable

## Output Format

```
Endpoint: POST /api/users
Status: 201 Created ✅
Response Time: 145ms
Body Validation: 
  - id: present ✅
  - name: "John" ✅
  - email: valid format ✅
```
```

### 4. Documentation Generator

```markdown
---
name: documentation-generator
description: Generate comprehensive documentation for code, APIs, and projects. Use when creating README files, API docs, code documentation, or when user asks to document something.
allowed-tools: Read, Write, Grep, Glob
---

# Documentation Generator

## Documentation Types

### 1. README.md
Structure:
- Project title and description
- Installation instructions
- Usage examples
- Configuration options
- Contributing guidelines
- License

### 2. API Documentation
Structure:
- Endpoint overview
- Authentication
- Request/response examples
- Error codes
- Rate limits

### 3. Code Documentation
Structure:
- Function/class purpose
- Parameters with types
- Return values
- Usage examples
- Edge cases

## Instructions

1. Analyze the target code/project
2. Identify key components
3. Generate appropriate documentation type
4. Include practical examples
5. Follow style conventions

## Best Practices

- Use clear, concise language
- Include runnable code examples
- Document edge cases and limitations
- Keep documentation close to code
- Update docs when code changes
```

### 5. Test Generator

```markdown
---
name: test-generator
description: Generate comprehensive tests for code. Use when writing unit tests, integration tests, creating test suites, or when user asks to test something.
allowed-tools: Read, Write, Bash
---

# Test Generator

## Test Pyramid

```
        ╱╲
       ╱  ╲ E2E (10%)
      ╱────╲
     ╱      ╲ Integration (20%)
    ╱────────╲
   ╱          ╲ Unit Tests (70%)
  ╱────────────╲
```

## Instructions

1. Analyze the code to test
2. Identify testable units
3. Generate tests following the pyramid
4. Include edge cases
5. Add meaningful assertions

## Test Categories

### Unit Tests
- Pure functions
- Business logic
- Validators
- Utilities

### Integration Tests
- API endpoints
- Database operations
- External service calls

### E2E Tests
- Critical user flows
- Happy paths
- Error scenarios

## Test Structure (AAA Pattern)

```python
def test_function_name():
    # Arrange - Set up test data
    input_data = {...}
    expected = {...}
    
    # Act - Execute the function
    result = function_under_test(input_data)
    
    # Assert - Verify the result
    assert result == expected
```

## Edge Cases to Consider

- Empty inputs
- Null/undefined values
- Boundary values
- Invalid types
- Large datasets
- Concurrent access
- Network failures
```

### 6. Database Query Helper

```markdown
---
name: database-query-helper
description: Help write and optimize database queries. Use when writing SQL, optimizing queries, designing schemas, or when user mentions database or SQL.
allowed-tools: Read, Bash
---

# Database Query Helper

## When to Use This Skill

- Writing SQL queries
- Optimizing slow queries
- Designing database schemas
- Debugging query issues

## Query Patterns

### Select with Joins
```sql
SELECT u.name, o.total
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.created_at > '2024-01-01'
ORDER BY o.total DESC
LIMIT 10;
```

### Aggregations
```sql
SELECT 
    category,
    COUNT(*) as count,
    AVG(price) as avg_price,
    SUM(quantity) as total_qty
FROM products
GROUP BY category
HAVING COUNT(*) > 5;
```

## Optimization Tips

1. **Use indexes** on frequently queried columns
2. **Avoid SELECT *** - specify needed columns
3. **Use EXPLAIN** to analyze query plans
4. **Batch large operations**
5. **Use appropriate data types**

## Common Issues

| Problem | Solution |
|---------|----------|
| N+1 queries | Use JOINs or batch loading |
| Full table scans | Add appropriate indexes |
| Slow JOINs | Check index coverage |
| Lock contention | Use row-level locking |
```

### 7. Git Workflow Skill

```markdown
---
name: git-workflow
description: Help with Git operations, branching strategies, and resolving conflicts. Use when working with Git, managing branches, resolving merge conflicts, or rebasing.
allowed-tools: Bash(git:*)
---

# Git Workflow

## Branching Strategy

```
main ─────●─────●─────●─────●───
          │           ↑
          │     merge │
          ▼           │
feature ──●───●───●───●
```

### Branch Naming
- `feat/` - New features
- `fix/` - Bug fixes
- `hotfix/` - Production fixes
- `docs/` - Documentation
- `refactor/` - Code improvements

## Common Operations

### Create Feature Branch
```bash
git checkout main
git pull origin main
git checkout -b feat/my-feature
```

### Sync with Main
```bash
git fetch origin
git rebase origin/main
```

### Interactive Rebase (clean history)
```bash
git rebase -i HEAD~3
# pick, squash, reword commits
```

### Resolve Conflicts
1. Identify conflicting files: `git status`
2. Open and resolve conflicts
3. Stage resolved files: `git add <file>`
4. Continue: `git rebase --continue`

## Best Practices

- Commit early and often
- Write meaningful commit messages
- Keep branches short-lived
- Review before merging
- Never force push to shared branches
```

---

## Advanced Skill Features

### Tool Restrictions

Limit what tools a Skill can use:

```markdown
---
name: safe-analyzer
description: Analyze code without modifications
allowed-tools: Read, Grep, Glob
---
```

Common tool patterns:
- `Read, Grep, Glob` - Read-only access
- `Bash(git:*)` - Only git commands
- `Bash, Read, Write` - Full file operations

### Bundled Scripts

Include executable code in your Skill:

```
my-skill/
├── SKILL.md
└── scripts/
    ├── analyze.py
    └── validate.sh
```

In SKILL.md:
```markdown
## Running Analysis

Execute the analysis script:
```bash
python scripts/analyze.py <input-file>
```

The script handles complex validation that's more reliable as code.
```

### Reference Files

Split large Skills into multiple files:

```
pdf-processor/
├── SKILL.md          # Main instructions
├── FORMS.md          # Form filling details
├── REFERENCE.md      # API reference
└── TROUBLESHOOTING.md
```

Reference from SKILL.md:
```markdown
For form filling, see [FORMS.md](FORMS.md).
For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
```

Claude loads these only when needed.

---

## Multi-File Skills with Scripts

### Complete Example: PDF Processing Skill

```
pdf-processing/
├── SKILL.md
├── REFERENCE.md
├── scripts/
│   ├── extract_text.py
│   ├── fill_form.py
│   └── merge_pdfs.py
└── templates/
    └── form_template.json
```

**SKILL.md:**
```markdown
---
name: pdf-processing
description: Extract text, fill forms, merge PDFs, and analyze documents. Use when working with PDF files, forms, document extraction, or when user mentions PDFs.
allowed-tools: Bash, Read, Write
---

# PDF Processing

## Capabilities

1. **Text Extraction** - Extract text and tables from PDFs
2. **Form Filling** - Fill PDF forms programmatically
3. **Merging** - Combine multiple PDFs
4. **Analysis** - Analyze document structure

## Quick Start

### Extract Text
```bash
python scripts/extract_text.py document.pdf
```

### Fill Form
```bash
python scripts/fill_form.py form.pdf data.json output.pdf
```

### Merge PDFs
```bash
python scripts/merge_pdfs.py file1.pdf file2.pdf merged.pdf
```

## Requirements

```bash
pip install pypdf pdfplumber
```

For detailed API reference, see [REFERENCE.md](REFERENCE.md).

## Output

Extracted text is formatted as Markdown with:
- Headers preserved
- Tables converted to Markdown tables
- Page numbers indicated
```

**scripts/extract_text.py:**
```python
#!/usr/bin/env python3
"""Extract text from PDF files."""
import sys
import pdfplumber

def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    text_content = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                text_content.append(f"## Page {i}\n\n{text}")
    
    return "\n\n".join(text_content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract_text.py <pdf_file>")
        sys.exit(1)
    
    result = extract_text(sys.argv[1])
    print(result)
```

---

## Best Practices

### 1. Write Effective Descriptions

The description is **critical** - it determines when Claude uses your Skill.

**❌ Bad (too vague):**
```yaml
description: Helps with documents
```

**✅ Good (specific triggers):**
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files, forms, or document extraction.
```

Include:
- **What** the skill does
- **When** to use it
- **Keywords** users might say

### 2. Keep Skills Focused

One Skill = One capability

**✅ Focused:**
- `pdf-text-extraction`
- `git-commit-messages`
- `api-testing`

**❌ Too broad:**
- `document-processing` → Split by document type
- `all-dev-tools` → Split by function

### 3. Use Progressive Disclosure

Keep SKILL.md concise (<500 lines). Move detailed content to separate files:

```
my-skill/
├── SKILL.md           # Core instructions (brief)
├── REFERENCE.md       # Detailed API docs
├── EXAMPLES.md        # Extended examples
└── TROUBLESHOOTING.md # Common issues
```

### 4. Include Concrete Examples

Show, don't just tell:

```markdown
## Example

**Input:**
```json
{"name": "John", "age": 30}
```

**Expected Output:**
```
User John is 30 years old.
```
```

### 5. Test Your Skills

After creating a Skill:

1. Ask Claude: "What Skills are available?"
2. Try trigger phrases from your description
3. Test with teammates
4. Iterate based on feedback

---

## Troubleshooting

### Skill Not Triggering

| Issue | Solution |
|-------|----------|
| Vague description | Add specific trigger words and contexts |
| Wrong location | Check `~/.claude/skills/` or `.claude/skills/` |
| YAML errors | Validate frontmatter syntax |
| Not restarted | Restart Claude Code after changes |

**Debug command:**
```bash
claude --debug
```

### Common YAML Issues

```yaml
# ❌ Wrong - tabs
name:	my-skill

# ✅ Correct - spaces
name: my-skill

# ❌ Wrong - unquoted special chars
description: Use for: testing

# ✅ Correct - quoted
description: "Use for: testing"
```

### Verify Skill Location

```bash
# Personal Skills
ls ~/.claude/skills/*/SKILL.md

# Project Skills
ls .claude/skills/*/SKILL.md
```

---

## Quick Setup Script

Bootstrap your skills structure:

```bash
#!/bin/bash
# setup-claude-skills.sh

# Create personal skills directory
mkdir -p ~/.claude/skills

# Create code-review skill
mkdir -p ~/.claude/skills/code-review
cat > ~/.claude/skills/code-review/SKILL.md << 'EOF'
---
name: code-reviewer
description: Review code for best practices, security issues, and bugs. Use when reviewing code, checking PRs, or analyzing code quality.
allowed-tools: Read, Grep, Glob
---

# Code Reviewer

## Review Checklist

1. Code quality and readability
2. Security vulnerabilities
3. Performance issues
4. Test coverage
5. Documentation

## Output Format

Organize by priority:
- 🔴 Critical
- 🟠 Major
- 🟡 Minor
- 💡 Suggestion
EOF

# Create commit-helper skill
mkdir -p ~/.claude/skills/commit-helper
cat > ~/.claude/skills/commit-helper/SKILL.md << 'EOF'
---
name: commit-message-generator
description: Generate conventional commit messages from git diffs. Use when writing commits or reviewing staged changes.
allowed-tools: Bash(git:*)
---

# Commit Message Generator

## Format
```
<type>(<scope>): <subject>
```

## Types
- feat, fix, docs, style, refactor, test, chore

## Instructions
1. Run `git diff --staged`
2. Analyze changes
3. Generate commit following conventions
EOF

# Create test-generator skill
mkdir -p ~/.claude/skills/test-generator
cat > ~/.claude/skills/test-generator/SKILL.md << 'EOF'
---
name: test-generator
description: Generate comprehensive tests for code. Use when writing unit tests, integration tests, or test suites.
allowed-tools: Read, Write, Bash
---

# Test Generator

## Test Structure (AAA)
1. **Arrange** - Set up test data
2. **Act** - Execute function
3. **Assert** - Verify result

## Edge Cases
- Empty inputs
- Null values
- Boundaries
- Invalid types
- Large datasets
EOF

echo "✅ Skills created in ~/.claude/skills/"
echo "📝 Restart Claude Code to load skills"
echo "🔍 Ask Claude: 'What Skills are available?'"
```

Run with:
```bash
chmod +x setup-claude-skills.sh
./setup-claude-skills.sh
```

---

## Popular Community Skills

| Skill | Description | Source |
|-------|-------------|--------|
| **docx** | Create/edit Word documents | Anthropic Official |
| **pdf** | PDF manipulation toolkit | Anthropic Official |
| **pptx** | PowerPoint creation | Anthropic Official |
| **xlsx** | Excel spreadsheet handling | Anthropic Official |
| **webapp-testing** | Playwright browser testing | Anthropic Official |
| **mcp-builder** | Create MCP servers | Anthropic Official |
| **frontend-design** | UI/UX design generation | Anthropic Official |
| **skill-creator** | Interactive skill builder | Anthropic Official |

### Finding More Skills

- **Official Skills**: `/plugin marketplace`
- **GitHub**: Search "awesome-claude-skills"
- **Community**: [Claude Skills Library](https://mcpservers.org/claude-skills)

---

## Resources

- **Official Documentation**: https://code.claude.com/docs/en/skills
- **Best Practices**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices
- **Agent Skills Spec**: https://agentskills.io
- **Engineering Blog**: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

---

*Build Skills that make Claude smarter for your specific workflows!*
