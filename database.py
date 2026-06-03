import sqlite3

DB_PATH = "data/game.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS games(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        day INTEGER NOT NULL DEFAULT 1,
        phase TEXT NOT NULL DEFAULT 'day'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER NOT NULL,
        discord_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        alive INTEGER NOT NULL DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS channels(
        game_id INTEGER NOT NULL,
        category_id INTEGER,
        gm_control_id INTEGER,
        gm_status_id INTEGER,
        co_status_id INTEGER,
        co_control_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS co_entries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER NOT NULL,
        discord_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        target_name TEXT,
        result TEXT,
        day INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()
