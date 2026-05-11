# Gmail MCP Server - Agent Context

## Commands

- `uv sync` — install dependencies
- `uv run python main.py` — start MCP server (requires authenticated user)
- `uv run python main.py --login` — authenticate via OAuth2
- `uv run python main.py --credentials /path/to/credentials.json` — set OAuth2 credentials
- `uv run ruff check .` — format and lint (line length 88)

## Critical Constraints

- **Python 3.12+ required** (`.python-version` pins 3.12)
- **No automated tests exist** — `tests/` is empty; pytest deps are unused
- **MCP protocol uses stdout** — never print to stdout in the server startup path or tool handlers; use `click.echo(..., err=True)` or `ctx.info()` instead
- **Server requires authenticated user** — exits with code 1 if no current user in `~/.gmail-mcp/`
- **OAuth2 credentials required** — obtain Desktop app credentials from Google Cloud Console with Gmail API enabled, add yourself as a test user

## Architecture

- `main.py` — CLI entry point; also registered as `gmail-mcp` script in `pyproject.toml`
- `src/server.py` — FastMCP server with tools, prompts, resources
- `src/auth_manager.py` — OAuth2 flow, multi-user switching, Fernet-encrypted token storage in `~/.gmail-mcp/`
- `src/gmail_client.py` — Gmail API wrapper
- `src/models.py` — Pydantic models
- `src/resources/` — static templates and guidelines (not API clients)

## Notable Conventions

- `src` imports are relative (`from src.server import ...`) because `main.py` runs from repo root; no `[build-system]` in pyproject.toml
- Scopes: `gmail.send` and `gmail.modify`
- Authentication falls back to console flow (WSL-safe) if browser open fails
