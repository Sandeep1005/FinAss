import sqlite3
from pathlib import Path


class DatabaseHandler:
    def __init__(self, db_path: str = "database.db"):
        self.db_path = Path(db_path)

    def get_connection(self):
        """Create and return a SQLite connection."""
        return sqlite3.connect(self.db_path)

    def initialize_database(self):
        """Initialize the database by creating all required tables."""
        self.create_entries()
        self.create_reports()

    def create_entries(self):
        """
        Create the 'entries' table if it does not already exist.

        Schema:
            entry_id   : INTEGER PRIMARY KEY AUTOINCREMENT
            message_id : INTEGER
            date       : TEXT (ISO datetime string)
            has_media  : BOOLEAN
            text       : TEXT
            media_url  : TEXT
            is_deleted : BOOLEAN
        """
        query = """
        CREATE TABLE IF NOT EXISTS entries (
            entry_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            date       TEXT,
            has_media  BOOLEAN,
            text       TEXT,
            media_url  TEXT,
            is_deleted BOOLEAN DEFAULT 0
        );
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()

    def create_reports(self):
        """
        Placeholder for the reports table.
        Implement the schema as needed.
        """
        query = """
        CREATE TABLE IF NOT EXISTS reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT
        );
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()

    def insert_entry(
        self,
        message_id: int,
        date: str,
        has_media: bool,
        text: str,
        media_url: str | None = None,
        is_deleted: bool = False,
    ) -> int | None:
        """
        Insert a single entry into the 'entries' table.

        Args:
            message_id (int): Telegram message ID.
            date (str): Datetime string in ISO 8601 format.
            has_media (bool): Whether the message contains media.
            text (str): Message text.
            media_url (str, optional): Path or URL to the media file.
            is_deleted (bool, optional): Whether the entry is marked as deleted.

        Returns:
            int: The auto-generated entry_id of the inserted row.
        """
        query = """
        INSERT INTO entries (
            message_id,
            date,
            has_media,
            text,
            media_url,
            is_deleted
        )
        VALUES (?, ?, ?, ?, ?, ?);
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    message_id,
                    date,
                    int(has_media),
                    text,
                    media_url,
                    int(is_deleted),
                ),
            )
            conn.commit()
            return cursor.lastrowid
    
    def soft_delete_entry(self, message_id: int) -> int:
        """
        Soft delete all entries associated with the given message_id by
        setting their is_deleted flag to True.

        Args:
            message_id (int): The message ID whose entries should be soft deleted.

        Returns:
            int: The number of rows that were updated.
        """
        query = """
        UPDATE entries
        SET is_deleted = 1
        WHERE message_id = ?;
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (message_id,))
            conn.commit()
            return cursor.rowcount
