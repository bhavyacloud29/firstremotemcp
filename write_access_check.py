from connection import get_connection


async def verify_write_access():

    conn = await get_connection()

    try:

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS WriteTest(
            Id INTEGER PRIMARY KEY
        )
        """)

        await conn.execute("""
        INSERT INTO WriteTest DEFAULT VALUES
        """)

        await conn.commit()

        print("Database write access confirmed")

    finally:

        await conn.close()