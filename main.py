"""Gmail MCP Server - Entry point and CLI interface."""

import sys
import click

from src.token_store import GmailTokenStore
from src.gmail_session import GmailSessionFactory
from src.server import create_server


# CLI interface
@click.command()
@click.option("--login", is_flag=True, help="Authenticate a new Gmail user")
@click.option("--logout", is_flag=True, help="Logout current user")
@click.option(
    "--switch-user", type=str, help="Switch to a different authenticated user"
)
@click.option("--list-users", is_flag=True, help="List all authenticated users")
@click.option("--remove-user", type=str, help="Remove a specific user")
@click.option("--credentials", type=str, help="Path to OAuth2 credentials file")
@click.option("--current-user", is_flag=True, help="Show current authenticated user")
def cli(login, logout, switch_user, list_users, remove_user, credentials, current_user):
    """Gmail MCP Server CLI."""

    # Create token store for CLI operations
    token_store = GmailTokenStore()
    auth_manager = token_store

    if credentials:
        try:
            auth_manager.set_credentials_file(credentials)
            click.echo(f"Credentials file set: {credentials}")
        except Exception as e:
            click.echo(f"Error setting credentials: {e}", err=True)
            sys.exit(1)
        return

    if login:
        try:
            if not auth_manager.credentials_file.exists():
                click.echo("Error: OAuth2 credentials not found.")
                click.echo(
                    "First set credentials with: gmail-mcp --credentials /path/to/credentials.json"
                )
                sys.exit(1)

            click.echo("Starting OAuth2 authentication...")
            email = auth_manager.authenticate_user()
            click.echo(f"Successfully authenticated: {email}")
        except Exception as e:
            click.echo(f"Authentication failed: {e}", err=True)
            sys.exit(1)
        return

    if logout:
        if auth_manager.logout_current_user():
            click.echo("Successfully logged out")
        else:
            click.echo("No user currently logged in")
        return

    if switch_user:
        if auth_manager.get_credentials(switch_user):
            try:
                auth_manager.set_current_user(switch_user)
                click.echo(f"Switched to user: {switch_user}")
            except ValueError as e:
                click.echo(str(e), err=True)
                sys.exit(1)
        else:
            click.echo(f"User not found or not authenticated: {switch_user}")
            sys.exit(1)
        return

    if list_users:
        users = auth_manager.list_users()
        current = auth_manager.get_current_user()
        if users:
            click.echo("Authenticated users:")
            for user in users:
                marker = " (current)" if user == current else ""
                click.echo(f"  - {user}{marker}")
        else:
            click.echo("No authenticated users")
        return

    if remove_user:
        if auth_manager.remove_user(remove_user):
            click.echo(f"Removed user: {remove_user}")
        else:
            click.echo(f"User not found: {remove_user}")
        return

    if current_user:
        current = auth_manager.get_current_user()
        if current:
            click.echo(f"Current user: {current}")
        else:
            click.echo("No user currently authenticated")
        return

    # Default: Start MCP server
    current = auth_manager.get_current_user()
    if not current:
        click.echo("Error: No authenticated user found.")
        click.echo("Please authenticate first with: gmail-mcp --login")
        sys.exit(1)

    # Don't print startup message when running as MCP server (stdout is used for MCP protocol)
    session_factory = GmailSessionFactory(token_store)
    mcp = create_server(session_factory)
    mcp.run()


if __name__ == "__main__":
    cli()
