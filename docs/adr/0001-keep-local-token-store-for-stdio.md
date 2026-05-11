# Keep Local Token Store for Stdio Rewrite

The initial FastMCP rewrite remains a local stdio **Local Gmail Agent**, so it will keep encrypted file-based storage under `~/.gmail-mcp/` for **Gmail User** tokens. This is temporary local infrastructure: the **Gmail Token Store** should have a replaceable interface because the intended future remote HTTP server can use OAuth capabilities from FastMCP instead of local token files.
