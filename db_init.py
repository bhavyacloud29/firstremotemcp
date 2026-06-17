from connection import get_connection


async def initialize_database():

    conn = await get_connection()

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS Users(
        UserId TEXT PRIMARY KEY,
        UserName TEXT NOT NULL
    )
    """)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS Expenses(
        ExpenseId INTEGER PRIMARY KEY AUTOINCREMENT,
        UserId TEXT NOT NULL,
        Amount REAL NOT NULL,
        Category TEXT NOT NULL,
        Description TEXT,
        ExpenseDate TEXT NOT NULL,
        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(UserId)
        REFERENCES Users(UserId)
    )
    """)

    await conn.commit()

    await conn.close()

    print("Database initialized")