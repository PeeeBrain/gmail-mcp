# Decommission Local Stdio Mode

Horizon deploys the repository default branch and expects an importable FastMCP server object, so maintaining a separate local stdio mode in `main.py` creates deployment friction. We will make this repository remote-only, expose the Horizon server as `main.py:mcp`, and remove the local CLI token-store workflow.
