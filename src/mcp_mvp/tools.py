from mcp.server.fastmcp import FastMCP
import yfinance as yf
from duckduckgo_search import DDGS
import os
import psycopg2
import psycopg2.extras


def register_tools(mcp: FastMCP):

    @mcp.tool()
    def hello(name: str) -> str:
        """Say hello to someone."""
        return f"Hello, {name}!"

    @mcp.tool()
    def byebye(name: str) -> str:
        """Say byebye to someone."""
        return f"Byebye, {name}!"

    @mcp.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    @mcp.tool()
    def get_price(ticker: str) -> str:
        """Get the current price of any asset (stock, crypto, ETF, etc.) using its Yahoo Finance ticker symbol (e.g. AAPL, BTC-USD, MSFT)."""
        data = yf.Ticker(ticker)
        info = data.fast_info
        price = info.last_price
        currency = info.currency
        if price is None:
            return f"Could not find price for ticker '{ticker}'. Make sure the symbol is valid on Yahoo Finance."
        return f"{ticker.upper()}: {price:.2f} {currency}"

    def _get_pg_connection():
        return psycopg2.connect(
            host=os.environ.get("PG_HOST", "localhost"),
            port=int(os.environ.get("PG_PORT", 5432)),
            dbname=os.environ["PG_DBNAME"],
            user=os.environ["PG_USER"],
            password=os.environ["PG_PASSWORD"],
        )

    @mcp.tool()
    def db_schema() -> str:
        """Return the list of tables and their columns from the PostgreSQL database. Call this first to understand the database structure before writing queries."""
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name, column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position;
                """)
                rows = cur.fetchall()
        finally:
            conn.close()
        if not rows:
            return "No tables found in the public schema."
        tables: dict = {}
        for table, column, dtype in rows:
            tables.setdefault(table, []).append(f"{column} ({dtype})")
        output = []
        for table, cols in tables.items():
            output.append(f"Table: {table}\n  Columns: {', '.join(cols)}")
        return "\n".join(output)

    @mcp.tool()
    def db_query(sql: str) -> str:
        """Execute a read-only SQL SELECT query on the PostgreSQL database and return the results. Only SELECT statements are allowed."""
        sql_stripped = sql.strip().upper()
        if not sql_stripped.startswith("SELECT"):
            return "Error: only SELECT queries are allowed."
        conn = _get_pg_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql)
                rows = cur.fetchmany(100)
        finally:
            conn.close()
        if not rows:
            return "Query returned no results."
        headers = list(rows[0].keys())
        lines = [" | ".join(headers)]
        lines.append("-" * len(lines[0]))
        for row in rows:
            lines.append(" | ".join(str(v) for v in row.values()))
        return "\n".join(lines)