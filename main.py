import random
from fastmcp import FastMCP
import json
from pathlib import Path
from connection import get_connection, close_pool
import pandas as pd
import asyncio
import os 
from dotenv import load_dotenv
from db_init import initialize_database
from write_access_check import verify_write_access
import signal


categories_path=os.path.join(os.path.dirname(__file__),"categories.json")
#create a fastmcp server instance
mcp = FastMCP("ExpenseTracker")

@mcp.tool
async def initialize_expense_tracker():

    await initialize_database()

    await verify_write_access()

    return {
        "success": True,
        "message": "Database initialized successfully with Neon Postgres"
    }


@mcp.tool
async def create_user(
    user_id: str,
    user_name: str
):

    conn = await get_connection()

    try:

        await conn.execute(
            """
            INSERT INTO Users
            (
                UserId,
                UserName
            )
            VALUES
            (
                $1, $2
            )
            """,
            (
                user_id,
                user_name
            )
        )

        return {
            "success": True,
            "message": "User created successfully"
        }

    finally:

        await conn.close()

@mcp.tool
async def add_expense(
    user_id: str,
    amount: float,
    category: str,
    description: str,
    expense_date: str
):

    conn = await get_connection()

    try:

        await conn.execute(
            """
            INSERT INTO Expenses
            (
                UserId,
                Amount,
                Category,
                Description,
                ExpenseDate
            )
            VALUES
            (
                $1, $2, $3, $4, $5
            )
            """,
            (
                user_id,
                amount,
                category,
                description,
                expense_date
            )
        )

        return {
            "success": True,
            "message": "Expense added successfully"
        }

    finally:

        await conn.close()

@mcp.tool
async def update_expense(
    user_id: str,
    expense_id: int,
    amount: float,
    category: str,
    description: str,
    expense_date: str
):

    conn = await get_connection()

    try:

        await conn.execute(
            """
            UPDATE Expenses
            SET
                Amount=$2,
                Category=$3,
                Description=$4,
                ExpenseDate=$5
            WHERE
                ExpenseId=$1
                AND UserId=$6
            """,
            (
                expense_id,
                amount,
                category,
                description,
                expense_date,
                user_id
            )
        )

        return {
            "success": True,
            "updated_rows": 1
        }

    finally:

        await conn.close()



@mcp.tool
async def delete_expense(
    user_id: str,
    expense_id: int
):

    conn = await get_connection()

    try:

        await conn.execute(
            """
            DELETE FROM Expenses
            WHERE ExpenseId=$1
            AND UserId=$2
            """,
            (
                expense_id,
                user_id
            )
        )

        return {
            "success": True,
            "deleted_rows": 1
        }

    finally:

        await conn.close()




@mcp.tool
async def get_expenses(
    user_id: str,
    start_date: str = None,
    end_date: str = None
):

        conn = await get_connection()

        try:

            query = """
            SELECT *
            FROM Expenses
            WHERE UserId=$1
            """

            params = [user_id]

            if start_date and end_date:

                query += """
                AND ExpenseDate
                BETWEEN $2 AND $3
                """

                params.extend(
                    [
                        start_date,
                        end_date
                    ]
                )

            rows = await conn.fetch(
                query,
                *params
            )

            return [
                dict(row)
                for row in rows
            ]

        finally:

            await conn.close()


@mcp.tool
async def search_expenses(
    user_id: str,
    keyword: str
):

    conn = await get_connection()

    try:

        search = f"%{keyword}%"

        rows = await conn.fetch(
            """
            SELECT *
            FROM Expenses
            WHERE UserId=$1
            AND
            (
                Category LIKE $2
                OR Description LIKE $3
            )
            """,
            (
                user_id,
                search,
                search
            )
        )

        return [
            dict(row)
            for row in rows
        ]

    finally:

        await conn.close()


@mcp.tool
async def expenses_by_category(
    user_id: str
):

    conn = await get_connection()

    try:

        rows = await conn.fetch(
            """
            SELECT
                Category,
                COUNT(*) AS ExpenseCount,
                SUM(Amount) AS TotalSpent
            FROM Expenses
            WHERE UserId=$1
            GROUP BY Category
            ORDER BY TotalSpent DESC
            """,
            (user_id,)
        )

        return [
            dict(row)
            for row in rows
        ]

    finally:

        await conn.close()



@mcp.tool
async def monthly_summary(
    user_id: str,
    month: int,
    year: int
):

    conn = await get_connection()

    try:

        rows = await conn.fetch(
            """
            SELECT
                COUNT(*) AS ExpenseCount,
                SUM(Amount) AS TotalSpent
            FROM Expenses
            WHERE UserId=$1
            AND TO_CHAR(ExpenseDate, 'MM')=$2
            AND TO_CHAR(ExpenseDate, 'YYYY')=$3
            """,
            (
                user_id,
                f"{month:02d}",
                str(year)
            )
        )

        row = rows[0] if rows else None

        return {
            "month": month,
            "year": year,
            "expense_count": int(row["ExpenseCount"]) if row and row["ExpenseCount"] else 0,
            "total_spent": float(row["TotalSpent"]) if row and row["TotalSpent"] else 0
        }

    finally:

        await conn.close()


@mcp.tool
async def visualize_expenses(
    user_id: str
):

    conn = await get_connection()

    try:

        rows = await conn.fetch(
            """
            SELECT
                Category,
                SUM(Amount) AS TotalSpent
            FROM Expenses
            WHERE UserId=$1
            GROUP BY Category
            ORDER BY TotalSpent DESC
            """,
            (user_id,)
        )

        return {
            "chart_type": "pie",
            "data": [
                dict(row)
                for row in rows
            ]
        }

    finally:

        await conn.close()


@mcp.resource("expense://categories",mime_type="application.json")
def expense_categories():
    with open(categories_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Add shutdown handler for connection pool
async def shutdown():
    await close_pool()


if __name__ == "__main__":
    import signal
    
    # Register shutdown handler for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(shutdown())
        )
    
    mcp.run(transport="http",host="0.0.0.0",port=8000)