# Expense Tracker MCP Server

A remote MCP (Model Context Protocol) server for tracking personal expenses. It exposes tools an AI assistant (or any MCP client) can call to create users, log expenses, search and summarize spending, and pull category breakdowns for visualization — backed by a serverless **Neon PostgreSQL** database.

## Features

- Create users and attribute expenses to them
- Add, update, and delete expenses
- Fetch expenses, optionally filtered by date range
- Keyword search across category and description
- Category-wise spending breakdown
- Monthly spend summary (count + total)
- Category totals formatted for pie-chart visualization
- Predefined expense categories exposed as an MCP resource

## Tech Stack

- **Python 3.11+**
- **[FastMCP](https://github.com/jlowin/fastmcp)** — MCP server framework
- **[asyncpg](https://github.com/MagicStack/asyncpg)** — async PostgreSQL driver
- **[Neon](https://neon.tech)** — serverless Postgres hosting
- **[uv](https://docs.astral.sh/uv/)** — Python package and environment manager

## Project Structure

```
.
├── main.py                # MCP server instance and tool/resource definitions
├── connection.py          # Connection pool setup, acquire/release helpers
├── db_init.py              # Creates Users/Expenses tables on first run
├── write_access_check.py   # Verifies the DB connection has write access
├── categories.json          # Predefined categories, served as an MCP resource
├── pyproject.toml           # Project dependencies (managed by uv)
├── .env                     # Local environment variables (not committed)
└── README.md
```

## Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- A [Neon](https://neon.tech) project with a connection string

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/bhavyacloud29/firstremotemcp.git
   cd <your-repo-folder>
   ```

2. **Configure environment variables**

   Create a `.env` file in the project root:
   ```bash
   NEON_CONNECTION_STRING=postgresql://<user>:<password>@<host>/<dbname>?sslmode=require
   ```

3. **Install dependencies with uv**
   ```bash
   uv sync
   ```

## Running the Server

```bash
uv run python main.py
```

The server starts on `0.0.0.0:8000` using FastMCP's HTTP transport, making it reachable as a **remote** MCP server rather than a local stdio process.

On first run, call the `initialize_expense_tracker` tool once (via any connected MCP client) to create the `Users` and `Expenses` tables and verify the database connection has write access.

### Exposing it remotely

For a client to connect from outside your machine, the server needs a public, HTTPS-reachable URL. Common options:

- Deploy to a platform like Render, Fly.io, or Railway and point clients at the public URL it gives you.
- Run it behind a reverse proxy (Nginx, Caddy) with TLS termination.
- For quick testing, tunnel it with a tool like `ngrok http 8000`.

Whichever route you pick, register that base URL as the server address in your MCP client.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NEON_CONNECTION_STRING` | Yes | Full Postgres connection string from your Neon project dashboard |

## Available Tools

| Tool | Parameters | Description |
|---|---|---|
| `initialize_expense_tracker` | — | Creates tables if they don't exist and verifies write access. Run once. |
| `create_user` | `user_id, user_name` | Registers a new user. |
| `add_expense` | `user_id, amount, category, description, expense_date` | Logs a new expense. `expense_date` must be `YYYY-MM-DD`. |
| `update_expense` | `user_id, expense_id, amount, category, description, expense_date` | Updates an existing expense by ID. |
| `delete_expense` | `user_id, expense_id` | Deletes an expense by ID. |
| `get_expenses` | `user_id, start_date?, end_date?` | Lists expenses, optionally filtered to a date range (inclusive). |
| `search_expenses` | `user_id, keyword` | Searches category and description for a keyword. |
| `expenses_by_category` | `user_id` | Returns expense count and total spend per category. |
| `monthly_summary` | `user_id, month, year` | Returns expense count and total spend for a given month. |
| `visualize_expenses` | `user_id` | Returns category totals shaped for a pie chart (`chart_type`, `data`). |

## Resources

- `expense://categories` — returns the predefined list of expense categories from `categories.json`.

## Notes & Gotchas

- `ExpenseDate` is stored as `TEXT` in `YYYY-MM-DD` format. Always pass dates in this exact format — date-range and monthly queries rely on it for correct lexicographic/prefix matching.
- `create_user` will fail with a primary key violation if you call it twice with the same `user_id`.
- `add_expense` will fail with a foreign key violation if `user_id` hasn't been registered via `create_user` first.
- Postgres folds unquoted column aliases to lowercase. If you add new queries with aliases and read specific keys off the result (e.g. `row["SomeAlias"]`), access them in lowercase (`row["somealias"]`) or quote the alias in SQL to preserve case.
- Connections are acquired from a shared pool (`connection.py`) and must be returned via `release_connection(conn)` rather than `conn.close()`, or the pool will leak connections over time.


