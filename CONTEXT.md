# Gmail MCP Server

A local MCP server that lets an MCP client compose and send mail through a selected Gmail identity without exposing Google credentials to the client.

## Language

**Local Gmail Agent**:
An MCP server process running on the user's machine over stdio with access to locally stored Gmail credentials.
_Avoid_: Remote Gmail server, hosted Gmail API

**Gmail User**:
A Google account whose OAuth credentials are stored locally and can be selected for Gmail operations.
_Avoid_: Account, profile

**Current Gmail User**:
The single Gmail User selected for a running local server process.
_Avoid_: Active account, default account

**User Selection**:
The CLI-only act of choosing which Gmail User becomes the Current Gmail User before the local server starts.
_Avoid_: Runtime switch, account switching

**Google OAuth Client Credentials**:
The downloaded Google Cloud desktop OAuth client configuration used to authenticate Gmail Users.
_Avoid_: Credentials, secrets

**Gmail Token Store**:
The local encrypted storage containing OAuth tokens for Gmail Users.
_Avoid_: Auth cache, credential store

**Gmail Session**:
Ready-to-use Gmail capability for the Current Gmail User in a running Local Gmail Agent.
_Avoid_: Credentials, client

**Gmail Session Factory**:
The module that creates a Gmail Session for the Current Gmail User from the Gmail Token Store.
_Avoid_: Auth manager, client factory

## Relationships

- A **Local Gmail Agent** has exactly one **Current Gmail User** at a time.
- A **Gmail User** is authenticated using **Google OAuth Client Credentials**.
- A **Gmail Token Store** contains credentials for zero or more **Gmail Users**.
- A **Gmail Token Store** refreshes and persists tokens before a **Gmail Session** is created.
- A **Gmail Token Store** does not expose Gmail User email addresses in token filenames.
- A **Gmail Token Store** migrates legacy raw-email token filenames to private token filenames.
- A **Gmail Token Store** stores the Current Gmail User pointer using a private token identifier, not a raw email address.
- A **Gmail Token Store** migrates legacy Current Gmail User pointers from raw email addresses to private token identifiers.
- A **Current Gmail User** must exist before the **Local Gmail Agent** can perform Gmail operations.
- **User Selection** happens outside the MCP tool surface.
- A **Local Gmail Agent** without a **Current Gmail User** fails during startup rather than exposing unusable Gmail tools.
- A **Gmail Session** belongs to exactly one **Current Gmail User**.
- A **Gmail Session Factory** creates a **Gmail Session** from the **Gmail Token Store** for the **Current Gmail User**.

## Example dialogue

> **Dev:** "Should FastMCP OAuth authenticate each request before sending mail?"
> **Domain expert:** "Not for this rewrite. The **Local Gmail Agent** runs over stdio and uses the **Current Gmail User** from the local **Gmail Token Store**."
>
> **Dev:** "Can the MCP client switch the **Current Gmail User** while the server is running?"
> **Domain expert:** "No. **User Selection** is a CLI operation before startup; MCP tools can report the selected user but not change it."
>
> **Dev:** "Should the server start if no **Current Gmail User** exists?"
> **Domain expert:** "No. The **Local Gmail Agent** should fail during startup and tell the user to authenticate first."
>
> **Dev:** "Does the **Gmail Token Store** hold only one **Gmail User**?"
> **Domain expert:** "No. It may hold multiple Gmail Users, but one is chosen as the **Current Gmail User** before the local server starts."
>
> **Dev:** "Should tool handlers construct Gmail clients from raw credentials?"
> **Domain expert:** "No. They should use a **Gmail Session** for the **Current Gmail User**."
>
> **Dev:** "Does a **Gmail Session** refresh OAuth tokens?"
> **Domain expert:** "No. The **Gmail Token Store** returns usable credentials before the **Gmail Session** is created."
>
> **Dev:** "Should the token storage module and Gmail operation module be the same thing?"
> **Domain expert:** "No. Rewrite the storage implementation if needed, but keep **Gmail Token Store**, **Gmail Session Factory**, and **Gmail Session** as separate concepts."

## Flagged ambiguities

- "auth" can mean MCP client authentication or Google OAuth authentication. Resolved for the initial rewrite: keep MCP local over stdio and focus auth work on the **Gmail User** flow.
