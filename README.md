# Stamp Collection Toolset

AI-powered CLI application to manage a space-themed stamp collection.

## Features

- **Colnect Scraping**: Build a searchable database of space-themed stamps
- **RAG Identification**: Identify physical stamps via camera using AI
- **LASTDODO Migration**: Migrate collections from LASTDODO to Colnect

## Installation

```powershell
uv sync
uv run stamp-tools --help
```

## Quick Start

```powershell
# Initialize database and verify connections
uv run stamp-tools init

# View configuration
uv run stamp-tools config show
```

## Documentation

See [CLAUDE.md](CLAUDE.md) for full documentation.
