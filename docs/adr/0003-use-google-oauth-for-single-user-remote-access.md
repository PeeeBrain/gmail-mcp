# Use Google OAuth for Single-User Remote Access

The remote deployment target is a **Single-User Remote Gmail Agent**, not a multi-user Gmail service. We will use Google OAuth as the MCP access gate and allow only the configured **Allowed Gmail Identity** to connect, so the public Horizon endpoint cannot be used to operate the owner's Gmail unless the caller authenticates as that Gmail identity.
