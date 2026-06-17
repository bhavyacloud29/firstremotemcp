import random
from fastmcp import FastMCP
import json
from pathlib import Path
from connection import get_connection
import pandas as pd
import asyncio
import os 
from dotenv import load_dotenv
from db_init import initialize_database
from write_access_check import verify_write_access


categories_path=os.path.join(os.path.dirname(__file__),"categories.json")
#create a fastmcp server instance
mcp = FastMCP("ExpenseTracker")

@mcp.tool
async def initialize_expense_tracker():

    await initialize_database()

    await verify_write_access()

    return {
        "success": True,
        "message": "Database initialized successfully"
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
                ?, ?
            )
            """,
            (
                user_id,
                user_name
            )
        )

        await conn.commit()

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
                ?, ?, ?, ?, ?
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

        await conn.commit()

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

        cursor = await conn.execute(
            """
            UPDATE Expenses
            SET
                Amount=?,
                Category=?,
                Description=?,
                ExpenseDate=?
            WHERE
                ExpenseId=?
                AND UserId=?
            """,
            (
                amount,
                category,
                description,
                expense_date,
                expense_id,
                user_id
            )
        )

        await conn.commit()

        return {
            "success": cursor.rowcount > 0,
            "updated_rows": cursor.rowcount
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

        cursor = await conn.execute(
            """
            DELETE FROM Expenses
            WHERE ExpenseId=?
            AND UserId=?
            """,
            (
                expense_id,
                user_id
            )
        )

        await conn.commit()

        return {
            "success": cursor.rowcount > 0,
            "deleted_rows": cursor.rowcount
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
            WHERE UserId=?
            """

            params = [user_id]

            if start_date and end_date:

                query += """
                AND ExpenseDate
                BETWEEN ? AND ?
                """

                params.extend(
                    [
                        start_date,
                        end_date
                    ]
                )

            cursor = await conn.execute(
                query,
                params
            )

            rows = await cursor.fetchall()

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

        cursor = await conn.execute(
            """
            SELECT *
            FROM Expenses
            WHERE UserId=?
            AND
            (
                Category LIKE ?
                OR Description LIKE ?
            )
            """,
            (
                user_id,
                search,
                search
            )
        )

        rows = await cursor.fetchall()

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

        cursor = await conn.execute(
            """
            SELECT
                Category,
                COUNT(*) AS ExpenseCount,
                SUM(Amount) AS TotalSpent
            FROM Expenses
            WHERE UserId=?
            GROUP BY Category
            ORDER BY TotalSpent DESC
            """,
            (user_id,)
        )

        rows = await cursor.fetchall()

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

        cursor = await conn.execute(
            """
            SELECT
                COUNT(*) AS ExpenseCount,
                SUM(Amount) AS TotalSpent
            FROM Expenses
            WHERE UserId=?
            AND strftime('%m', ExpenseDate)=?
            AND strftime('%Y', ExpenseDate)=?
            """,
            (
                user_id,
                f"{month:02d}",
                str(year)
            )
        )

        row = await cursor.fetchone()

        return {
            "month": month,
            "year": year,
            "expense_count": row[0] or 0,
            "total_spent": float(row[1] or 0)
        }

    finally:

        await conn.close()


@mcp.tool
async def visualize_expenses(
    user_id: str
):

    conn = await get_connection()

    try:

        cursor = await conn.execute(
            """
            SELECT
                Category,
                SUM(Amount) AS TotalSpent
            FROM Expenses
            WHERE UserId=?
            GROUP BY Category
            ORDER BY TotalSpent DESC
            """,
            (user_id,)
        )

        rows = await cursor.fetchall()

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


if __name__ == "__main__":
    mcp.run(transport="http",host="0.0.0.0",port=8000)
