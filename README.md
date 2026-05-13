# Gmail MCP Server

A remote FastMCP server for sending Gmail messages through a single owner Gmail
identity. The server is designed for Prefect Horizon and relies on Horizon's
gateway authentication for MCP access.

## Features

- Horizon-managed MCP authentication
- Server-owned Gmail refresh token for the owner Gmail identity
- Gmail send, draft creation, draft listing, and draft sending tools
- Professional email composition prompts, resources, and helper tools
- Remote-only Horizon entry point at `main.py:mcp`

## Deployment

Deploy this repository to Prefect Horizon from the default branch.

Configure Horizon with:

- Entrypoint: `main.py:mcp`
- Horizon authentication: enabled

Set these deployment environment variables:

- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth client ID for the owner Gmail token
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth client secret for the owner Gmail
  token
- `GOOGLE_OAUTH_REFRESH_TOKEN`: refresh token for the owner Gmail identity
- `ALLOWED_GMAIL_EMAIL`: the Gmail address the refresh token must belong to

The Google OAuth refresh token must include these scopes:

```text
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.modify
```

Horizon controls who may connect to the MCP server. The backend uses the
configured owner Gmail refresh token for Gmail API calls.

## Local Verification

Install dependencies:

```bash
uv sync
```

Inspect the Horizon entry point with dummy local configuration:

```bash
GOOGLE_OAUTH_CLIENT_ID=test.apps.googleusercontent.com \
GOOGLE_OAUTH_CLIENT_SECRET=test \
GOOGLE_OAUTH_REFRESH_TOKEN=test-refresh-token \
ALLOWED_GMAIL_EMAIL=owner@example.com \
uv run fastmcp inspect main.py:mcp
```

For a real local OAuth test, copy the example environment file and fill in your
Google OAuth web client values:

```bash
cp .env.example .env
```

Then load it before running the local HTTP server:

```bash
set -a
source .env
set +a
uv run fastmcp run main.py:mcp --transport http --host 127.0.0.1 --port 8000
```

Run quality checks:

```bash
uv run ruff check .
uv run pytest
```

## Available MCP Tools

### Core Gmail Tools

- `send_email`: send an email immediately
- `create_draft`: create an email draft
- `send_draft`: send an existing Gmail draft
- `list_drafts`: list Gmail drafts
- `get_user_info`: return the authenticated Gmail profile

### Email Assistance Tools

- `get_subject_line_help`
- `validate_subject_line_tool`
- `get_email_templates`

## MCP Prompts

- `professional_email_composer`
- `follow_up_email_generator`
- `meeting_request_composer`
- `draft_strategy_advisor`
- `email_review_checklist`

## MCP Resources

Template resources are exposed for professional HTML emails, signatures, and
email guidelines.
