# Claude Code Agents & Subagents Startup Guide

A comprehensive guide to creating, configuring, and orchestrating agents and subagents in Claude Code for specialized workflows and parallel execution.

---

## Table of Contents

1. [What Are Subagents?](#what-are-subagents)
2. [Subagents vs Skills vs Slash Commands](#subagents-vs-skills-vs-slash-commands)
3. [Built-in Subagents](#built-in-subagents)
4. [Directory Structure](#directory-structure)
5. [Subagent File Anatomy](#subagent-file-anatomy)
6. [Creating Subagents](#creating-subagents)
7. [Essential Starter Subagents](#essential-starter-subagents)
8. [Task Tool & Parallel Execution](#task-tool--parallel-execution)
9. [Orchestration Patterns](#orchestration-patterns)
10. [Advanced Usage](#advanced-usage)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)
13. [Quick Setup Script](#quick-setup-script)

---

## What Are Subagents?

Subagents are **specialized AI assistants** that Claude Code can delegate tasks to. Each subagent:

- Has its **own context window** (separate from the main conversation)
- Uses a **custom system prompt** that guides its behavior
- Can be configured with **specific tools** it's allowed to use
- Can use a **different model** (e.g., Haiku for speed, Opus for complexity)

**Key Benefits:**

| Benefit | Description |
|---------|-------------|
| **Context Preservation** | Each subagent operates in isolation, keeping the main conversation focused |
| **Specialized Expertise** | Custom prompts enable domain-specific knowledge and patterns |
| **Reusability** | Define once, use across projects and share with your team |
| **Flexible Permissions** | Each subagent can have different tool access levels |
| **Parallel Execution** | Run multiple subagents simultaneously for faster workflows |

---

## Subagents vs Skills vs Slash Commands

| Feature | Subagents | Skills | Slash Commands |
|---------|-----------|--------|----------------|
| **Context** | Separate window | Main conversation | Main conversation |
| **Invocation** | Automatic or explicit | Automatic (model-invoked) | Explicit (`/command`) |
| **Best for** | Isolated tasks, parallel work | Domain knowledge, workflows | Quick actions, shortcuts |
| **Can bundle scripts** | No | Yes | No |
| **Cross-platform** | Claude Code only | Works everywhere | Claude Code only |
| **Custom model** | ✅ Yes | ❌ No | ✅ Yes |
| **Tool restrictions** | ✅ Yes | ✅ Yes | ✅ Yes |

**When to use Subagents:**
- Tasks that produce verbose output you don't need in main context
- Work requiring specific tool restrictions
- Self-contained tasks that can return a summary
- Parallel execution of multiple independent tasks

**When to use Skills instead:**
- Reusable prompts that run in main conversation context
- When you need bundled scripts
- Cross-platform portability (Claude.ai, API)

---

## Built-in Subagents

Claude Code includes three built-in subagents that activate automatically:

### 1. Explore Subagent

**Purpose:** Fast, read-only codebase exploration

```
Model: Haiku (fast, low-latency)
Mode: Strictly read-only
Tools: Glob, Grep, Read, Bash (read-only commands only)
```

**When Claude uses it:**
- Searching or understanding a codebase without making changes
- File discovery and code exploration
- Quick lookups and pattern searches

**Thoroughness levels:**
- `quick` - Basic searches, fastest results
- `medium` - Balanced exploration
- `very thorough` - Comprehensive analysis

### 2. Plan Subagent

**Purpose:** Codebase research during plan mode

```
Model: Sonnet (capable analysis)
Mode: Research only
Tools: Read, Glob, Grep, Bash
```

**When Claude uses it:**
- In plan mode when Claude needs to understand your codebase
- Gathering context before presenting a plan
- Researching existing patterns and structure

### 3. General-Purpose Subagent

**Purpose:** Complex, multi-step tasks requiring both exploration and action

```
Model: Sonnet (capable reasoning)
Mode: Full read/write access
Tools: All tools available
```

**When Claude uses it:**
- Tasks requiring both exploration and modification
- Complex reasoning to interpret search results
- Multiple dependent steps

---

## Directory Structure

### Project Subagents (Shared via Git)

Available only in the current project:

```
your-project/
└── .claude/
    └── agents/
        ├── code-reviewer.md
        ├── test-runner.md
        └── debugger.md
```

**Priority:** Highest (overrides user subagents with same name)

### User Subagents (Personal/Global)

Available across all your projects:

```
~/.claude/
└── agents/
    ├── security-auditor.md
    ├── documentation-writer.md
    └── performance-analyzer.md
```

**Priority:** Lower than project subagents

### Plugin Subagents

Bundled with installed plugins, managed via `/agents` interface.

---

## Subagent File Anatomy

Each subagent is a Markdown file with YAML frontmatter:

```markdown
---
name: subagent-name
description: When this subagent should be invoked. Be specific!
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
permissionMode: default
skills: skill1, skill2
---

You are a [role description].

## Your Expertise
- Domain knowledge
- Specific capabilities

## Instructions
1. Step-by-step guidance
2. How to approach tasks
3. What to return

## Output Format
How to structure results for the main agent.
```

### Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | Unique identifier (lowercase, hyphens) |
| `description` | ✅ | When to invoke (critical for auto-delegation) |
| `tools` | ❌ | Comma-separated list. If omitted, inherits all tools |
| `model` | ❌ | `sonnet`, `opus`, `haiku`, or `inherit` |
| `permissionMode` | ❌ | `default`, `acceptEdits`, `bypassPermissions`, `plan` |
| `skills` | ❌ | Skills to auto-load when subagent starts |

### Model Selection

| Model | Use Case | Cost/Speed |
|-------|----------|------------|
| `haiku` | Fast lookups, simple tasks | Cheapest, fastest |
| `sonnet` | Balanced reasoning (default) | Medium |
| `opus` | Complex analysis, deep reasoning | Most capable, slowest |
| `inherit` | Match main conversation's model | Varies |

### Available Tools

**Read-only agents:**
```yaml
tools: Read, Grep, Glob
```

**Research agents:**
```yaml
tools: Read, Grep, Glob, WebFetch, WebSearch
```

**Code writers:**
```yaml
tools: Read, Write, Edit, Bash, Glob, Grep
```

**Full access:**
```yaml
# Omit tools field to inherit all
```

---

## Creating Subagents

### Method 1: Interactive (`/agents` - Recommended)

```
/agents
```

1. Select **Create new agent**
2. Choose **User-level** or **Project-level**
3. Select **Generate with Claude** (recommended)
4. Describe your subagent
5. Select tools (or leave blank to inherit all)
6. Press `e` to edit in your editor (optional)
7. Save

### Method 2: Manual File Creation

```bash
# Project subagent
mkdir -p .claude/agents
cat > .claude/agents/code-reviewer.md << 'EOF'
---
name: code-reviewer
description: Expert code review. Use proactively after code changes.
tools: Read, Grep, Glob
model: sonnet
---

You are a senior code reviewer...
EOF

# User subagent
mkdir -p ~/.claude/agents
# Create file...
```

### Method 3: CLI Flag (Session-specific)

```bash
claude --agents '{
  "quick-search": {
    "description": "Fast codebase search",
    "prompt": "You search codebases efficiently.",
    "tools": ["Read", "Grep", "Glob"],
    "model": "haiku"
  }
}'
```

---

## Essential Starter Subagents

### 1. Code Reviewer

```markdown
---
name: code-reviewer
description: Expert code review specialist. Use PROACTIVELY after writing or modifying code. Reviews for quality, security, and maintainability.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a senior code reviewer ensuring high standards of code quality and security.

## When Invoked

1. Run `git diff` to see recent changes
2. Focus on modified files
3. Begin review immediately

## Review Checklist

### Code Quality
- [ ] Code is simple and readable
- [ ] Functions/variables are well-named
- [ ] No duplicated code
- [ ] Appropriate comments

### Security
- [ ] No exposed secrets or API keys
- [ ] Input validation implemented
- [ ] No SQL injection risks
- [ ] Proper authentication/authorization

### Performance
- [ ] No unnecessary loops
- [ ] Efficient algorithms
- [ ] Caching where appropriate

### Testing
- [ ] Adequate test coverage
- [ ] Edge cases tested

## Output Format

Organize feedback by priority:
- 🔴 **Critical** - Must fix before merge
- 🟠 **Warning** - Should fix soon
- 🟡 **Minor** - Nice to have
- 💡 **Suggestion** - Consider improving

Include specific line numbers and code examples for each issue.
```

### 2. Test Runner

```markdown
---
name: test-runner
description: Test automation expert. Use PROACTIVELY to run tests and fix failures. Invoke when tests need to be run or when test failures occur.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---

You are a test automation expert focused on maintaining test quality.

## When Invoked

1. Detect the test framework (Jest, pytest, vitest, etc.)
2. Run the appropriate test command
3. If tests fail, analyze failures
4. Fix issues while preserving test intent

## Test Strategy

### For Test Failures
1. Read the failing test carefully
2. Understand what it's testing
3. Check if implementation or test is wrong
4. Fix the root cause, not symptoms

### For New Code
1. Identify untested functionality
2. Write tests following AAA pattern (Arrange, Act, Assert)
3. Cover edge cases
4. Run to verify

## Output Format

```
Test Results: X passed, Y failed, Z skipped

Failed Tests:
1. test_name - Expected X, got Y
   Root cause: [explanation]
   Fix: [what was changed]

Coverage: X% (target: 80%)
```
```

### 3. Debugger

```markdown
---
name: debugger
description: Debugging specialist for errors, exceptions, and unexpected behavior. Use PROACTIVELY when encountering any errors or issues.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
---

You are an expert debugger specializing in root cause analysis.

## When Invoked

1. Capture error message and stack trace
2. Identify reproduction steps
3. Isolate the failure location
4. Implement minimal fix
5. Verify solution works

## Debugging Process

### Analysis
- Parse error messages and stack traces
- Check recent code changes (`git diff`, `git log`)
- Identify the exact line/function failing

### Hypothesis Testing
- Form hypothesis about root cause
- Add strategic debug logging
- Test hypothesis with minimal changes

### Resolution
- Implement the smallest fix that works
- Verify fix doesn't break other functionality
- Remove debug code

## Output Format

```
Error: [error message]
Location: [file:line]

Root Cause:
[Explanation of what went wrong and why]

Fix Applied:
[Description of the change]

Verification:
[How the fix was verified]

Prevention:
[Recommendations to prevent similar issues]
```
```

### 4. Security Auditor

```markdown
---
name: security-auditor
description: Security specialist for vulnerability scanning and secure coding. Use when reviewing code for security issues or before deploying.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a security expert specializing in application security.

## When Invoked

Scan the codebase for common vulnerabilities:

### OWASP Top 10
1. Injection (SQL, Command, etc.)
2. Broken Authentication
3. Sensitive Data Exposure
4. XML External Entities (XXE)
5. Broken Access Control
6. Security Misconfiguration
7. Cross-Site Scripting (XSS)
8. Insecure Deserialization
9. Using Components with Known Vulnerabilities
10. Insufficient Logging & Monitoring

### Code Patterns to Check
- Hardcoded credentials
- Unvalidated user input
- Missing authentication/authorization
- Insecure cryptography
- Debug code in production
- Exposed error messages

## Output Format

```
Security Audit Report

🔴 CRITICAL (must fix immediately):
- [finding with location and remediation]

🟠 HIGH (fix before release):
- [finding with location and remediation]

🟡 MEDIUM (fix soon):
- [finding with location and remediation]

📋 Recommendations:
- [general security improvements]
```
```

### 5. Documentation Writer

```markdown
---
name: documentation-writer
description: Documentation specialist. Use when creating or updating documentation, READMEs, or API docs.
tools: Read, Write, Edit, Glob, Grep
model: sonnet
---

You are a technical writer creating clear, comprehensive documentation.

## When Invoked

1. Analyze the target code/project
2. Identify documentation needs
3. Generate appropriate documentation

## Documentation Types

### README.md
- Project title and description
- Installation instructions
- Quick start / Usage examples
- Configuration options
- Contributing guidelines
- License

### API Documentation
- Endpoint overview
- Authentication
- Request/response examples
- Error codes
- Rate limits

### Code Documentation
- Function/class purpose
- Parameters with types
- Return values
- Usage examples

## Style Guidelines

- Use clear, concise language
- Include runnable code examples
- Document edge cases and limitations
- Use consistent formatting
- Write for your audience level

## Output Format

Return complete, formatted documentation ready to be saved to file.
```

### 6. Data Scientist

```markdown
---
name: data-scientist
description: Data analysis expert for SQL queries, data processing, and insights. Use for data analysis tasks, BigQuery operations, or database queries.
tools: Bash, Read, Write, Grep
model: sonnet
---

You are a data scientist specializing in SQL and data analysis.

## When Invoked

1. Understand the data analysis requirement
2. Write efficient SQL queries
3. Use appropriate tools (bq, psql, etc.)
4. Analyze and summarize results
5. Present findings clearly

## SQL Best Practices

- Use appropriate indexes
- Avoid SELECT * (specify columns)
- Use CTEs for complex queries
- Include comments for complex logic
- Consider query cost/performance

## Analysis Workflow

1. **Explore**: Understand data structure and schema
2. **Query**: Write optimized SQL
3. **Validate**: Check results make sense
4. **Summarize**: Present key findings
5. **Recommend**: Suggest next steps

## Output Format

```
Analysis: [topic]

Query:
[SQL query used]

Results:
[Key findings]

Insights:
[What the data tells us]

Recommendations:
[Suggested actions]
```
```

---

## Task Tool & Parallel Execution

The **Task tool** allows running multiple subagents in parallel, each with its own context window.

### Basic Parallel Execution

```
> Explore the codebase using 4 tasks in parallel.
  Each agent should explore different directories.
```

Claude will spawn multiple Task agents:

```
● Task(Explore backend structure)
  ⎿ Done (17 tool uses · 56.6k tokens · 1m 34.3s)
● Task(Explore frontend structure)
  ⎿ Done (23 tool uses · 48.9k tokens · 1m 15.9s)
● Task(Explore configuration)
  ⎿ Done (28 tool uses · 45.2k tokens · 1m 2.1s)
● Task(Explore tests)
  ⎿ Done (15 tool uses · 32.1k tokens · 45.2s)
```

### Key Characteristics

| Aspect | Details |
|--------|---------|
| **Parallelism cap** | Max 10 concurrent tasks |
| **Context overhead** | ~20k tokens per task |
| **Batching** | Waits for batch to complete before next |
| **Communication** | Tasks cannot communicate with each other |

### Tasks vs Custom Subagents

| Tasks | Custom Subagents |
|-------|------------------|
| Ephemeral (one-off) | Persistent (reusable) |
| Inherit main context's config | Custom system prompt |
| Good for parallel search | Good for specialized expertise |
| No custom prompts | Detailed instructions |

---

## Orchestration Patterns

### Pattern 1: Parallel Research

```
> Use 3 subagents in parallel to:
  1. Search for authentication patterns in the codebase
  2. Find all API endpoints
  3. Identify database schemas
```

### Pattern 2: Pipeline Workflow

```
> First use the code-analyzer subagent to find performance issues,
  then use the optimizer subagent to fix them,
  then use the test-runner subagent to verify the changes.
```

### Pattern 3: Master-Clone Architecture

Let the main agent orchestrate clones of itself:

```
> Break this refactoring into independent tasks.
  Use Task() to spawn parallel agents for each file.
  Coordinate the results when all complete.
```

### Pattern 4: Specialist Team

Create a team of specialists in your CLAUDE.md:

```markdown
## Subagent Team

When implementing features, use this workflow:

1. **product-manager** - Define requirements and acceptance criteria
2. **architect** - Design technical approach
3. **implementer** - Write the code
4. **test-runner** - Verify with tests
5. **code-reviewer** - Final quality check

Chain these subagents in sequence for complex features.
```

### Pattern 5: Parallel File Processing

For large-scale operations across many files:

```
> Deprecate the old API across all 75 files that use it.
  Use parallel tasks, one per file, to make the changes safely.
```

---

## Advanced Usage

### Resumable Subagents

Continue a previous subagent's work:

```
> Use the code-analyzer agent to review the auth module
[Agent completes, returns agentId: "abc123"]

> Resume agent abc123 and now also analyze authorization
[Agent continues with full context from previous conversation]
```

### Chaining Subagents

```
> Use the security-auditor to scan the codebase,
  then use the debugger to fix any critical vulnerabilities,
  then use the test-runner to verify the fixes.
```

### Background Execution

Send a subagent to background while you keep working:

```
[Subagent running...]
Ctrl + B  # Send to background
[Continue working in main thread]
```

### Skills Integration

Auto-load skills when subagent starts:

```yaml
---
name: pdf-processor
description: Process PDF documents
tools: Read, Write, Bash
skills: pdf-processing, document-analysis
---
```

### MCP Integration

Subagents can access MCP tools from configured servers:

```yaml
---
name: database-analyst
description: Analyze database schemas and queries
tools: Read, Grep, mcp__postgres__query, mcp__postgres__schema
---
```

---

## Best Practices

### 1. Write Specific Descriptions

**❌ Vague:**
```yaml
description: Reviews code
```

**✅ Specific:**
```yaml
description: Expert code review specialist. Use PROACTIVELY after writing or modifying code. Reviews for quality, security, and maintainability.
```

Include "PROACTIVELY" or "MUST BE USED" to encourage automatic delegation.

### 2. Start with Claude-Generated Agents

Use `/agents` → Generate with Claude → Customize. This gives you a solid foundation to iterate on.

### 3. Design Focused Agents

One agent = One responsibility

**✅ Good:**
- `code-reviewer` - Reviews code
- `test-runner` - Runs tests
- `debugger` - Fixes bugs

**❌ Bad:**
- `do-everything` - Too broad

### 4. Limit Tool Access

Only grant necessary tools:

```yaml
# Read-only reviewer
tools: Read, Grep, Glob

# Full implementation access
tools: Read, Write, Edit, Bash, Glob, Grep
```

### 5. Version Control Project Agents

Check `.claude/agents/` into git so your team benefits:

```bash
git add .claude/agents/
git commit -m "Add team subagents"
```

### 6. Balance Parallelism vs Cost

Each parallel task has ~20k token overhead. Group related operations:

**❌ Expensive:**
```
> Create 100 tasks, one per file
```

**✅ Efficient:**
```
> Create 10 tasks, each handling 10 files
```

---

## Troubleshooting

### Subagent Not Being Used

| Issue | Solution |
|-------|----------|
| Vague description | Add specific trigger words |
| Wrong location | Check `~/.claude/agents/` or `.claude/agents/` |
| Not loaded | Restart Claude Code or use `/agents` |

### Subagent Errors

| Issue | Solution |
|-------|----------|
| Missing tools | Add required tools to `tools` field |
| Permission denied | Check `permissionMode` setting |
| MCP tools not working | Verify MCP server is connected and tools are listed |

### Debug with `/agents`

```
/agents
```

View all available subagents and their configurations.

### Important Limitations

1. **Subagents cannot spawn other subagents** - No nested delegation
2. **No stepwise plans** - Subagents execute immediately
3. **No interactive thinking** - Progress not visible until completion
4. **Context isolation** - Subagents can't share information directly

---

## Quick Setup Script

Bootstrap your subagent structure:

```bash
#!/bin/bash
# setup-claude-agents.sh

# Create user agents directory
mkdir -p ~/.claude/agents

# Code Reviewer
cat > ~/.claude/agents/code-reviewer.md << 'EOF'
---
name: code-reviewer
description: Expert code review. Use PROACTIVELY after code changes. Reviews for quality, security, and best practices.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a senior code reviewer.

## Review Process
1. Run `git diff` to see changes
2. Analyze modified files
3. Check for issues

## Checklist
- Code quality and readability
- Security vulnerabilities
- Performance issues
- Test coverage

## Output
Organize by priority: 🔴 Critical, 🟠 Warning, 🟡 Minor, 💡 Suggestion
Include line numbers and fix examples.
EOF

# Test Runner
cat > ~/.claude/agents/test-runner.md << 'EOF'
---
name: test-runner
description: Test automation expert. Use PROACTIVELY to run tests and fix failures.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---

You are a test automation expert.

## Process
1. Detect test framework
2. Run tests
3. Analyze failures
4. Fix while preserving test intent

## Output
Test results summary with pass/fail counts, failure analysis, and fixes applied.
EOF

# Debugger
cat > ~/.claude/agents/debugger.md << 'EOF'
---
name: debugger
description: Debugging specialist. Use PROACTIVELY when encountering errors or unexpected behavior.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
---

You are an expert debugger.

## Process
1. Capture error and stack trace
2. Identify root cause
3. Implement minimal fix
4. Verify solution

## Output
Root cause explanation, fix applied, and prevention recommendations.
EOF

# Security Auditor
cat > ~/.claude/agents/security-auditor.md << 'EOF'
---
name: security-auditor
description: Security specialist. Use when reviewing code for vulnerabilities or before deployment.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a security expert.

## Scan For
- OWASP Top 10 vulnerabilities
- Hardcoded credentials
- Unvalidated input
- Insecure cryptography

## Output
Security report with findings by severity (Critical/High/Medium) and remediation steps.
EOF

echo "✅ Subagents created in ~/.claude/agents/"
echo "📝 Run /agents in Claude Code to view and manage"
echo "🚀 Subagents will be available in your next session"
```

Run with:
```bash
chmod +x setup-claude-agents.sh
./setup-claude-agents.sh
```

---

## Community Resources

| Resource | Description |
|----------|-------------|
| [awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 100+ specialized subagents |
| [Claude Code Docs](https://code.claude.com/docs/en/sub-agents) | Official documentation |
| [Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) | Building deployable agents |

---

## Summary: When to Use What

```
┌─────────────────────────────────────────────────────────────────┐
│                    Decision Framework                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Need separate context window?                                  │
│  ├── YES → Subagent                                            │
│  └── NO → Skill or Slash Command                               │
│                                                                 │
│  Need parallel execution?                                       │
│  ├── YES → Task tool (ephemeral) or multiple Subagents         │
│  └── NO → Single Subagent or Skill                             │
│                                                                 │
│  Need bundled scripts?                                          │
│  ├── YES → Skill                                               │
│  └── NO → Subagent or Slash Command                            │
│                                                                 │
│  Need cross-platform (API, Claude.ai)?                          │
│  ├── YES → Skill                                               │
│  └── NO → Subagent (Claude Code only)                          │
│                                                                 │
│  Quick one-off action?                                          │
│  ├── YES → Slash Command                                       │
│  └── NO → Skill (automatic) or Subagent (isolated)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*Build your team of specialized AI assistants!*
