# Use Horizon Auth with an Owner Gmail Token

Horizon authentication is mandatory on the free hosted endpoint and sits in front of the backend MCP server, so backend FastMCP Google OAuth rejects Horizon gateway tokens. We will let Horizon authenticate MCP access and use a server-owned Google refresh token for the **Allowed Gmail Identity** to perform Gmail API operations.
