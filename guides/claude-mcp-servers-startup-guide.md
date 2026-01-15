# Claude Code MCP Servers Startup Guide

A comprehensive guide to installing, configuring, and using Model Context Protocol (MCP) servers with Claude Code to extend its capabilities.

---

## Table of Contents

1. [What is MCP?](#what-is-mcp)
2. [How MCP Works](#how-mcp-works)
3. [Installation Basics](#installation-basics)
4. [Essential MCP Servers](#essential-mcp-servers)
5. [Additional Useful MCPs](#additional-useful-mcps)
6. [Configuration & Management](#configuration--management)
7. [Using MCPs Effectively](#using-mcps-effectively)
8. [Troubleshooting](#troubleshooting)
9. [Quick Setup Script](#quick-setup-script)
10. [Best Practices](#best-practices)

---

## What is MCP?

**Model Context Protocol (MCP)** is Anthropic's open standard for connecting AI models to external tools, data sources, and services. Think of it as a universal adapter that lets Claude Code "talk" to external systems.

**Without MCP:**
```
You → Claude Code → Text responses only
```

**With MCP:**
```
You → Claude Code → GitHub, Browsers, Databases, APIs, File Systems, etc.
```

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **Extended Capabilities** | Claude can browse the web, manage repos, query databases |
| **Real-time Data** | Access current documentation, live APIs, fresh search results |
| **Automation** | Control browsers, manage files, trigger CI/CD pipelines |
| **Modular Design** | Add only the capabilities you need |
| **Standardized** | Works across Claude Code, Claude Desktop, and other clients |

---

## How MCP Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code                               │
│                     (MCP Client)                                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│ Playwright │  │  GitHub   │  │ Context7  │
│ MCP Server │  │MCP Server │  │MCP Server │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘
      │              │              │
      ▼              ▼              ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│  Browser  │  │ GitHub API│  │   Docs    │
└───────────┘  └───────────┘  └───────────┘
```

Each MCP server:
- Exposes **tools** that Claude can call
- Handles authentication and API communication
- Returns structured data to Claude

---

## Installation Basics

### Command Syntax

```bash
claude mcp add <name> [options] -- <command> [args]
```

### Scope Options (`-s`)

| Scope | Flag | Location | Availability |
|-------|------|----------|--------------|
| **Local** | `-s local` (default) | Current project only | Just you, this project |
| **User** | `-s user` | `~/.claude.json` | You, all projects |
| **Project** | `-s project` | `.mcp.json` (git-tracked) | Everyone on the project |

**Recommendation:** Use `-s user` for personal tools you want everywhere.

### Verify Installation

```bash
# List all installed MCPs
claude mcp list

# In Claude Code, see available tools
/mcp
```

### Remove an MCP

```bash
claude mcp remove <name>
```

---

## Essential MCP Servers

These are the most universally useful MCPs that work for virtually any project.

### 1. Playwright - Browser Automation ⭐ (Most Recommended)

**What it does:** Controls a real browser - navigate sites, fill forms, click buttons, take screenshots, scrape data, test UIs.

**Why you need it:** Many developers say this is the *only* MCP they need. It solves countless problems: testing UIs, scraping documentation, automating web tasks, debugging frontend issues.

```bash
claude mcp add playwright -s user -- npx -y @playwright/mcp@latest
```

**Usage Examples:**
```
> Use playwright to navigate to example.com and take a screenshot
> Use playwright to fill out the contact form with test data
> Use playwright to extract all product prices from this e-commerce page
> Use playwright to test the login flow on our staging site
```

**Available Tools:**
- `browser_navigate` - Go to URL
- `browser_click` - Click elements
- `browser_type` - Enter text
- `browser_screenshot` - Capture page
- `browser_snapshot` - Get accessibility tree
- `browser_execute_javascript` - Run JS

**Pro Tip:** The browser window stays visible, so you can manually log into sites and then let Claude continue with your authenticated session.

---

### 2. Context7 - Up-to-date Documentation ⭐

**What it does:** Fetches current documentation for thousands of libraries and frameworks, injecting it into Claude's context.

**Why you need it:** Eliminates the #1 frustration with AI coding - outdated or hallucinated APIs. Claude generates code using *actual current syntax*.

```bash
claude mcp add context7 -s user -- npx -y @upstash/context7-mcp@latest
```

**Usage Examples:**
```
> Create a Next.js 14 server component. use context7
> Implement authentication with Supabase. use context7
> Set up a Cloudflare Worker to cache JSON. use context7
```

**How it works:**
1. You mention a library/framework
2. Context7 fetches the latest docs
3. Claude gets accurate, current information
4. Generated code actually works!

**Before Context7:**
```
Ask about Redis Streams → Get hallucinated code → Debug for hours
```

**After Context7:**
```
Ask about Redis Streams, use context7 → Get working code → Ship it
```

---

### 3. Sequential Thinking - Complex Problem Solving ⭐

**What it does:** Enables Claude to break down complex problems into manageable steps with structured reasoning.

**Why you need it:** Better results for debugging, architecture decisions, planning, and any task requiring multi-step thinking.

```bash
claude mcp add sequential-thinking -s user -- npx -y @modelcontextprotocol/server-sequential-thinking
```

**Usage Examples:**
```
> Walk me through debugging why deployments are failing
> Help me plan the migration from Heroku to AWS with zero downtime
> Break down the steps to implement CI/CD for this monorepo
> Analyze this complex algorithm and suggest optimizations
```

**Best for:**
- Debugging tricky issues
- Architectural decisions
- Multi-step planning
- Complex refactoring

---

### 4. GitHub - Repository Management

**What it does:** Full GitHub integration - manage repos, issues, PRs, CI/CD, commits, and more.

**Why you need it:** Never leave your terminal to manage GitHub. Claude can create PRs, review code, manage issues, and trigger workflows.

**Option A: Using Docker (Recommended)**
```bash
claude mcp add github -s user \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here \
  -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server
```

**Option B: Using npx**
```bash
claude mcp add github -s user \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here \
  -- npx -y @modelcontextprotocol/server-github
```

**Getting a GitHub Token:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`, `read:user`

**Usage Examples:**
```
> Create a PR from my feature branch with a summary of changes
> Find all open issues labeled "bug" in this repo
> Show me the failed CI checks on the latest commit
> Create an issue for the authentication bug we discussed
```

---

### 5. Filesystem - Extended File Access

**What it does:** Gives Claude controlled access to read/write files outside the current project directory.

**Why you need it:** Cross-project operations, analyzing logs in other directories, managing files across your system.

```bash
claude mcp add filesystem -s user -- npx -y @modelcontextprotocol/server-filesystem \
  ~/Projects \
  ~/Documents \
  ~/Downloads \
  ~/Desktop
```

**Customize the paths** to directories you want Claude to access.

**Usage Examples:**
```
> Find all package.json files in my Projects folder
> Analyze the log file in ~/Downloads/server.log
> Copy the config template from ~/Documents to this project
```

**Security Note:** Only grant access to directories you actually need.

---

### 6. Fetch - Web Content Retrieval

**What it does:** Retrieves content from URLs - web pages, APIs, documentation.

**Why you need it:** Claude can fetch and read web content, API responses, and online documentation.

```bash
claude mcp add fetch -s user -- npx -y @kazuph/mcp-fetch
```

**Usage Examples:**
```
> Fetch the README from this GitHub repo URL
> Get the JSON response from this API endpoint
> Retrieve the documentation page at this URL
```

---

### 7. Brave Search - Web Search

**What it does:** Enables web search capability using Brave Search API.

**Why you need it:** Research, finding solutions, staying current with latest information.

**Requires:** Free API key from [Brave Search API](https://brave.com/search/api/)

```bash
claude mcp add brave-search -s user \
  -e BRAVE_API_KEY=your_api_key_here \
  -- npx -y @modelcontextprotocol/server-brave-search
```

**Usage Examples:**
```
> Search for best practices for React Server Components
> Find recent articles about the new TypeScript 5.5 features
> Look up solutions for this specific error message
```

---

## Additional Useful MCPs

### Database Access

**PostgreSQL:**
```bash
claude mcp add postgres -s user \
  -e DATABASE_URL=postgresql://user:pass@localhost:5432/dbname \
  -- npx -y @modelcontextprotocol/server-postgres
```

**SQLite:**
```bash
claude mcp add sqlite -s user -- npx -y @modelcontextprotocol/server-sqlite
```

### Productivity & Project Management

**Linear (Issue Tracking):**
```bash
claude mcp add linear -s user \
  -e LINEAR_API_KEY=your_key \
  -- npx -y @linear/mcp-server
```

**Notion:**
```bash
npx @composio/mcp@latest setup notion --client claude
```

### Development Tools

**Puppeteer (Alternative to Playwright):**
```bash
claude mcp add puppeteer -s user -- npx -y @modelcontextprotocol/server-puppeteer
```

**Semgrep (Security Scanning):**
```bash
claude mcp add semgrep -s user -- npx -y @semgrep/mcp-server
```

**Memory Bank (Persistent Memory):**
```bash
claude mcp add memory -s user -- npx -y @modelcontextprotocol/server-memory
```

### Universal MCP (Composio Rube)

**What it does:** Single MCP that connects to 500+ apps (GitHub, Figma, Linear, Slack, etc.)

```bash
npx @composio/mcp@latest setup rube --client claude
```

**Why consider it:** Instead of managing many MCPs, one server handles multiple integrations.

---

## Configuration & Management

### View Current Configuration

```bash
# List all MCPs
claude mcp list

# View detailed config (stored in ~/.claude.json)
cat ~/.claude.json | jq '.mcpServers'
```

### Configuration Locations

| Scope | File Location |
|-------|---------------|
| User | `~/.claude.json` |
| Project (local) | `.claude/settings.local.json` |
| Project (shared) | `.mcp.json` |

### Add MCP with JSON (Advanced)

```bash
claude mcp add-json playwright '{
  "command": "npx",
  "args": ["@playwright/mcp@latest"],
  "env": {
    "PLAYWRIGHT_HEADLESS": "false"
  }
}'
```

### Environment Variables

Pass environment variables with `-e`:

```bash
claude mcp add myserver -s user \
  -e API_KEY=xxx \
  -e DEBUG=true \
  -- npx -y my-mcp-server
```

### Project-Shared Configuration (`.mcp.json`)

Share MCPs with your team via git:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

---

## Using MCPs Effectively

### Explicit Invocation

The first time you use an MCP, explicitly mention it:

```
> Use playwright to navigate to example.com
> Search using brave-search for React best practices
> Use context7 to get the latest Next.js documentation
```

After the first use, Claude usually remembers to use it automatically.

### Check Available Tools

```
/mcp
```

Navigate to an MCP server to see all its available tools.

### Debug Mode

Launch Claude Code with MCP debugging:

```bash
claude --mcp-debug
```

This shows detailed logs about MCP connections and tool calls.

### Combining MCPs

MCPs work together seamlessly:

```
> Search for the best React testing practices using brave-search,
  then use playwright to test our login component,
  and create a GitHub issue with the results
```

---

## Troubleshooting

### MCP Not Connecting

**Symptoms:** `/mcp` shows server but no tools, or server not listed

**Solutions:**
1. Restart Claude Code
2. Check the command works standalone:
   ```bash
   npx -y @playwright/mcp@latest
   ```
3. Run with debug flag:
   ```bash
   claude --mcp-debug
   ```
4. Remove and re-add:
   ```bash
   claude mcp remove playwright
   claude mcp add playwright -s user -- npx -y @playwright/mcp@latest
   ```

### Environment Variable Issues

**Symptoms:** Authentication failures, "API key not found"

**Solutions:**
1. Verify the variable is set:
   ```bash
   echo $GITHUB_PERSONAL_ACCESS_TOKEN
   ```
2. Re-add with explicit variable:
   ```bash
   claude mcp add github -s user \
     -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_actual_token \
     -- npx -y @modelcontextprotocol/server-github
   ```

### Slow Startup

**Symptoms:** Claude Code takes long to start

**Cause:** Too many MCPs loading

**Solutions:**
1. Remove unused MCPs
2. Limit to 2-4 essential MCPs
3. Use project-specific MCPs instead of user-wide

### Common Errors

| Error | Solution |
|-------|----------|
| "Server not found" | Check command path, ensure npx works |
| "Connection refused" | Restart Claude Code, check for port conflicts |
| "Permission denied" | Check file permissions, API token scopes |
| "Timeout" | Server may be slow to start, increase timeout |

### View Logs

**macOS:**
```bash
ls ~/Library/Logs/Claude/
cat ~/Library/Logs/Claude/mcp-server-*.log
```

**Windows:**
```
%APPDATA%\Claude\logs\
```

**Linux:**
```bash
ls ~/.config/Claude/logs/
```

---

## Quick Setup Script

Bootstrap the essential MCPs with one script:

```bash
#!/bin/bash
# setup-essential-mcps.sh

set -e

echo "🚀 Installing Essential MCP Servers for Claude Code"
echo "=================================================="

# Check if claude is installed
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code not found. Please install it first."
    exit 1
fi

# 1. Playwright - Browser Automation
echo ""
echo "📦 Installing Playwright (Browser Automation)..."
claude mcp add playwright -s user -- npx -y @playwright/mcp@latest
echo "✅ Playwright installed"

# 2. Context7 - Up-to-date Documentation
echo ""
echo "📦 Installing Context7 (Documentation)..."
claude mcp add context7 -s user -- npx -y @upstash/context7-mcp@latest
echo "✅ Context7 installed"

# 3. Sequential Thinking - Complex Problem Solving
echo ""
echo "📦 Installing Sequential Thinking..."
claude mcp add sequential-thinking -s user -- npx -y @modelcontextprotocol/server-sequential-thinking
echo "✅ Sequential Thinking installed"

# 4. Fetch - Web Content
echo ""
echo "📦 Installing Fetch (Web Content)..."
claude mcp add fetch -s user -- npx -y @kazuph/mcp-fetch
echo "✅ Fetch installed"

# 5. Filesystem (Optional - customize paths)
echo ""
echo "📦 Installing Filesystem (customize paths as needed)..."
claude mcp add filesystem -s user -- npx -y @modelcontextprotocol/server-filesystem \
  ~/Projects \
  ~/Documents
echo "✅ Filesystem installed"

echo ""
echo "=================================================="
echo "🎉 Essential MCPs installed successfully!"
echo ""
echo "📋 Installed servers:"
claude mcp list
echo ""
echo "💡 Tips:"
echo "   - Run '/mcp' in Claude Code to see available tools"
echo "   - Say 'use playwright' or 'use context7' explicitly at first"
echo "   - For GitHub, run the manual command with your token"
echo ""
echo "🔧 Optional: Add GitHub MCP"
echo "   claude mcp add github -s user \\"
echo "     -e GITHUB_PERSONAL_ACCESS_TOKEN=your_token \\"
echo "     -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server"
echo ""
echo "🔧 Optional: Add Brave Search (requires API key)"
echo "   claude mcp add brave-search -s user \\"
echo "     -e BRAVE_API_KEY=your_key \\"
echo "     -- npx -y @modelcontextprotocol/server-brave-search"
```

**Run with:**
```bash
chmod +x setup-essential-mcps.sh
./setup-essential-mcps.sh
```

---

## Best Practices

### 1. Start Small

Begin with 2-3 essential MCPs:
- **Playwright** - Browser automation
- **Context7** - Documentation
- **Sequential Thinking** - Better reasoning

Add more as you discover specific needs.

### 2. Use User Scope for Personal Tools

```bash
claude mcp add playwright -s user -- ...
```

This makes the MCP available in all your projects.

### 3. Use Project Scope for Team Tools

Create `.mcp.json` in your repo for MCPs the whole team needs:

```json
{
  "mcpServers": {
    "custom-api": {
      "command": "npx",
      "args": ["-y", "our-custom-mcp"]
    }
  }
}
```

### 4. Secure Your Credentials

- Never commit API keys to git
- Use environment variables
- Store sensitive tokens in `.env` files (gitignored)
- Use secret managers for team settings

### 5. Limit Tool Access

Only install MCPs you actually use. Each MCP:
- Adds startup time
- Consumes context window
- Increases potential attack surface

### 6. Keep MCPs Updated

Periodically update to get bug fixes and new features:

```bash
# Remove and re-add with @latest
claude mcp remove playwright
claude mcp add playwright -s user -- npx -y @playwright/mcp@latest
```

### 7. Test Before Trusting

Before relying on an MCP for critical work:
1. Verify it connects: `/mcp`
2. Test a simple command
3. Check the output makes sense

---

## Summary: Recommended Setup

| Priority | MCP | Purpose | Install Command |
|----------|-----|---------|-----------------|
| ⭐ 1 | **Playwright** | Browser automation | `claude mcp add playwright -s user -- npx -y @playwright/mcp@latest` |
| ⭐ 2 | **Context7** | Current documentation | `claude mcp add context7 -s user -- npx -y @upstash/context7-mcp@latest` |
| ⭐ 3 | **Sequential Thinking** | Complex reasoning | `claude mcp add sequential-thinking -s user -- npx -y @modelcontextprotocol/server-sequential-thinking` |
| 4 | **GitHub** | Repo management | See GitHub section above |
| 5 | **Fetch** | Web content | `claude mcp add fetch -s user -- npx -y @kazuph/mcp-fetch` |
| 6 | **Brave Search** | Web search | Requires API key |

---

## Resources

- **Official MCP Docs:** https://modelcontextprotocol.io
- **Claude Code MCP Guide:** https://code.claude.com/docs/en/mcp
- **MCP Server Registry:** https://github.com/modelcontextprotocol/servers
- **Community MCPs:** https://mcpcat.io

---

*Extend Claude Code's capabilities with the right tools for your workflow!*
