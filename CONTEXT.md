# Gmail MCP Server

A remote MCP server that lets an allowed Gmail owner compose and send mail
through Gmail after authenticating with Google OAuth.

## Language

**Single-User Remote Gmail Agent**:
An MCP server deployed to remote hosting that performs Gmail operations for one allowed Gmail identity.
_Avoid_: Local Gmail agent, multi-user Gmail server

**Allowed Gmail Identity**:
The only Gmail User permitted to authenticate to and operate the Single-User Remote Gmail Agent.
_Avoid_: Any Google user, shared Gmail user

**MCP Access Identity**:
The Google-authenticated identity of the caller allowed to connect to the remote MCP server.
_Avoid_: Gmail token store user, local current user

**Google OAuth Client Credentials**:
The Google Cloud web OAuth client configuration used by FastMCP to authenticate MCP clients and request Gmail scopes.
_Avoid_: Desktop credentials, local credentials file

**Gmail User**:
The Google account whose Gmail mailbox is operated by the server.
_Avoid_: Account, profile

**Gmail Session**:
Ready-to-use Gmail capability created from the current request's Google OAuth access token.
_Avoid_: Credentials, client

**Gmail Session Factory**:
The module that creates a Gmail Session from Google OAuth credentials.
_Avoid_: Token store, auth manager

## Relationships

- A **Single-User Remote Gmail Agent** has exactly one **Allowed Gmail Identity**.
- A **Single-User Remote Gmail Agent** derives its **MCP Access Identity** from Google OAuth.
- A **Single-User Remote Gmail Agent** allows Gmail operations only for the **Allowed Gmail Identity**.
- A **Single-User Remote Gmail Agent** verifies the **Allowed Gmail Identity** on every Gmail operation.
- A **Single-User Remote Gmail Agent** requests only email identity, Gmail send, and Gmail modify Google OAuth scopes.
- A **Gmail Session** belongs to the **MCP Access Identity** for the current request.
- A **Gmail Session Factory** creates a **Gmail Session** from the current request's Google OAuth access token.
- The server no longer supports local stdio mode or a local Gmail token store.

## Example Dialogue

> **Dev:** "Can anyone with the Horizon URL send mail?"
> **Domain expert:** "No. The server requires Google OAuth and only the **Allowed Gmail Identity** can use Gmail tools."
>
> **Dev:** "Does the server keep refresh tokens in `~/.gmail-mcp/`?"
> **Domain expert:** "No. Local stdio mode has been decommissioned; Gmail operations use the current request's Google OAuth access token."
>
> **Dev:** "Should Horizon authentication also be enabled?"
> **Domain expert:** "No. FastMCP Google OAuth protects the MCP endpoint directly for this server."

## Flagged Ambiguities

- "auth" can mean MCP access authentication or Gmail API authorization. Current resolution: a single Google OAuth flow protects MCP access and grants Gmail send/modify scopes for the **Allowed Gmail Identity**.
- "remote Gmail server" was explored as both multi-user and single-user. Current target: a **Single-User Remote Gmail Agent** only.
