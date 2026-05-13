# Gmail MCP Server

A remote MCP server that lets Horizon-authorized callers compose and send mail
through one configured owner Gmail identity.

## Language

**Single-User Remote Gmail Agent**:
An MCP server deployed to remote hosting that performs Gmail operations for one allowed Gmail identity.
_Avoid_: Local Gmail agent, multi-user Gmail server

**Allowed Gmail Identity**:
The Gmail User whose mailbox the Single-User Remote Gmail Agent operates.
_Avoid_: Any Google user, shared Gmail user

**MCP Access Identity**:
The Horizon-authenticated identity of the caller allowed to connect to the remote MCP server.
_Avoid_: Gmail token store user, local current user

**Google OAuth Client Credentials**:
The Google Cloud OAuth client configuration used to refresh the owner Gmail token.
_Avoid_: Desktop credentials, local credentials file

**Owner Gmail Refresh Token**:
A Google OAuth refresh token for the Allowed Gmail Identity stored as a Horizon environment secret.
_Avoid_: MCP access token, Horizon token

**Gmail User**:
The Google account whose Gmail mailbox is operated by the server.
_Avoid_: Account, profile

**Gmail Session**:
Ready-to-use Gmail capability created from the Owner Gmail Refresh Token.
_Avoid_: Credentials, client

**Gmail Session Factory**:
The module that creates a Gmail Session from Google OAuth credentials.
_Avoid_: Token store, auth manager

## Relationships

- A **Single-User Remote Gmail Agent** has exactly one **Allowed Gmail Identity**.
- A **Single-User Remote Gmail Agent** receives MCP access through Horizon authentication.
- A **Single-User Remote Gmail Agent** uses the **Owner Gmail Refresh Token** for Gmail API calls.
- An **Owner Gmail Refresh Token** must belong to the **Allowed Gmail Identity**.
- An **Owner Gmail Refresh Token** requests only Gmail send and Gmail modify Google OAuth scopes.
- A **Gmail Session** belongs to the configured **Allowed Gmail Identity**.
- A **Gmail Session Factory** creates a **Gmail Session** from the **Owner Gmail Refresh Token**.
- The server no longer supports local stdio mode or a local Gmail token store.

## Example Dialogue

> **Dev:** "Can anyone with the Horizon URL send mail?"
> **Domain expert:** "No. Horizon authentication controls who can connect to the MCP server."
>
> **Dev:** "Does the server keep refresh tokens in `~/.gmail-mcp/`?"
> **Domain expert:** "No. Local stdio mode has been decommissioned; Gmail operations use the **Owner Gmail Refresh Token** from deployment secrets."
>
> **Dev:** "Should Horizon authentication also be enabled?"
> **Domain expert:** "Yes. Horizon authentication is the MCP access gate on the hosted deployment."

## Flagged Ambiguities

- "auth" can mean MCP access authentication or Gmail API authorization. Current resolution: Horizon authenticates MCP access, while Google OAuth refreshes Gmail API access for the **Allowed Gmail Identity**.
- "remote Gmail server" was explored as both multi-user and single-user. Current target: a **Single-User Remote Gmail Agent** only.
