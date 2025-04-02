import sqlite3

def get_cursor_and_connection():
    conn = sqlite3.connect('family_tree.db')
    cursor = conn.cursor()
    return cursor, conn
    