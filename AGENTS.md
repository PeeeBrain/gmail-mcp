# Gmail MCP Server - Agent Context

## Commands

- `uv sync` — install dependencies
- `uv run fastmcp inspect main.py:mcp` — inspect the Horizon entry point
- `uv run ruff check .` — format and lint (line length 88)
- `uv run pytest` — run the test suite

## Critical Constraints

- **Python 3.12+ required** (`.python-version` pins 3.12)
- **Remote-only MCP server** — local stdio mode and CLI token management have been decommissioned
- **Horizon entry point is `main.py:mcp`** — Horizon deploys the default branch and imports this object
- **FastMCP Google OAuth protects the MCP endpoint** — do not enable a second Horizon auth layer for this server
- **Allowed Gmail identity is enforced per request** — every Gmail operation must reject callers whose Google email does not match `ALLOWED_GMAIL_EMAIL`
- **MCP protocol uses stdout** — never print to stdout in tool handlers; use `ctx.info()`/`ctx.error()` instead

## Architecture

- `main.py` — Horizon import shim exposing `mcp`
- `remote.py` — remote Google OAuth server assembly
- `src/remote_auth.py` — per-request Google access token to Gmail session adapter
- `src/server.py` — FastMCP server with tools, prompts, resources
- `src/gmail_gateway.py` — Gmail API wrapper
- `src/models.py` — Pydantic models
- `src/resources/` — static templates and guidelines

## Notable Conventions

- Required Google OAuth scopes: `openid`, `userinfo.email`, `gmail.send`, `gmail.modify`
- Deployment config comes from environment variables, not local credential files
- `ALLOWED_GMAIL_EMAIL` is the only Gmail identity allowed to operate tools
