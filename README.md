# Gmail MCP Server

A remote FastMCP server for sending Gmail messages through a single allowed
Gmail identity. The server is designed for Prefect Horizon and is protected by
Google OAuth at MCP connection time.

## Features

- Google OAuth MCP access with FastMCP `GoogleProvider`
- Allowed Gmail identity enforcement on every Gmail operation
- Gmail send, draft creation, draft listing, and draft sending tools
- Professional email composition prompts, resources, and helper tools
- Remote-only Horizon entry point at `main.py:mcp`

## Deployment

Deploy this repository to Prefect Horizon from the default branch.

Configure Horizon with:

- Entrypoint: `main.py:mcp`
- Horizon authentication: disabled for this server, because FastMCP Google OAuth
  protects the MCP endpoint directly

Set these deployment environment variables:

- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth web client ID
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth web client secret
- `GMAIL_MCP_BASE_URL`: deployed server base URL, for example
  `https://your-server-name.fastmcp.app`
- `ALLOWED_GMAIL_EMAIL`: the only Gmail address allowed to connect and send
  mail
- `FASTMCP_JWT_SIGNING_KEY`: optional stable signing secret so clients do not
  need to re-authenticate after every server restart

The Google OAuth client must allow the FastMCP callback for the deployed base
URL. By default FastMCP uses `/auth/callback`, so add:

```text
https://your-server-name.fastmcp.app/auth/callback
```

The Google OAuth consent screen must include these scopes:

```text
openid
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.modify
```

Only the Google account matching `ALLOWED_GMAIL_EMAIL` can use the Gmail tools.
Other Google accounts may complete Google login, but Gmail operations are
rejected server-side.

## Local Verification

Install dependencies:

```bash
uv sync
```

Inspect the Horizon entry point with dummy local configuration:

```bash
GOOGLE_OAUTH_CLIENT_ID=test.apps.googleusercontent.com \
GOOGLE_OAUTH_CLIENT_SECRET=test \
GMAIL_MCP_BASE_URL=http://localhost:8000 \
ALLOWED_GMAIL_EMAIL=owner@example.com \
FASTMCP_JWT_SIGNING_KEY=test-signing-key \
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
